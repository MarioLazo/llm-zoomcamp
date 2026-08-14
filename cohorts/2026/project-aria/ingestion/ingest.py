"""Ingestion: transcripts -> chunks -> embeddings -> Qdrant.

Reads markdown transcripts from TRANSCRIPTS_DIR. Each file may start with a
YAML-ish front matter line `speaker: NAME`; the rest is the transcript body.
Chunks with a sliding window (size/step from config), embeds with the ONNX
model, and upserts into a Qdrant collection configured for hybrid search
(named dense vector + BM25 sparse vector).

Invoked directly (`python -m ingestion.ingest`) or by the Kestra flow.
"""
from __future__ import annotations

import glob
import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client import models as qm

from app import bm25, config
from app.embedder import Embedder


def load_transcripts(directory: str) -> list[dict]:
    docs = []
    for path in sorted(glob.glob(os.path.join(directory, "*.md"))):
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        speaker = ""
        body = raw
        if raw.startswith("speaker:"):
            first, _, body = raw.partition("\n")
            speaker = first.split(":", 1)[1].strip()
        docs.append({"filename": os.path.basename(path), "speaker": speaker, "content": body.strip()})
    return docs


def chunk(docs: list[dict], size: int, step: int) -> list[dict]:
    chunks = []
    for d in docs:
        text = d["content"]
        for start in range(0, max(len(text), 1), step):
            piece = text[start : start + size]
            if not piece.strip():
                continue
            chunks.append(
                {"filename": d["filename"], "speaker": d["speaker"], "start": start, "content": piece}
            )
            if start + size >= len(text):
                break
    return chunks


def ensure_collection(client: QdrantClient):
    if client.collection_exists(config.QDRANT_COLLECTION):
        client.delete_collection(config.QDRANT_COLLECTION)
    client.create_collection(
        config.QDRANT_COLLECTION,
        vectors_config={
            "dense": qm.VectorParams(size=config.EMBEDDING_DIM, distance=qm.Distance.COSINE)
        },
        sparse_vectors_config={"bm25": qm.SparseVectorParams(modifier=qm.Modifier.IDF)},
    )


def run(client: QdrantClient | None = None):
    # `client` is injectable so tests/CI can pass an embedded QdrantClient
    # (e.g. QdrantClient(":memory:")) instead of requiring a running server.
    docs = load_transcripts(config.TRANSCRIPTS_DIR)
    chunks = chunk(docs, config.CHUNK_SIZE, config.CHUNK_STEP)
    print(f"Loaded {len(docs)} transcripts -> {len(chunks)} chunks")

    embedder = Embedder()
    vectors = embedder.encode_batch([c["content"] for c in chunks])
    sparse_vectors = bm25.sparse_vectors_batch([c["content"] for c in chunks])

    client = client or QdrantClient(url=config.QDRANT_URL)
    ensure_collection(client)

    points = [
        qm.PointStruct(
            id=str(uuid.uuid4()),
            vector={"dense": vec.tolist(), "bm25": svec},
            payload=c,
        )
        for c, vec, svec in zip(chunks, vectors, sparse_vectors)
    ]
    client.upsert(config.QDRANT_COLLECTION, points=points)
    print(f"Upserted {len(points)} points into '{config.QDRANT_COLLECTION}'")
    return client


if __name__ == "__main__":
    run()
