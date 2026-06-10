"use client";

import { useEffect, useMemo, useState } from "react";
import { apiClient, parseBbox, type DocumentElement, type ParsedDocument } from "@/lib/api";
import { findChunksForElement } from "@/lib/chunk-map";
import { getPictureDataUri } from "@/lib/docling";
import { PdfPreview } from "./PdfPreview";
import { ElementIcon } from "./ui/Icons";

type ViewTab = "structured" | "markdown" | "json" | "chunks";

const VIEW_TABS: { id: ViewTab; label: string }[] = [
  { id: "structured", label: "Structured" },
  { id: "markdown", label: "Markdown" },
  { id: "json", label: "JSON" },
  { id: "chunks", label: "Chunks" },
];

export function ParseViewer({ document }: { document: ParsedDocument }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [viewTab, setViewTab] = useState<ViewTab>("structured");
  const [filter, setFilter] = useState<string>("all");

  const types = useMemo(() => {
    const set = new Set(document.elements.map((e) => e.type));
    return ["all", ...Array.from(set).sort()];
  }, [document.elements]);

  const filtered = useMemo(() => {
    if (filter === "all") return document.elements;
    return document.elements.filter((e) => e.type === filter);
  }, [document.elements, filter]);

  const typeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const e of document.elements) counts[e.type] = (counts[e.type] ?? 0) + 1;
    return counts;
  }, [document.elements]);

  const selected = document.elements.find((e) => e.id === selectedId);
  const selectedBbox = selected ? parseBbox(selected.metadata) : null;
  const selectedChunks = selected ? findChunksForElement(selected, document.chunks) : [];
  const bboxCount = useMemo(
    () => document.elements.filter((e) => parseBbox(e.metadata)).length,
    [document.elements]
  );
  const fileUrl = apiClient.documentFileUrl(document.document_id);

  useEffect(() => {
    const firstWithBbox = document.elements.find((e) => parseBbox(e.metadata));
    setSelectedId(firstWithBbox?.id ?? document.elements[0]?.id ?? null);
    setViewTab("structured");
    setFilter("all");
  }, [document.document_id]);

  const exportContent = () => {
    if (viewTab === "markdown") return document.markdown || "(no markdown export)";
    if (viewTab === "json") return JSON.stringify(document.json_export, null, 2);
    if (viewTab === "chunks") {
      return document.chunks
        .map(
          (c) =>
            `# Chunk ${c.chunk_number} — ${c.section_title || "General"}\n` +
            `Page ${c.page_number ?? "n/a"} · Types: ${c.element_types.join(", ")}\n\n${c.text}`
        )
        .join("\n\n" + "─".repeat(48) + "\n\n");
    }
    return "";
  };

  return (
    <div className="workbench">
      <div className="workbench-toolbar">
        <div>
          <div className="workbench-title">
            <span>{document.filename}</span>
            <span className="status-pill">Parsed</span>
          </div>
          <div className="workbench-stats" style={{ marginTop: "0.35rem" }}>
            <span className="stat-chip">{document.page_count} pages</span>
            <span className="stat-chip">{document.elements.length} elements</span>
            <span className="stat-chip">{document.chunks.length} chunks</span>
            {Object.entries(typeCounts).slice(0, 4).map(([t, n]) => (
              <span key={t} className="stat-chip">{n} {t}</span>
            ))}
          </div>
        </div>
        <div className="segmented-control" role="tablist">
          {VIEW_TABS.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={viewTab === tab.id}
              className={`segmented-btn ${viewTab === tab.id ? "active" : ""}`}
              onClick={() => setViewTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {viewTab === "structured" ? (
        <>
          <DoclingConceptBar
            elementCount={document.elements.length}
            bboxCount={bboxCount}
            chunkCount={document.chunks.length}
            onOpenChunks={() => setViewTab("chunks")}
          />
          <div className="workbench-layout">
          <aside className="structure-panel">
            <div className="structure-panel-header">
              <h3>Extracted structure</h3>
              <select
                className="structure-filter"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                aria-label="Filter elements"
              >
                {types.map((t) => (
                  <option key={t} value={t}>
                    {t === "all" ? "All types" : t}
                  </option>
                ))}
              </select>
            </div>
            <div className="elements-list">
              {filtered.map((elem) => (
                <ElementCard
                  key={elem.id}
                  element={elem}
                  hasBbox={parseBbox(elem.metadata) != null}
                  pictureUri={
                    elem.type === "image"
                      ? getPictureDataUri(document.json_export, elem.ref)
                      : null
                  }
                  selected={selectedId === elem.id}
                  onSelect={() => setSelectedId(elem.id)}
                />
              ))}
              {filtered.length === 0 && (
                <p style={{ color: "var(--text-muted)", fontSize: "0.82rem", padding: "0.5rem" }}>
                  No elements match this filter.
                </p>
              )}
            </div>
          </aside>

          <div className="preview-panel">
            <div className="preview-panel-header">
              <h3>Document preview</h3>
              <a href={fileUrl} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">
                Open in tab
              </a>
            </div>
            <div className="preview-pane">
              <PdfPreview
                documentId={document.document_id}
                filename={document.filename}
                page={selected?.page ?? 1}
                highlight={selectedBbox}
                highlightLabel={selected?.label}
              />
            </div>
            {selected && (
              <SelectionInsight
                element={selected}
                bbox={selectedBbox}
                chunks={selectedChunks}
                onOpenChunks={() => setViewTab("chunks")}
              />
            )}
            <div className="preview-meta">
              <span>
                {selected
                  ? `${selected.label}${selected.page ? ` · Page ${selected.page}` : ""}`
                  : "Select an element to see its bounding box and search chunk on the page"}
              </span>
              <span>{bboxCount} layout boxes · {document.chunks.length} search chunks</span>
            </div>
            {selected?.type === "image" && (
              <div className="preview-image-extract">
                {(() => {
                  const cropUri = getPictureDataUri(document.json_export, selected.ref);
                  if (!cropUri) {
                    return (
                      <p className="preview-image-extract-empty">
                        No separate image extract in Docling JSON for this region.
                      </p>
                    );
                  }
                  return (
                    <>
                      <p className="preview-image-extract-label">Docling picture extract</p>
                      <img
                        src={cropUri}
                        alt={`Extracted ${selected.label}`}
                        className="preview-image-extract-img"
                      />
                    </>
                  );
                })()}
              </div>
            )}
          </div>
        </div>
        </>
      ) : viewTab === "chunks" ? (
        <div className="chunks-export-panel">
          <div className="chunks-export-intro">
            <h3>Search-ready chunks</h3>
            <p>
              Docling elements are grouped by section and reading order, then split into chunks
              for OpenSearch. Tables are kept as structured segments. This is what hybrid search
              retrieves after indexing.
            </p>
          </div>
          <pre className="export-content">{exportContent()}</pre>
        </div>
      ) : (
        <pre className="export-content">{exportContent()}</pre>
      )}
    </div>
  );
}

function DoclingConceptBar({
  elementCount,
  bboxCount,
  chunkCount,
  onOpenChunks,
}: {
  elementCount: number;
  bboxCount: number;
  chunkCount: number;
  onOpenChunks: () => void;
}) {
  return (
    <div className="docling-concept-bar" aria-label="Docling extraction concepts">
      <div className="docling-concept-item">
        <span className="docling-concept-label">Reading order</span>
        <p>
          {elementCount} elements are listed in document flow. Docling preserves headings,
          paragraphs, and tables in the order they should be read.
        </p>
      </div>
      <div className="docling-concept-item docling-concept-item-highlight">
        <span className="docling-concept-label">Bounding boxes</span>
        <p>
          {bboxCount} elements include layout coordinates. Click one to draw its box on the
          preview. A component can have one or more boxes, even across pages.
        </p>
      </div>
      <div className="docling-concept-item">
        <span className="docling-concept-label">Chunks</span>
        <p>
          {chunkCount} search-ready segments group related elements by section for OpenSearch.{" "}
          <button type="button" className="docling-concept-link" onClick={onOpenChunks}>
            View chunks
          </button>
        </p>
      </div>
    </div>
  );
}

function SelectionInsight({
  element,
  bbox,
  chunks,
  onOpenChunks,
}: {
  element: DocumentElement;
  bbox: ReturnType<typeof parseBbox>;
  chunks: ParsedDocument["chunks"];
  onOpenChunks: () => void;
}) {
  const preview = element.text.trim().slice(0, 120);

  return (
    <div className="selection-insight">
      <div className="selection-insight-col">
        <span className="selection-insight-title">Bounding box</span>
        {bbox ? (
          <>
            <p className="selection-insight-text">
              Docling maps this {element.label.toLowerCase()} to a rectangle on page{" "}
              {element.page ?? "?"} (PDF coordinates: left {bbox.l.toFixed(1)}, top{" "}
              {bbox.t.toFixed(1)}, right {bbox.r.toFixed(1)}, bottom {bbox.b.toFixed(1)}).
            </p>
            <p className="selection-insight-hint">The gold overlay on the preview is this box.</p>
          </>
        ) : (
          <p className="selection-insight-text muted">
            No layout box in Docling metadata for this element.
          </p>
        )}
      </div>
      <div className="selection-insight-col">
        <span className="selection-insight-title">Search chunk</span>
        {chunks.length > 0 ? (
          <>
            <p className="selection-insight-text">
              This element contributes to chunk{" "}
              {chunks.map((c) => `#${c.chunk_number}`).join(", ")}
              {chunks[0]?.section_title ? ` in “${chunks[0].section_title}”` : ""}.
            </p>
            {preview && (
              <p className="selection-insight-snippet">
                {preview}
                {element.text.length > 120 ? "…" : ""}
              </p>
            )}
            <button type="button" className="docling-concept-link" onClick={onOpenChunks}>
              Open Chunks tab
            </button>
          </>
        ) : (
          <p className="selection-insight-text muted">
            Could not match this element to a chunk preview. Open the Chunks tab for the full
            index payload.
          </p>
        )}
      </div>
    </div>
  );
}

function ElementCard({
  element,
  hasBbox,
  pictureUri,
  selected,
  onSelect,
}: {
  element: DocumentElement;
  hasBbox?: boolean;
  pictureUri?: string | null;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <div
      className={`element-card ${selected ? "selected" : ""}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onSelect()}
    >
      <div className="element-card-top">
        <ElementIcon type={element.type} />
        <span className="element-type">{element.label}</span>
        {hasBbox && (
          <span className="element-bbox-badge" title="Has layout bounding box">
            ▢
          </span>
        )}
        {element.page != null && <span className="element-page">p.{element.page}</span>}
      </div>
      {element.type === "table" && element.html ? (
        <div dangerouslySetInnerHTML={{ __html: element.html }} />
      ) : element.type === "image" ? (
        <div className="image-card">
          {pictureUri ? (
            <img src={pictureUri} alt="Extracted picture" className="element-image-thumb" />
          ) : (
            <>
              <div style={{ fontSize: "1.25rem", marginBottom: "0.2rem" }}>◫</div>
              Visual element
            </>
          )}
          {element.text && <div style={{ marginTop: "0.25rem", fontSize: "0.78rem" }}>{element.text}</div>}
        </div>
      ) : (
        <div className="element-text">
          {element.text.length > 180 ? `${element.text.slice(0, 180)}…` : element.text || "—"}
        </div>
      )}
    </div>
  );
}
