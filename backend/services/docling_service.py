from __future__ import annotations

import importlib.util
import re
import uuid
from pathlib import Path
from typing import Any

import httpx
from docling.datamodel.base_models import ConversionStatus, OutputFormat
from docling.datamodel.service.options import ConvertDocumentsOptions
from docling.datamodel.service.responses import PresignedUrlConvertResponse
from docling.datamodel.service.targets import PresignedUrlTarget
from docling.service_client import DoclingServiceClient
from docling.service_client.exceptions import ServiceError, UsageLimitExceededError
from docling_core.types.doc import DocItemLabel, DoclingDocument

from backend.config import (
    CHUNK_OVERLAP_WORDS,
    CHUNK_SIZE_WORDS,
    DOCLING_API_KEY,
    DOCLING_SERVICE_URL,
    PARSED_DIR,
)
from backend.models.schemas import DocumentChunk, DocumentElement, ParsedDocument

LABEL_MAP: dict[DocItemLabel, tuple[str, str]] = {
    DocItemLabel.TITLE: ("title", "Title"),
    DocItemLabel.SECTION_HEADER: ("heading", "Heading"),
    DocItemLabel.TEXT: ("paragraph", "Paragraph"),
    DocItemLabel.PARAGRAPH: ("paragraph", "Paragraph"),
    DocItemLabel.TABLE: ("table", "Table"),
    DocItemLabel.PICTURE: ("image", "Image"),
    DocItemLabel.CAPTION: ("caption", "Caption"),
    DocItemLabel.FOOTNOTE: ("metadata", "Footnote"),
    DocItemLabel.PAGE_HEADER: ("metadata", "Page Header"),
    DocItemLabel.PAGE_FOOTER: ("metadata", "Page Footer"),
    DocItemLabel.LIST_ITEM: ("paragraph", "List Item"),
    DocItemLabel.CODE: ("paragraph", "Code"),
    DocItemLabel.FORMULA: ("paragraph", "Formula"),
    DocItemLabel.DOCUMENT_INDEX: ("metadata", "Document Index"),
}


def _assert_saas_only() -> None:
    """Fail fast if local Docling parsing packages are installed."""
    local_packages = (
        ("docling_parse", "docling-parse"),
        ("docling_ibm_models", "docling-ibm-models"),
    )
    for module_name, package_name in local_packages:
        if importlib.util.find_spec(module_name) is not None:
            raise RuntimeError(
                f"Local Docling package '{package_name}' is installed. "
                "This demo uses Docling SaaS only — run: "
                "pip uninstall docling docling-parse docling-ibm-models && "
                "pip install 'docling-slim[service-client]'"
            )

    try:
        import importlib.metadata as metadata

        if metadata.version("docling"):
            raise RuntimeError(
                "The full 'docling' package is installed. "
                "Uninstall it and use docling-slim[service-client] for SaaS-only parsing."
            )
    except metadata.PackageNotFoundError:
        pass


def _load_document_from_presigned_result(
    result: PresignedUrlConvertResponse,
    source_name: str,
) -> DoclingDocument:
    if not result.documents:
        raise RuntimeError("Docling SaaS returned no documents in the conversion result.")

    doc_item = result.documents[0]
    if doc_item.status not in {
        ConversionStatus.SUCCESS,
        ConversionStatus.PARTIAL_SUCCESS,
    }:
        errors = "; ".join(error.error_message for error in doc_item.errors)
        message = errors or doc_item.status.value
        raise RuntimeError(f"Docling SaaS conversion failed for {source_name}: {message}")

    json_artifact = next(
        (artifact for artifact in doc_item.artifacts if artifact.artifact_type == "json"),
        None,
    )
    if json_artifact is None:
        raise RuntimeError(
            "Docling SaaS did not return a JSON artifact. "
            "IBM Docling for watsonx uses presigned_url output; ensure JSON is enabled."
        )

    response = httpx.get(str(json_artifact.uri), timeout=120.0)
    response.raise_for_status()
    return DoclingDocument.model_validate_json(response.text)


def _convert_via_saas(file_path: Path) -> Any:
    _assert_saas_only()

    if not DOCLING_SERVICE_URL:
        raise RuntimeError(
            "DOCLING_SERVICE_URL is not set. Add it to your .env file."
        )
    if not DOCLING_API_KEY:
        raise RuntimeError(
            "DOCLING_API_KEY is not set. Add your Docling SaaS API key to .env."
        )

    try:
        with DoclingServiceClient(url=DOCLING_SERVICE_URL, api_key=DOCLING_API_KEY) as client:
            options = ConvertDocumentsOptions(
                to_formats=[OutputFormat.JSON, OutputFormat.MARKDOWN],
            )
            job = client.submit(
                source=file_path,
                target=PresignedUrlTarget(),
                options=options,
            )
            result = job.result(timeout=300)
            if not isinstance(result, PresignedUrlConvertResponse):
                raise RuntimeError(
                    "Unexpected Docling SaaS response type from presigned_url conversion."
                )
            return _load_document_from_presigned_result(result, file_path.name)
    except UsageLimitExceededError as exc:
        raise RuntimeError(
            f"Docling SaaS usage limit exceeded ({exc}). "
            "Check your IBM Docling SaaS quota or billing."
        ) from exc
    except ServiceError as exc:
        detail = f" Detail: {exc.detail}." if exc.detail else ""
        if exc.status_code == 403:
            raise RuntimeError(
                "Docling SaaS rejected the request (403 Forbidden). "
                "Your API key may be invalid, expired, or not authorized for this instance. "
                f"Verify DOCLING_API_KEY and DOCLING_SERVICE_URL in .env.{detail}"
            ) from exc
        if exc.status_code == 401:
            raise RuntimeError(
                f"Docling SaaS authentication failed (401). Check DOCLING_API_KEY in .env.{detail}"
            ) from exc
        raise RuntimeError(f"Docling SaaS error: {exc}.{detail}") from exc


def _page_for_item(item: Any, doc: Any) -> int | None:
    if hasattr(item, "prov") and item.prov:
        for prov in item.prov:
            if hasattr(prov, "page_no"):
                return int(prov.page_no)
    return None


def _bbox_for_item(item: Any) -> dict[str, float] | None:
    if hasattr(item, "prov") and item.prov:
        prov = item.prov[0]
        if hasattr(prov, "bbox"):
            bbox = prov.bbox
            return {
                "l": float(getattr(bbox, "l", 0)),
                "t": float(getattr(bbox, "t", 0)),
                "r": float(getattr(bbox, "r", 0)),
                "b": float(getattr(bbox, "b", 0)),
            }
    return None


def _table_to_html(doc: Any, item: Any) -> str | None:
    try:
        if hasattr(item, "export_to_html"):
            html = item.export_to_html(doc=doc)
            if html and html.strip():
                return html
    except Exception:
        pass
    try:
        if hasattr(item, "export_to_dataframe"):
            df = item.export_to_dataframe(doc=doc)
            if df is not None and not df.empty:
                headers = "".join(f"<th>{c}</th>" for c in df.columns)
                rows = []
                for row in df.itertuples(index=False):
                    rows.append(
                        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
                    )
                return (
                    "<table class='docling-table'><thead><tr>"
                    + headers
                    + "</tr></thead><tbody>"
                    + "".join(rows)
                    + "</tbody></table>"
                )
    except Exception:
        pass
    text = getattr(item, "text", "") or ""
    if not text.strip():
        return None
    rows = [r.strip() for r in text.split("\n") if r.strip()]
    if len(rows) < 2:
        return f"<pre>{text}</pre>"
    html_rows = []
    for i, row in enumerate(rows):
        cells = [c.strip() for c in re.split(r"\s{2,}|\t|\|", row) if c.strip()]
        if not cells:
            cells = [row]
        tag = "th" if i == 0 else "td"
        html_rows.append(
            "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>"
        )
    return "<table class='docling-table'>" + "".join(html_rows) + "</table>"


def _label_to_type(label: DocItemLabel) -> tuple[str, str]:
    return LABEL_MAP.get(label, ("paragraph", str(label).replace("_", " ").title()))


def _chunk_text(text: str) -> list[str]:
    words = text.split()
    if len(words) <= CHUNK_SIZE_WORDS:
        return [text] if text.strip() else []
    chunks: list[str] = []
    start = 0
    step = max(1, CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS)
    while start < len(words):
        end = min(len(words), start + CHUNK_SIZE_WORDS)
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end == len(words):
            break
        start += step
    return chunks


def _build_chunks(elements: list[DocumentElement], doc_id: str) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    current_section = "General"
    buffer: list[str] = []
    buffer_types: list[str] = []
    buffer_page: int | None = None
    chunk_number = 0

    def flush() -> None:
        nonlocal chunk_number
        if not buffer:
            return
        text = " ".join(buffer).strip()
        for piece in _chunk_text(text):
            chunk_number += 1
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{doc_id}::chunk::{chunk_number}",
                    chunk_number=chunk_number,
                    text=piece,
                    section_title=current_section,
                    page_number=buffer_page,
                    element_types=sorted(set(buffer_types)),
                )
            )
        buffer.clear()
        buffer_types.clear()

    for elem in elements:
        if elem.type in {"title", "heading"} and elem.text.strip():
            flush()
            current_section = elem.text.strip()
            buffer_page = elem.page
            continue
        if elem.type == "table" and elem.html:
            flush()
            chunk_number += 1
            table_text = re.sub(r"<[^>]+>", " ", elem.html)
            table_text = re.sub(r"\s+", " ", table_text).strip()
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{doc_id}::chunk::{chunk_number}",
                    chunk_number=chunk_number,
                    text=table_text or elem.text,
                    section_title=current_section,
                    page_number=elem.page,
                    element_types=["table"],
                )
            )
            continue
        if elem.text.strip():
            buffer.append(elem.text.strip())
            buffer_types.append(elem.type)
            if buffer_page is None:
                buffer_page = elem.page

    flush()
    return chunks


def parse_document(file_path: Path, document_id: str | None = None) -> ParsedDocument:
    doc_id = document_id or uuid.uuid4().hex[:12]
    doc = _convert_via_saas(file_path)

    markdown = ""
    if hasattr(doc, "export_to_markdown"):
        markdown = doc.export_to_markdown() or ""

    json_export: dict[str, Any] = {}
    if hasattr(doc, "export_to_dict"):
        json_export = doc.export_to_dict()
    elif hasattr(doc, "model_dump"):
        json_export = doc.model_dump(mode="json")

    elements: list[DocumentElement] = []
    elem_idx = 0
    seen_title = False

    for thing in doc.iterate_items():
        item = thing[0] if isinstance(thing, tuple) else thing
        level = thing[1] if isinstance(thing, tuple) and len(thing) > 1 else None
        label = getattr(item, "label", DocItemLabel.TEXT)
        elem_type, elem_label = _label_to_type(label)
        if label == DocItemLabel.TITLE or (label == DocItemLabel.SECTION_HEADER and not seen_title):
            elem_type, elem_label = "title", "Title"
            seen_title = True
        text = (getattr(item, "text", None) or "").strip()
        page = _page_for_item(item, doc)
        bbox = _bbox_for_item(item)
        ref = getattr(item, "self_ref", None) or getattr(item, "id", None)

        html = None
        image_url = None
        if elem_type == "table":
            html = _table_to_html(doc, item)
        if elem_type == "image":
            image_url = f"/api/documents/{doc_id}/preview?page={page or 1}"

        if not text and not html and elem_type != "image":
            continue

        elem_idx += 1
        elements.append(
            DocumentElement(
                id=f"elem-{elem_idx}",
                type=elem_type,
                label=elem_label,
                text=text,
                html=html,
                image_url=image_url,
                page=page,
                level=level,
                ref=str(ref) if ref else None,
                metadata={"bbox": bbox} if bbox else {},
            )
        )

    page_count = len(doc.pages) if hasattr(doc, "pages") else 0
    chunks = _build_chunks(elements, doc_id)
    parsed = ParsedDocument(
        document_id=doc_id,
        filename=file_path.name,
        status="complete",
        page_count=page_count,
        elements=elements,
        markdown=markdown,
        json_export=json_export,
        chunks=chunks,
        metadata={
            "element_count": len(elements),
            "chunk_count": len(chunks),
            "source_path": str(file_path),
            "parsing_mode": "docling_saas",
        },
    )

    out_path = PARSED_DIR / f"{doc_id}.json"
    out_path.write_text(parsed.model_dump_json(indent=2), encoding="utf-8")
    return parsed


def load_parsed(document_id: str) -> ParsedDocument | None:
    path = PARSED_DIR / f"{document_id}.json"
    if not path.exists():
        return None
    return ParsedDocument.model_validate_json(path.read_text(encoding="utf-8"))
