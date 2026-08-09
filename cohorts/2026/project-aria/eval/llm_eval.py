"""LLM evaluation — compares prompt variants with an LLM-as-judge.

We evaluate the final answer quality for the `chat` mode across two system-prompt
variants (baseline vs. citation-strict), judged on faithfulness + relevance by a
stronger model. The higher-scoring prompt is the one to ship.

Run after ingestion:  python -m eval.llm_eval
"""
from __future__ import annotations

import json
from pathlib import Path

from app import llm
from app.rerank import rerank
from app.search import InterviewSearch

GT = json.loads((Path(__file__).parent / "ground_truth.json").read_text())

PROMPT_VARIANTS = {
    "baseline": "Answer the question using the context.",
    "citation_strict": (
        "Answer ONLY from the context. Cite the source filename in brackets for "
        "every claim. If the context lacks the answer, say 'Not in the interviews.'"
    ),
}

JUDGE_SYSTEM = (
    "You are a strict evaluator. Given a question, retrieved context, and an "
    "answer, score the answer from 1-5 on FAITHFULNESS (grounded in context, no "
    "invention) and RELEVANCE (addresses the question). Reply as JSON: "
    '{"faithfulness": n, "relevance": n}.'
)


def build_context(sources):
    return "\n\n".join(f"[{s['source']}]\n{s['text']}" for s in sources)


def judge(question, context, answer):
    prompt = f"Question: {question}\n\nContext:\n{context}\n\nAnswer:\n{answer}"
    raw, *_ = llm.generate(JUDGE_SYSTEM, prompt, smart=True)
    try:
        data = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
        return float(data["faithfulness"]), float(data["relevance"])
    except Exception:
        return 0.0, 0.0


def evaluate():
    search = InterviewSearch()
    results = {}
    for variant, system in PROMPT_VARIANTS.items():
        faith, rel = [], []
        for case in GT:
            sources = rerank(case["query"], search.hybrid_search(case["query"], limit=20), top_k=5)
            ctx = build_context(sources)
            answer, *_ = llm.generate(system, f"Context:\n{ctx}\n\nQuestion: {case['query']}")
            f, r = judge(case["query"], ctx, answer)
            faith.append(f)
            rel.append(r)
        results[variant] = {
            "faithfulness": sum(faith) / len(faith),
            "relevance": sum(rel) / len(rel),
        }
    return results


if __name__ == "__main__":
    results = evaluate()
    print(f"{'variant':<18}{'faithful':>10}{'relevance':>11}")
    for v, s in results.items():
        print(f"{v:<18}{s['faithfulness']:>10.2f}{s['relevance']:>11.2f}")
    best = max(results, key=lambda v: results[v]["faithfulness"] + results[v]["relevance"])
    print(f"\nBest prompt: {best}  ->  ship this system prompt")
