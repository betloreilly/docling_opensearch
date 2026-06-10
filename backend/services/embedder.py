from __future__ import annotations

import threading

from backend.config import EMBEDDING_MODEL

_model = None
_lock = threading.Lock()


def get_embedder():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_text(text: str) -> list[float]:
    model = get_embedder()
    vector = model.encode(text[:8000], normalize_embeddings=True)
    return vector.tolist()
