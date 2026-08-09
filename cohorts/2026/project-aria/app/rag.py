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
        "filenames in brackets. Keep bullets tight and decision-ready."
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

        rewritten = self.rewrite_query(query)                 # 1. query rewrite
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
