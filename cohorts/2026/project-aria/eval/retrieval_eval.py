"""Retrieval evaluation — compares FOUR approaches and picks the best.

    1. text    (BM25 / keyword)
    2. vector  (dense semantic)
    3. hybrid  (RRF fusion of the two)
    4. hybrid + cross-encoder rerank

Metrics: Hit-Rate@k and MRR@k against eval/ground_truth.json (relevance is at
the filename level — a hit is any returned chunk from a relevant transcript).

Run after ingestion:  python -m eval.retrieval_eval
"""
from __future__ import annotations

import json
from pathlib import Path

from app.rerank import rerank
from app.search import InterviewSearch

K = 5
GT = json.loads((Path(__file__).parent / "ground_truth.json").read_text())


def hit_and_rr(results, relevant, k=K):
    files = [r["source"] for r in results[:k]]
    hit = any(f in relevant for f in files)
    rr = 0.0
    for i, f in enumerate(files, start=1):
        if f in relevant:
            rr = 1.0 / i
            break
    return hit, rr


def evaluate(search: InterviewSearch):
    methods = {
        "text": lambda q: search.text_search(q, limit=K),
        "vector": lambda q: search.vector_search(q, limit=K),
        "hybrid": lambda q: search.hybrid_search(q, limit=K),
        "hybrid+rerank": lambda q: rerank(q, search.hybrid_search(q, limit=K * 4), top_k=K),
    }
    scores = {}
    for name, fn in methods.items():
        hits, rrs = [], []
        for case in GT:
            res = fn(case["query"])
            hit, rr = hit_and_rr(res, case["relevant"])
            hits.append(hit)
            rrs.append(rr)
        scores[name] = {
            "hit_rate": sum(hits) / len(hits),
            "mrr": sum(rrs) / len(rrs),
        }
    return scores


if __name__ == "__main__":
    scores = evaluate(InterviewSearch())
    print(f"{'method':<16}{'hit@'+str(K):>10}{'mrr@'+str(K):>10}")
    for name, s in scores.items():
        print(f"{name:<16}{s['hit_rate']:>10.3f}{s['mrr']:>10.3f}")
    best = max(scores, key=lambda n: (scores[n]["mrr"], scores[n]["hit_rate"]))
    print(f"\nBest approach: {best}  ->  use this in production")
