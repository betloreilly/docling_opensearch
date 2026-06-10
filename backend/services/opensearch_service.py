from __future__ import annotations

import copy
import datetime as dt
from typing import Any, Literal

from opensearchpy import OpenSearch, RequestsHttpConnection

from backend.config import (
    HYBRID_PIPELINE,
    KEYWORD_WEIGHT,
    OPENSEARCH_INDEX,
    OPENSEARCH_PASS,
    OPENSEARCH_URL,
    OPENSEARCH_USER,
    VECTOR_DIM,
    VECTOR_WEIGHT,
)
from backend.models.schemas import ParsedDocument, SearchHit, SearchQueryDebug, SearchResponse
from backend.services.embedder import embed_text

HYBRID_SEARCH_DOCS_URL = (
    "https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/"
)

_client: OpenSearch | None = None


def get_client() -> OpenSearch:
    global _client
    if _client is None:
        _client = OpenSearch(
            hosts=[OPENSEARCH_URL],
            http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
            use_ssl=OPENSEARCH_URL.startswith("https"),
            verify_certs=False,
            ssl_show_warn=False,
            connection_class=RequestsHttpConnection,
        )
    return _client


def _index_mapping() -> dict[str, Any]:
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "index.knn": True,
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "chunk_id": {"type": "keyword"},
                "document_title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "source_file": {"type": "keyword"},
                "section_title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "section_path": {"type": "keyword"},
                "page_number": {"type": "integer"},
                "chunk_number": {"type": "integer"},
                "element_types": {"type": "keyword"},
                "chunk_text": {"type": "text"},
                "chunk_text_vector": {
                    "type": "knn_vector",
                    "dimension": VECTOR_DIM,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "lucene",
                        "parameters": {"ef_construction": 128, "m": 24},
                    },
                },
                "ingested_at": {"type": "date"},
            }
        },
    }


def ensure_index() -> None:
    client = get_client()
    if not client.indices.exists(index=OPENSEARCH_INDEX):
        client.indices.create(index=OPENSEARCH_INDEX, body=_index_mapping())


def _build_search_pipeline_body() -> dict[str, Any]:
    """Search pipeline per OpenSearch hybrid search docs (normalization-processor)."""
    return {
        "description": "Post processor for hybrid search (NexValue demo)",
        "phase_results_processors": [
            {
                "normalization-processor": {
                    "normalization": {"technique": "min_max"},
                    "combination": {
                        "technique": "arithmetic_mean",
                        "parameters": {
                            "weights": [KEYWORD_WEIGHT, VECTOR_WEIGHT],
                        },
                    },
                }
            }
        ],
    }


def ensure_hybrid_pipeline() -> None:
    client = get_client()
    client.transport.perform_request(
        "PUT",
        f"/_search/pipeline/{HYBRID_PIPELINE}",
        body=_build_search_pipeline_body(),
    )


def index_document(parsed: ParsedDocument) -> int:
    ensure_index()
    ensure_hybrid_pipeline()
    client = get_client()

    document_title = parsed.filename.rsplit(".", 1)[0].replace("_", " ").title()
    docs: list[dict[str, Any]] = []

    for chunk in parsed.chunks:
        vector = embed_text(chunk.text)
        docs.append(
            {
                "doc_id": parsed.document_id,
                "chunk_id": chunk.chunk_id,
                "document_title": document_title,
                "source_file": parsed.filename,
                "section_title": chunk.section_title,
                "section_path": f"{document_title} > {chunk.section_title or 'General'}",
                "page_number": chunk.page_number,
                "chunk_number": chunk.chunk_number,
                "element_types": chunk.element_types,
                "chunk_text": chunk.text,
                "chunk_text_vector": vector,
                "ingested_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            }
        )

    if not docs:
        return 0

    actions = []
    for doc in docs:
        actions.append({"index": {"_index": OPENSEARCH_INDEX, "_id": doc["chunk_id"]}})
        actions.append(doc)

    client.bulk(body=actions, refresh=True)
    return len(docs)


def _extract_highlights(hit: dict[str, Any]) -> list[str]:
    highlight = hit.get("highlight", {})
    snippets: list[str] = []
    for values in highlight.values():
        snippets.extend(values)
    return snippets


def _truncate_vectors(obj: Any) -> Any:
    """Replace embedding arrays with a short preview for UI display."""
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if key in {"vector", "chunk_text_vector"} and isinstance(value, list):
                preview = [round(float(v), 6) for v in value[:4]]
                out[key] = preview + [f"... ({len(value)} dimensions)"]
            else:
                out[key] = _truncate_vectors(value)
        return out
    if isinstance(obj, list):
        return [_truncate_vectors(item) for item in obj]
    return obj


def _lexical_subquery(query: str) -> dict[str, Any]:
    """BM25 keyword subquery — docs example uses match; we use multi_match across chunk fields."""
    return {
        "multi_match": {
            "query": query,
            "type": "best_fields",
            "fields": [
                "chunk_text^3",
                "section_title^2",
                "document_title^2",
            ],
        }
    }


def _vector_subquery(query: str, k: int, vector: list[float]) -> dict[str, Any]:
    """
    kNN on pre-ingested chunk_text_vector.
    Docs show `neural` when ML Commons generates vectors at query time;
    we use `knn` because Docling chunks are embedded at ingest time.
    """
    return {
        "knn": {
            "chunk_text_vector": {
                "vector": vector,
                "k": k,
            }
        }
    }


def _build_keyword_query(query: str, size: int) -> dict[str, Any]:
    return {
        "size": size,
        "_source": {"excludes": ["chunk_text_vector"]},
        "query": {"bool": {"must": [_lexical_subquery(query)]}},
        "highlight": {
            "fields": {"chunk_text": {"fragment_size": 180, "number_of_fragments": 2}},
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"],
        },
    }


def _build_semantic_query(query: str, size: int, vector: list[float]) -> dict[str, Any]:
    k = max(size, 25)
    return {
        "size": size,
        "_source": {"excludes": ["chunk_text_vector"]},
        "query": _vector_subquery(query, k, vector),
    }


def _build_hybrid_query(query: str, size: int, vector: list[float]) -> dict[str, Any]:
    """
    Official hybrid search shape:
    GET /{index}/_search?search_pipeline={pipeline}
    { "query": { "hybrid": { "queries": [ lexical, vector ] } } }
    """
    k = max(size, 25)
    return {
        "size": size,
        "_source": {"excludes": ["chunk_text_vector"]},
        "query": {
            "hybrid": {
                "queries": [
                    {"bool": {"must": [_lexical_subquery(query)]}},
                    _vector_subquery(query, k, vector),
                ]
            }
        },
        "highlight": {
            "fields": {"chunk_text": {"fragment_size": 180, "number_of_fragments": 2}},
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"],
        },
    }


def _build_query_debug(
    query: str,
    mode: Literal["keyword", "semantic", "hybrid"],
    size: int,
    body: dict[str, Any],
    params: dict[str, Any],
) -> SearchQueryDebug:
    pipeline_body = _build_search_pipeline_body()
    endpoint = f"GET /{OPENSEARCH_INDEX}/_search"
    if params.get("search_pipeline"):
        endpoint += f"?search_pipeline={params['search_pipeline']}"

    if mode == "hybrid":
        steps = [
            "Understand the employee's question as text and as a meaning vector",
            "Search policy chunks by exact words and by similar meaning at the same time",
            "Blend both result lists into one ranked set of answers",
        ]
        notes = []
    elif mode == "semantic":
        steps = [
            "Turn the question into a meaning vector",
            "Find the closest matching policy chunks by meaning",
        ]
        notes = []
    else:
        steps = [
            "Look for the question's words in chunk text, section titles, and document names",
            "Rank chunks by how well the words match",
        ]
        notes = []

    return SearchQueryDebug(
        documentation_url=HYBRID_SEARCH_DOCS_URL,
        index=OPENSEARCH_INDEX,
        search_pipeline=params.get("search_pipeline"),
        fusion_weights={"keyword": KEYWORD_WEIGHT, "vector": VECTOR_WEIGHT},
        steps=steps,
        create_search_pipeline=(
            {
                "method": "PUT",
                "path": f"/_search/pipeline/{HYBRID_PIPELINE}",
                "body": pipeline_body,
            }
            if mode == "hybrid"
            else None
        ),
        search_request={
            "method": "GET",
            "endpoint": endpoint,
            "body": _truncate_vectors(copy.deepcopy(body)),
        },
        notes=notes,
    )


def _explanation_for_mode(mode: str) -> str:
    if mode == "keyword":
        return "Finds exact policy terms and acronyms in document text."
    if mode == "semantic":
        return "Finds answers by meaning, even when the wording is different."
    return (
        f"Combines exact word matching ({KEYWORD_WEIGHT:.0%}) with meaning-based search "
        f"({VECTOR_WEIGHT:.0%}) for the best employee experience."
    )


def search(
    query: str,
    mode: Literal["keyword", "semantic", "hybrid"] = "hybrid",
    size: int = 8,
) -> SearchResponse:
    client = get_client()
    if not client.indices.exists(index=OPENSEARCH_INDEX):
        return SearchResponse(
            query=query,
            mode=mode,
            total=0,
            hits=[],
            explanation=_explanation_for_mode(mode),
            query_debug=None,
        )

    vector = embed_text(query) if mode in {"semantic", "hybrid"} else []

    if mode == "keyword":
        body = _build_keyword_query(query, size)
        params: dict[str, Any] = {}
    elif mode == "semantic":
        body = _build_semantic_query(query, size, vector)
        params = {}
    else:
        ensure_hybrid_pipeline()
        body = _build_hybrid_query(query, size, vector)
        params = {"search_pipeline": HYBRID_PIPELINE}

    query_debug = _build_query_debug(query, mode, size, body, params)
    result = client.search(index=OPENSEARCH_INDEX, body=body, params=params)
    hits: list[SearchHit] = []

    for hit in result.get("hits", {}).get("hits", []):
        source = hit.get("_source", {})
        score = float(hit.get("_score") or 0.0)
        match_type = mode
        if mode == "hybrid":
            match_type = "hybrid (keyword + vector)"

        hits.append(
            SearchHit(
                chunk_id=source.get("chunk_id", ""),
                document_title=source.get("document_title", ""),
                source_file=source.get("source_file", ""),
                section_title=source.get("section_title"),
                page_number=source.get("page_number"),
                chunk_text=source.get("chunk_text", ""),
                score=score,
                match_type=match_type,
                metadata={
                    "element_types": source.get("element_types", []),
                    "section_path": source.get("section_path"),
                    "chunk_number": source.get("chunk_number"),
                },
                highlights=_extract_highlights(hit),
            )
        )

    total = result.get("hits", {}).get("total", {})
    total_val = total.get("value", 0) if isinstance(total, dict) else int(total or 0)

    return SearchResponse(
        query=query,
        mode=mode,
        total=total_val,
        hits=hits,
        explanation=_explanation_for_mode(mode),
        query_debug=query_debug,
    )


def get_index_stats() -> dict[str, Any]:
    client = get_client()
    if not client.indices.exists(index=OPENSEARCH_INDEX):
        return {"indexed": False, "chunk_count": 0, "documents": []}
    count = client.count(index=OPENSEARCH_INDEX).get("count", 0)
    agg = client.search(
        index=OPENSEARCH_INDEX,
        body={
            "size": 0,
            "aggs": {
                "documents": {
                    "terms": {"field": "source_file", "size": 50},
                    "aggs": {"chunks": {"value_count": {"field": "chunk_id"}}},
                }
            },
        },
    )
    docs = []
    for bucket in agg.get("aggregations", {}).get("documents", {}).get("buckets", []):
        docs.append(
            {
                "source_file": bucket["key"],
                "chunk_count": bucket["chunks"]["value"],
            }
        )
    return {"indexed": True, "chunk_count": count, "documents": docs}
