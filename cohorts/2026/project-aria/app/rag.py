"""ARIA (Automated Regulatory Intelligence Agent) — end-to-end RAG flow:

    query rewrite  →  hybrid search  →  cross-encoder rerank  →  LLM

Three modes share the pipeline, mapped to how a compliance/regulatory officer
actually works a corpus of interview transcripts and policy documents:
  - chat     : grounded Q&A with citations, for research and investigation
  - evidence : pull verbatim, auditable quotes on a risk theme (evidence trail)
  - briefing : draft a compliance briefing outline for leadership/audit

Each call returns an answer plus the sources and timing/token metadata, which
app.monitoring persists for the dashboard.
"""
from __future__ import annotations

import time

from . import llm
from .rerank import rerank
from .search import InterviewSearch

# --- prompts -----------------------------------------------------------------

REWRITE_SYSTEM = (
    "You rewrite a user's question into a concise search query optimized for "
    "retrieval over interview transcripts and regulatory/policy documents. "
    "Preserve any named entities verbatim — borrower/company names, people, "
    "document titles, loan or policy identifiers — dropping them produces a "
    "generic query that can retrieve the wrong specific record. "
    "Return ONLY the rewritten query."
)

MODE_SYSTEM = {
    "chat": (
        "You are ARIA, a compliance research assistant answering questions using "
        "excerpts from interview transcripts and policy documents. Ground every "
        "claim in the provided context and cite the source filename in brackets, "
        "e.g. [transcript_02_infra_lead.md]. If the context does not contain the answer, say so."
    ),
    "evidence": (
        "You extract verbatim quotes relevant to the user's compliance or risk "
        "theme, for use as an auditable evidence trail. Return a bulleted list; "
        'each item is an exact quote in quotation marks followed by the source '
        "in brackets. Do not paraphrase — auditors need the original wording."
    ),
    "briefing": (
        "You draft a compliance briefing outline from interview and policy "
        "excerpts, for leadership or an audit committee. Produce 4-6 sections; "
        "each has a title and 2-3 bullets grounded in the context, with source "
        "filenames in brackets. Keep bullets tight and decision-ready. If the "
        "context includes items with a status of overdue or at-risk, you MUST "
        "call them out explicitly by name in the outline — silently omitting a "
        "slipping item from a board report is itself a governance failure, not "
        "a minor gap."
    ),
    "underwriting": (
        "You are ARIA, reviewing a commercial or agricultural loan file for "
        "underwriting documentation completeness ahead of a regulatory exam. "
        "Using ONLY the provided context, assess three required elements: "
        "Repayment Source Analysis, Cash Flow Analysis, and Collateral "
        "Valuation. For each element, respond on its own line in exactly this "
        "format:\n"
        "- <Element Name>: STATUS [source.md] — one-line summary\n"
        "where STATUS is one of PRESENT, EXCEPTION, or DOCUMENTED DEVIATION. "
        "Use PRESENT when the element is documented with sufficient analysis "
        "(repayment source: verified capacity/coverage; cash flow: reviewed "
        "statements or projections; collateral: independent valuation with a "
        "date and method) and cite the filename that proves it. Use EXCEPTION "
        "when the element is missing, stale, or carried forward without "
        "current analysis — briefly say why, and only cite a source if that "
        "source is what proves the gap (e.g. a note saying analysis was not "
        "refreshed). Use DOCUMENTED DEVIATION when the file itself states a "
        "business rationale for why the standard element does not apply or "
        "was substituted — cite the source containing that rationale. After "
        "the three lines, add exactly one summary line: 'Overall: X of 3 "
        "elements documented, Y exception(s), Z documented deviation(s).' "
        "where the counts match what you reported above. If the context does "
        "not identify which loan file to review, say so instead of guessing."
    ),
}


def _build_context(sources: list[dict]) -> str:
    blocks = []
    for s in sources:
        tag = s["source"] + (f" ({s['speaker']})" if s.get("speaker") else "")
        blocks.append(f"[{tag}]\n{s['text']}")
    return "\n\n---\n\n".join(blocks)


class RAG:
    def __init__(self, search: InterviewSearch | None = None):
        self.search = search or InterviewSearch()

    def rewrite_query(self, query: str) -> str:
        text, *_ = llm.generate(REWRITE_SYSTEM, query, smart=False)
        return text.strip() or query

    def answer(self, query: str, mode: str = "chat", top_k: int = 5) -> dict:
        t0 = time.time()

        # Query rewrite is skipped for `underwriting`: it exists to generalize
        # a conversational question into a better search query, but this mode's
        # queries name a specific borrower/loan file to look up — rewriting
        # measurably dropped that identifying detail in testing (a generic
        # "loan documentation checklist" retrieves the wrong file), the exact
        # failure mode of applying rewrite unconditionally that
        # self-review-aria.md flagged as untested risk. See eval/mou_eval.py.
        rewritten = query if mode == "underwriting" else self.rewrite_query(query)
        candidates = self.search.hybrid_search(rewritten, limit=top_k * 4)  # 2. hybrid
        sources = rerank(rewritten, candidates, top_k=top_k)  # 3. rerank

        system = MODE_SYSTEM.get(mode, MODE_SYSTEM["chat"])
        prompt = f"Context:\n{_build_context(sources)}\n\nUser request: {query}"
        # evidence/briefing benefit from the stronger model
        answer, tin, tout, model = llm.generate(system, prompt, smart=(mode != "chat"))

        return {
            "answer": answer,
            "sources": sources,
            "query": query,
            "rewritten": rewritten,
            "mode": mode,
            "model": model,
            "tokens_in": tin,
            "tokens_out": tout,
            "top_score": sources[0]["rerank_score"] if sources else 0.0,
            "num_sources": len(sources),
            "latency_ms": (time.time() - t0) * 1000,
        }
