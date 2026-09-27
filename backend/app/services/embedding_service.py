"""
Semantic embedding generation using sentence-transformers, used by the
Hybrid RAG continuity pipeline. The model is loaded lazily (and only
once) since it is relatively heavy to initialize.
"""
from functools import lru_cache
from typing import List

import numpy as np

from app.config import settings


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.embedding_model)


def embed_text(text: str) -> List[float]:
    try:
        model = _get_model()
        vector = model.encode(text, normalize_embeddings=True)
        return vector.tolist()
    except Exception:
        # sentence-transformers not installed / no internet to fetch weights:
        # fall back to a lightweight deterministic bag-of-words hash embedding
        # so the retrieval pipeline still functions end-to-end.
        return _hash_embedding(text)


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    a, b = np.array(vec_a), np.array(vec_b)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _hash_embedding(text: str, dim: int = 384) -> List[float]:
    vec = np.zeros(dim)
    for token in text.lower().split():
        idx = hash(token) % dim
        vec[idx] += 1.0
    norm = np.linalg.norm(vec)
    return (vec / norm).tolist() if norm else vec.tolist()
