"""LLM evaluation — compares prompt variants with an LLM-as-judge.

We evaluate the final answer quality for the `chat` mode across two system-prompt
variants (baseline vs. citation-strict), judged on faithfulness + relevance by a
stronger model. The higher-scoring prompt is the one to ship.

Run after ingestion:  python -m eval.llm_eval

Note: paces LLM calls (~13s apart) to stay under Gemini's free-tier 5
requests/minute cap — this script alone makes ~40 calls (2 variants x 10
queries x generate+judge), which blows through that limit if fired back-to-back.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from app import llm
from app.rerank import rerank
from app.search import InterviewSearch

GT = json.loads((Path(__file__).parent / "ground_truth.json").read_text())
# 13s was sized for Gemini's free-tier 5/min cap; Claude's rate limits are
# much higher, so this only needs to be a light courtesy pace now.
CALL_PACING_SECONDS = 2

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


def judge(question, context, answer, usage):
    prompt = f"Question: {question}\n\nContext:\n{context}\n\nAnswer:\n{answer}"
    raw, tin, tout, model = llm.generate(JUDGE_SYSTEM, prompt, smart=True)
    usage["tokens_in"] += tin
    usage["tokens_out"] += tout
    usage["calls"] += 1
    usage["model"] = model
    try:
        data = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
        return float(data["faithfulness"]), float(data["relevance"])
    except Exception:
        return 0.0, 0.0


def evaluate():
    search = InterviewSearch()
    results = {}
    total_cases = len(PROMPT_VARIANTS) * len(GT)
    done = 0
    usage = {"tokens_in": 0, "tokens_out": 0, "calls": 0, "model": None}
    for variant, system in PROMPT_VARIANTS.items():
        faith, rel = [], []
        for case in GT:
            sources = rerank(case["query"], search.hybrid_search(case["query"], limit=20), top_k=5)
            ctx = build_context(sources)
            answer, tin, tout, model = llm.generate(system, f"Context:\n{ctx}\n\nQuestion: {case['query']}")
            usage["tokens_in"] += tin
            usage["tokens_out"] += tout
            usage["calls"] += 1
            usage["model"] = model
            time.sleep(CALL_PACING_SECONDS)
            f, r = judge(case["query"], ctx, answer, usage)
            done += 1
            print(f"  [{done}/{total_cases}] {variant}: {case['query'][:60]}...")
            if done < total_cases:
                time.sleep(CALL_PACING_SECONDS)
            faith.append(f)
            rel.append(r)
        results[variant] = {
            "faithfulness": sum(faith) / len(faith),
            "relevance": sum(rel) / len(rel),
        }
    return results, usage


if __name__ == "__main__":
    results, usage = evaluate()
    print(f"{'variant':<18}{'faithful':>10}{'relevance':>11}")
    for v, s in results.items():
        print(f"{v:<18}{s['faithfulness']:>10.2f}{s['relevance']:>11.2f}")
    best = max(results, key=lambda v: results[v]["faithfulness"] + results[v]["relevance"])
    print(f"\nBest prompt: {best}  ->  ship this system prompt")
    total_tok = usage["tokens_in"] + usage["tokens_out"]
    print(
        f"\nToken usage: {usage['calls']} calls, {usage['tokens_in']} in + "
        f"{usage['tokens_out']} out = {total_tok} total (model: {usage['model']})"
    )
