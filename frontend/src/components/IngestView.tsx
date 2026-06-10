"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient, type JobStatus, type ParsedDocument } from "@/lib/api";
import { EmptyState } from "./EmptyState";
import { IconDocument, IconLayers, IconUpload } from "./ui/Icons";
import { ParseViewer } from "./ParseViewer";

const STAGE_ORDER = ["upload", "parsing", "structure", "preparing", "indexing", "complete"];
const STAGE_LABELS: Record<string, string> = {
  upload: "Upload complete",
  parsing: "Parsing with Docling",
  structure: "Extracting structure",
  preparing: "Preparing for OpenSearch",
  indexing: "Indexing",
  complete: "Indexing complete",
};

function fileExt(filename: string) {
  return filename.split(".").pop()?.toUpperCase() ?? "FILE";
}

export function IngestView() {
  const [samples, setSamples] = useState<
    { filename: string; size_kb: number; tags?: string[]; label?: string; description?: string }[]
  >([]);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [parsed, setParsed] = useState<ParsedDocument | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    apiClient.listSamples().then(setSamples).catch(() => setSamples([]));
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const pollJob = useCallback((jobId: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const status = await apiClient.getJob(jobId);
        setJob(status);
        if (status.parsed) setParsed(status.parsed);
        if (status.status === "complete" || status.status === "error") {
          if (pollRef.current) clearInterval(pollRef.current);
          setLoading(false);
          if (status.status === "complete" && status.document_id) {
            const doc = await apiClient.getDocument(status.document_id);
            setParsed(doc);
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to poll job");
        setLoading(false);
        if (pollRef.current) clearInterval(pollRef.current);
      }
    }, 800);
  }, []);

  const startIngest = async (fn: () => Promise<JobStatus>) => {
    setError(null);
    setLoading(true);
    setParsed(null);
    try {
      const newJob = await fn();
      setJob(newJob);
      pollJob(newJob.job_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ingest failed");
      setLoading(false);
    }
  };

  const stageIndex = job ? STAGE_ORDER.indexOf(job.stage) : -1;

  return (
    <div>
      <section className="panel panel-elevated" style={{ marginBottom: "1.25rem" }}>
        <div className="panel-header">
          <div>
            <h2>Choose a document</h2>
            <p className="panel-header-desc">
              Pick a sample PDF or upload your own. Try the <strong>OCR</strong> and{" "}
              <strong>complex table</strong> showcases to see Docling&apos;s layout intelligence.
            </p>
          </div>
        </div>
        <div className="panel-body">
          <div className="ingest-grid">
            <div>
              <p className="section-label">Upload your own</p>
              <div
                className="upload-zone"
                onClick={() => !loading && fileRef.current?.click()}
                onKeyDown={(e) => e.key === "Enter" && fileRef.current?.click()}
                role="button"
                tabIndex={0}
                aria-label="Upload document"
              >
                <input
                  ref={fileRef}
                  type="file"
                  accept=".pdf,.docx,.md,.txt,.png,.jpg,.jpeg,.tiff,.tif,.webp"
                  disabled={loading}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) startIngest(() => apiClient.ingestUpload(file));
                  }}
                />
                <div className="upload-zone-icon">
                  <IconUpload />
                </div>
                <p className="upload-zone-title">Drop a file or click to browse</p>
                <p className="upload-zone-hint">PDF, Office, text, or images (PNG/JPEG) for OCR</p>
                <div className="file-type-badges">
                  {["PDF", "PNG", "JPEG", "DOCX", "MD"].map((t) => (
                    <span key={t} className="file-type-badge">{t}</span>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <p className="section-label">Or try a sample</p>
              <div className="sample-grid">
                {samples.map((s) => (
                  <div key={s.filename} className="sample-card">
                    <div className="sample-card-icon">
                      <IconDocument />
                    </div>
                    <div className="sample-card-body">
                      <div className="sample-card-name" title={s.filename}>{s.filename}</div>
                      {s.label && (
                        <span className={`sample-showcase-badge ${s.tags?.[0] ?? ""}`}>{s.label}</span>
                      )}
                      {s.description && (
                        <p className="sample-card-desc">{s.description}</p>
                      )}
                      <div className="sample-card-meta">
                        <span className="file-type-badge">{fileExt(s.filename)}</span>
                        <span>{s.size_kb} KB</span>
                      </div>
                    </div>
                    <button
                      className="btn btn-sm"
                      disabled={loading}
                      onClick={() => startIngest(() => apiClient.ingestSample(s.filename))}
                    >
                      Parse &amp; index
                    </button>
                  </div>
                ))}
                {samples.length === 0 && (
                  <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No samples in data/</p>
                )}
              </div>
            </div>
          </div>

          <div className="ingest-note">
            Once indexed, switch to Enterprise Search to find answers across your parsed documents.
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          {job && (
            <div
              className={`job-status-card ${job.status === "complete" ? "success" : ""} ${job.status === "error" ? "error" : ""}`}
            >
              <div className="job-status-header">
                <span className="job-status-filename">{job.filename}</span>
                <span className="job-status-message">
                  {loading && <span className="spinner" style={{ marginRight: "0.4rem", verticalAlign: "middle" }} />}
                  {job.message}
                </span>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${job.progress}%` }} />
              </div>
              <div className="status-steps">
                {STAGE_ORDER.map((stage, i) => {
                  let cls = "status-step";
                  if (i < stageIndex) cls += " done";
                  else if (i === stageIndex) cls += " active";
                  return (
                    <span key={stage} className={cls}>{STAGE_LABELS[stage]}</span>
                  );
                })}
              </div>
              {job.status === "error" && job.error && (
                <div className="alert alert-error" style={{ marginTop: "0.75rem", marginBottom: 0 }}>{job.error}</div>
              )}
              {job.status === "complete" && (
                <div className="alert alert-success" style={{ marginTop: "0.75rem", marginBottom: 0 }}>
                  Document parsed and indexed. Scroll down to inspect extracted structure.
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      <section>
        <p className="section-label">Step 2 — Inspect Docling extraction</p>
        {parsed ? (
          <ParseViewer document={parsed} />
        ) : (
          <div className="panel">
            <EmptyState
              icon={<IconLayers />}
              title="No document parsed yet"
              description="Parse a NexValue policy document to inspect headings, tables, metadata, and chunks before indexing into OpenSearch."
              action={
                loading ? (
                  <span style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                    <span className="spinner" /> Parsing in progress…
                  </span>
                ) : (
                  <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    Select a sample above or upload a PDF or image to begin
                  </span>
                )
              }
            />
          </div>
        )}
      </section>
    </div>
  );
}
