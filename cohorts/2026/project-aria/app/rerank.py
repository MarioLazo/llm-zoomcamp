"""Cross-encoder re-ranking (self-hosted, free).

A bi-encoder (our ONNX embedder) is fast but coarse. A cross-encoder scores
each (query, passage) pair jointly and is far more accurate — we use it to
re-order the top candidates from hybrid search before sending to the LLM.
"""
from __future__ import annotations

from functools import lru_cache

from . import config


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(config.RERANK_MODEL)


def rerank(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    """Re-score results with the cross-encoder and return the top_k."""
    if not results:
        return []
    pairs = [(query, r["text"]) for r in results]
    scores = _model().predict(pairs)
    for r, s in zip(results, scores):
        r["rerank_score"] = float(s)
    return sorted(results, key=lambda r: r["rerank_score"], reverse=True)[:top_k]
