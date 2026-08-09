"""Qdrant-backed search: dense (vector), sparse (BM25/keyword), and hybrid.

Hybrid fuses the two ranked lists with Reciprocal Rank Fusion (RRF, k=60) —
the same fusion we used in LLM Zoomcamp HW2.
"""
from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client import models as qm

from . import config
from .embedder import Embedder


class InterviewSearch:
    def __init__(self, embedder: Embedder | None = None, client: QdrantClient | None = None):
        # `client` is injectable so tests/CI can pass an embedded QdrantClient
        # (e.g. QdrantClient(":memory:")) instead of requiring a running server.
        self.client = client or QdrantClient(url=config.QDRANT_URL)
        self.collection = config.QDRANT_COLLECTION
        self.embedder = embedder or Embedder()

    # --- dense (semantic) ---
    def vector_search(self, query: str, limit: int = 10):
        vec = self.embedder.encode(query).tolist()
        hits = self.client.query_points(
            self.collection, query=vec, using="dense", limit=limit, with_payload=True
        ).points
        return [self._fmt(h) for h in hits]

    # --- sparse (keyword / BM25) ---
    def text_search(self, query: str, limit: int = 10):
        hits = self.client.query_points(
            self.collection,
            query=qm.Document(text=query, model="Qdrant/bm25"),
            using="bm25",
            limit=limit,
            with_payload=True,
        ).points
        return [self._fmt(h) for h in hits]

    # --- hybrid (RRF fusion of dense + sparse) ---
    def hybrid_search(self, query: str, limit: int = 10):
        vec = self.embedder.encode(query).tolist()
        hits = self.client.query_points(
            self.collection,
            prefetch=[
                qm.Prefetch(query=vec, using="dense", limit=limit * 2),
                qm.Prefetch(
                    query=qm.Document(text=query, model="Qdrant/bm25"),
                    using="bm25",
                    limit=limit * 2,
                ),
            ],
            query=qm.FusionQuery(fusion=qm.Fusion.RRF),
            limit=limit,
            with_payload=True,
        ).points
        return [self._fmt(h) for h in hits]

    @staticmethod
    def _fmt(hit):
        p = hit.payload or {}
        return {
            "score": hit.score,
            "text": p.get("content", ""),
            "source": p.get("filename", ""),
            "speaker": p.get("speaker", ""),
            "start": p.get("start", 0),
        }
