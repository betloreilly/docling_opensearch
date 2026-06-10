from __future__ import annotations

import asyncio
import json
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import httpx

from backend.config import (
    DATA_DIR,
    DOCLING_API_KEY,
    DOCLING_SERVICE_URL,
    MEDIA_TYPES,
    SUPPORTED_EXTENSIONS,
    UPLOAD_DIR,
)
from backend.models.schemas import JobStatus, ParsedDocument, SearchRequest, SearchResponse
from backend.services import docling_service, opensearch_service

app = FastAPI(
    title="Docling + OpenSearch Demo",
    description="Document ingestion with Docling and hybrid search with OpenSearch",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_jobs: dict[str, JobStatus] = {}
_doc_files: dict[str, Path] = {}


STAGES = [
    ("upload", 10, "Upload complete"),
    ("parsing", 35, "Parsing with Docling SaaS"),
    ("structure", 60, "Extracting document structure"),
    ("preparing", 80, "Preparing content for OpenSearch"),
    ("indexing", 95, "Indexing into OpenSearch"),
    ("complete", 100, "Indexing complete"),
]


def _resolve_file(document_id: str) -> Path | None:
    if document_id in _doc_files:
        path = _doc_files[document_id]
        if path.exists():
            return path

    for pattern in (f"{document_id}_*", f"{document_id}*"):
        for path in UPLOAD_DIR.glob(pattern):
            if path.is_file():
                return path

    parsed = docling_service.load_parsed(document_id)
    if parsed:
        source_path = parsed.metadata.get("source_path")
        if source_path:
            candidate = Path(str(source_path))
            if candidate.exists():
                return candidate
        for directory in (UPLOAD_DIR, DATA_DIR):
            candidate = directory / parsed.filename
            if candidate.exists():
                return candidate
            for path in directory.glob(f"{document_id}_*"):
                if path.is_file():
                    return path

    for directory in (UPLOAD_DIR, DATA_DIR):
        for path in directory.iterdir():
            if path.is_file() and path.stem.startswith(document_id):
                return path
    return None


async def _run_ingest_job(job_id: str, file_path: Path, document_id: str, filename: str) -> None:
    try:
        for stage_id, progress, message in STAGES[:-1]:
            job = _jobs[job_id]
            job.stage = stage_id
            job.progress = progress
            job.message = message
            job.status = "running"
            _jobs[job_id] = job
            await asyncio.sleep(0.4 if stage_id != "parsing" else 0.8)

        parsed = await asyncio.to_thread(docling_service.parse_document, file_path, document_id)
        job = _jobs[job_id]
        job.stage = "preparing"
        job.progress = 80
        job.message = "Preparing content for OpenSearch"
        job.parsed = parsed
        _jobs[job_id] = job

        chunk_count = await asyncio.to_thread(opensearch_service.index_document, parsed)

        job = _jobs[job_id]
        job.stage = "complete"
        job.progress = 100
        job.message = f"Indexing complete — {chunk_count} chunks indexed"
        job.status = "complete"
        job.parsed = parsed
        _jobs[job_id] = job
    except Exception as exc:
        job = _jobs[job_id]
        job.status = "error"
        job.error = str(exc)
        job.message = "Ingestion failed"
        _jobs[job_id] = job


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/docling/status")
def docling_status() -> dict:
    """Lightweight Docling SaaS connectivity check (health endpoint only)."""
    if not DOCLING_SERVICE_URL:
        return {"ok": False, "error": "DOCLING_SERVICE_URL is not set in .env"}
    if not DOCLING_API_KEY:
        return {"ok": False, "error": "DOCLING_API_KEY is not set in .env"}
    try:
        response = httpx.get(
            f"{DOCLING_SERVICE_URL.rstrip('/')}/health",
            headers={"X-Api-Key": DOCLING_API_KEY},
            timeout=15.0,
        )
        return {
            "ok": response.status_code == 200,
            "health_status": response.status_code,
            "service_url": DOCLING_SERVICE_URL,
            "hint": (
                "Health OK but uploads still fail? Regenerate your API key and confirm "
                "DOCLING_SERVICE_URL matches your IBM Docling SaaS instance."
                if response.status_code == 200
                else "Docling SaaS health check failed — verify credentials in .env."
            ),
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "error": f"Could not reach Docling SaaS: {exc}"}


def _load_sample_manifest() -> dict[str, dict]:
    manifest_path = DATA_DIR / ".samples_manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


@app.get("/api/samples")
def list_samples() -> list[dict]:
    manifest = _load_sample_manifest()
    samples = []
    for path in sorted(DATA_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            entry: dict = {
                "filename": path.name,
                "size_kb": round(path.stat().st_size / 1024, 1),
            }
            if path.name in manifest:
                entry.update(manifest[path.name])
            samples.append(entry)

    def sort_key(item: dict) -> tuple[int, str]:
        featured = 0 if item.get("tags") else 1
        return (featured, item["filename"].lower())

    samples.sort(key=sort_key)
    return samples


@app.post("/api/ingest/sample/{filename}")
async def ingest_sample(filename: str) -> JobStatus:
    file_path = DATA_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sample not found")
    document_id = uuid.uuid4().hex[:12]
    dest = UPLOAD_DIR / f"{document_id}_{filename}"
    shutil.copy(file_path, dest)
    _doc_files[document_id] = dest

    job_id = uuid.uuid4().hex[:12]
    job = JobStatus(
        job_id=job_id,
        document_id=document_id,
        filename=filename,
        stage="upload",
        progress=10,
        message="Upload complete",
        status="running",
    )
    _jobs[job_id] = job
    asyncio.create_task(_run_ingest_job(job_id, dest, document_id, filename))
    return job


@app.post("/api/ingest/upload")
async def ingest_upload(file: UploadFile = File(...)) -> JobStatus:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    document_id = uuid.uuid4().hex[:12]
    dest = UPLOAD_DIR / f"{document_id}_{file.filename}"
    content = await file.read()
    dest.write_bytes(content)
    _doc_files[document_id] = dest

    job_id = uuid.uuid4().hex[:12]
    job = JobStatus(
        job_id=job_id,
        document_id=document_id,
        filename=file.filename,
        stage="upload",
        progress=10,
        message="Upload complete",
        status="running",
    )
    _jobs[job_id] = job
    asyncio.create_task(_run_ingest_job(job_id, dest, document_id, file.filename))
    return job


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> JobStatus:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/documents/{document_id}")
def get_document(document_id: str) -> ParsedDocument:
    parsed = docling_service.load_parsed(document_id)
    if not parsed:
        raise HTTPException(status_code=404, detail="Document not found")
    return parsed


@app.get("/api/documents/{document_id}/file")
def get_document_file(document_id: str):
    file_path = _resolve_file(document_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    media = MEDIA_TYPES.get(file_path.suffix.lower(), "application/octet-stream")
    return FileResponse(
        file_path,
        media_type=media,
        filename=file_path.name,
        content_disposition_type="inline",
    )


@app.post("/api/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query required")
    return opensearch_service.search(req.query, req.mode, req.size)


@app.get("/api/index/stats")
def index_stats() -> dict:
    return opensearch_service.get_index_stats()
