from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", REPO_ROOT / "data"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", REPO_ROOT / "uploads"))
PARSED_DIR = Path(os.getenv("PARSED_DIR", REPO_ROOT / "parsed"))

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "https://localhost:9200")
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
OPENSEARCH_PASS = os.getenv("OPENSEARCH_PASS", "YourStrongPass123!")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "docling_demo")
HYBRID_PIPELINE = os.getenv("OPENSEARCH_HYBRID_PIPELINE", "docling-hybrid-pipeline")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
VECTOR_DIM = int(os.getenv("VECTOR_DIM", "384"))

KEYWORD_WEIGHT = float(os.getenv("KEYWORD_WEIGHT", "0.4"))
VECTOR_WEIGHT = float(os.getenv("VECTOR_WEIGHT", "0.6"))

CHUNK_SIZE_WORDS = int(os.getenv("CHUNK_SIZE_WORDS", "200"))
CHUNK_OVERLAP_WORDS = int(os.getenv("CHUNK_OVERLAP_WORDS", "40"))

# Docling SaaS (docling-serve)
DOCLING_SERVICE_URL = os.getenv("DOCLING_SERVICE_URL", "").rstrip("/")
DOCLING_API_KEY = os.getenv("DOCLING_API_KEY") or os.getenv("DOCLING_SERVICE_API_KEY", "")

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".md",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".tif",
    ".webp",
}

MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".webp": "image/webp",
}

for path in (DATA_DIR, UPLOAD_DIR, PARSED_DIR):
    path.mkdir(parents=True, exist_ok=True)
