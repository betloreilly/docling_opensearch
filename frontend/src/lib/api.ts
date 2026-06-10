// Empty string = same-origin via Next.js /api rewrite (required for PDF preview iframe).
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export type DoclingBbox = {
  l: number;
  t: number;
  r: number;
  b: number;
};

export function parseBbox(metadata: Record<string, unknown>): DoclingBbox | null {
  const raw = metadata.bbox;
  if (!raw || typeof raw !== "object") return null;
  const bbox = raw as Record<string, unknown>;
  if (
    typeof bbox.l === "number" &&
    typeof bbox.t === "number" &&
    typeof bbox.r === "number" &&
    typeof bbox.b === "number"
  ) {
    return { l: bbox.l, t: bbox.t, r: bbox.r, b: bbox.b };
  }
  return null;
}

export type DocumentElement = {
  id: string;
  type: string;
  label: string;
  text: string;
  html?: string | null;
  image_url?: string | null;
  page?: number | null;
  level?: number | null;
  ref?: string | null;
  metadata: Record<string, unknown>;
};

export type DocumentChunk = {
  chunk_id: string;
  chunk_number: number;
  text: string;
  section_title?: string | null;
  page_number?: number | null;
  element_types: string[];
};

export type ParsedDocument = {
  document_id: string;
  filename: string;
  status: string;
  page_count: number;
  elements: DocumentElement[];
  markdown: string;
  json_export: Record<string, unknown>;
  chunks: DocumentChunk[];
  metadata: Record<string, unknown>;
};

export type JobStatus = {
  job_id: string;
  document_id: string;
  filename: string;
  stage: string;
  progress: number;
  message: string;
  status: "pending" | "running" | "complete" | "error";
  error?: string | null;
  parsed?: ParsedDocument | null;
};

export type SearchHit = {
  chunk_id: string;
  document_title: string;
  source_file: string;
  section_title?: string | null;
  page_number?: number | null;
  chunk_text: string;
  score: number;
  match_type: string;
  metadata: Record<string, unknown>;
  highlights: string[];
};

export type SearchQueryDebug = {
  documentation_url: string;
  index: string;
  search_pipeline?: string | null;
  fusion_weights: { keyword: number; vector: number };
  steps: string[];
  create_search_pipeline?: {
    method: string;
    path: string;
    body: Record<string, unknown>;
  } | null;
  search_request: {
    method: string;
    endpoint: string;
    body: Record<string, unknown>;
  };
  notes: string[];
};

export type SearchResponse = {
  query: string;
  mode: string;
  total: number;
  hits: SearchHit[];
  explanation: string;
  query_debug?: SearchQueryDebug | null;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const apiClient = {
  listSamples: () =>
    api<
      {
        filename: string;
        size_kb: number;
        tags?: string[];
        label?: string;
        description?: string;
      }[]
    >("/api/samples"),
  ingestSample: (filename: string) =>
    api<JobStatus>(`/api/ingest/sample/${encodeURIComponent(filename)}`, { method: "POST" }),
  ingestUpload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api<JobStatus>("/api/ingest/upload", { method: "POST", body: form });
  },
  getJob: (jobId: string) => api<JobStatus>(`/api/jobs/${jobId}`),
  getDocument: (documentId: string) => api<ParsedDocument>(`/api/documents/${documentId}`),
  documentFileUrl: (documentId: string) => `${API_BASE}/api/documents/${documentId}/file`,
  search: (query: string, size = 8) =>
    api<SearchResponse>("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, mode: "hybrid", size }),
    }),
  indexStats: () =>
    api<{ indexed: boolean; chunk_count: number; documents: { source_file: string; chunk_count: number }[] }>(
      "/api/index/stats"
    ),
};
