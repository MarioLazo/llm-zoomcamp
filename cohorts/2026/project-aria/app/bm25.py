"""Client-side BM25 sparse embedding, shared by search.py and ingestion/ingest.py.

Qdrant's server-side BM25 inference (passing `models.Document(text=..., model=
"Qdrant/bm25")` directly) errors with "InferenceService is not initialized" on
this self-hosted setup — that inference path isn't reliably available outside
Qdrant Cloud. Computing the sparse vector locally with fastembed (already a
dependency for BM25 support) sidesteps the server-side dependency entirely.
"""
from __future__ import annotations

from functools import lru_cache

from qdrant_client import models as qm


@lru_cache(maxsize=1)
def _model():
    from fastembed import SparseTextEmbedding

    return SparseTextEmbedding(model_name="Qdrant/bm25")


def sparse_vector(text: str) -> qm.SparseVector:
    emb = next(_model().embed([text]))
    return qm.SparseVector(indices=emb.indices.tolist(), values=emb.values.tolist())


def sparse_vectors_batch(texts: list[str]) -> list[qm.SparseVector]:
    return [
        qm.SparseVector(indices=e.indices.tolist(), values=e.values.tolist())
        for e in _model().embed(texts)
    ]
