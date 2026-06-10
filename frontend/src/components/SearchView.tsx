"use client";

import { useEffect, useState } from "react";
import { apiClient, type SearchHit, type SearchResponse } from "@/lib/api";
import { DASHBOARDS_INDEX_URL, OPENSEARCH_INDEX } from "@/lib/config";
import { EmptyState } from "./EmptyState";
import { IconSearch } from "./ui/Icons";

const DEMO_QUERIES = [
  "What documents are required for customer due diligence?",
  "When is enhanced due diligence needed?",
  "How long should customer data be retained?",
  "What is the process for high-risk customers?",
];

export function SearchView() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<{ indexed: boolean; chunk_count: number } | null>(null);

  useEffect(() => {
    apiClient.indexStats().then(setStats).catch(() => setStats(null));
  }, [results]);

  const runSearch = async (q?: string) => {
    const searchQuery = (q ?? query).trim();
    if (!searchQuery) return;
    setQuery(searchQuery);
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.search(searchQuery);
      setResults(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel panel-elevated">
      <div className="search-hero">
        <div className="search-input-wrap">
          <div className="search-input-inner">
            <IconSearch />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runSearch()}
              placeholder="Search indexed documents…"
              aria-label="Search query"
            />
          </div>
          <button className="btn" onClick={() => runSearch()} disabled={loading}>
            {loading ? (
              <>
                <span className="spinner" /> Searching
              </>
            ) : (
              "Search"
            )}
          </button>
        </div>

        <div className="suggested-queries">
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", alignSelf: "center" }}>Try:</span>
          {DEMO_QUERIES.map((q) => (
            <button key={q} className="query-chip" onClick={() => runSearch(q)}>
              {q.length > 38 ? `${q.slice(0, 38)}…` : q}
            </button>
          ))}
        </div>
      </div>

      <div className="results-header">
        {stats ? (
          <span className="results-count">
            {stats.indexed
              ? `${stats.chunk_count} chunks indexed in ${OPENSEARCH_INDEX}`
              : "No index yet. Parse a document on the Ingest tab first."}
          </span>
        ) : (
          <span className="results-count">Loading index stats…</span>
        )}
        <div className="results-header-actions">
          {results && <span className="results-count">{results.total} matches</span>}
          <a
            href={DASHBOARDS_INDEX_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-ghost btn-sm search-index-link"
            title={`Open OpenSearch Dashboards Query Workbench (${OPENSEARCH_INDEX})`}
          >
            View index
          </a>
        </div>
      </div>

      <div className="panel-body" style={{ padding: 0 }}>
        {error && <div className="alert alert-error" style={{ margin: "1rem 1.35rem 0" }}>{error}</div>}

        {!results && !loading && !error && (
          <EmptyState
            icon={<IconSearch />}
            title="Search your documents"
            description="After parsing with Docling, ask questions across your indexed policy documents."
          />
        )}

        {loading && (
          <div style={{ padding: "2.5rem", textAlign: "center", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            <span className="spinner" style={{ marginRight: "0.5rem", verticalAlign: "middle" }} />
            Searching…
          </div>
        )}

        {results && results.hits.length === 0 && !loading && (
          <EmptyState
            icon={<IconSearch />}
            title="No results found"
            description="Try a different query or ingest a document on the Ingest & Parse tab."
          />
        )}

        {results?.hits.map((hit) => (
          <ResultCard key={hit.chunk_id} hit={hit} />
        ))}
      </div>
    </div>
  );
}

function ResultCard({ hit }: { hit: SearchHit }) {
  const displayText =
    hit.highlights.length > 0 ? (
      <span dangerouslySetInnerHTML={{ __html: hit.highlights.join(" … ") }} />
    ) : (
      hit.chunk_text.length > 320 ? `${hit.chunk_text.slice(0, 320)}…` : hit.chunk_text
    );

  return (
    <article className="result-card">
      <div className="result-top">
        <div>
          <div className="result-title">{hit.document_title}</div>
          <div className="result-meta">
            {hit.source_file}
            {hit.section_title ? ` · ${hit.section_title}` : ""}
            {hit.page_number != null ? ` · Page ${hit.page_number}` : ""}
          </div>
        </div>
      </div>

      <div className="result-snippet">{displayText}</div>

      {Array.isArray(hit.metadata?.element_types) && (hit.metadata.element_types as string[]).length > 0 ? (
        <div className="meta-chips">
          {(hit.metadata.element_types as string[]).map((t) => (
            <span key={t} className="meta-chip">{t}</span>
          ))}
          {hit.metadata.chunk_number != null && (
            <span className="meta-chip">chunk #{String(hit.metadata.chunk_number)}</span>
          )}
        </div>
      ) : null}
    </article>
  );
}
