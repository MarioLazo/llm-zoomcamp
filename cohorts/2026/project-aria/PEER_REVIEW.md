# ARIA — Peer Review Guide

Thanks for taking the time to review this. This doc is written **for you, the
reviewer** — what ARIA is, what I was actually testing/learning while
building it, and exactly what to check and confirm. Should take about
15-20 minutes read + skim, or ~30 if you want to run it yourself.

If you're reviewing this reciprocally, I'll review yours the same way —
just let me know once yours is ready.

---

## What ARIA is (30 seconds)

A RAG assistant for **compliance and regulatory research** — ask grounded
questions over interview transcripts and policy documents, pull verbatim
quotes as an auditable evidence trail, or draft a compliance briefing. Every
answer is cited to source, not guessed. Demo scenario: a fictional bank
(Northfield Mutual) preparing SOC 2 Type II evidence for its website hosting
environment. All sample data is synthetic — see
[`SCENARIO.md`](SCENARIO.md) and the "Data & privacy" section of the
[README](README.md).

Full architecture, stack, and how-to-run are in the [README](README.md) —
this doc doesn't repeat that, it tells you what to actually *look at* and
*verify*.

---

## What I was learning / testing

Beyond just building a working RAG app, three things I specifically wanted
to test:

1. **Does hybrid search + reranking actually earn its keep**, or is it
   cargo-culted best practice? I ran a real 4-way retrieval comparison
   (text/vector/hybrid/hybrid+rerank) instead of assuming the "best
   practices" list is always right for a given corpus size.
2. **Does provider choice (Claude vs. Gemini) matter for quality**, or only
   for cost? I ran the *identical* eval suite against both and measured it,
   rather than picking one on vibes.
3. **What does a compliance tool need beyond standard RAG metrics?**
   Faithfulness/relevance don't catch a hallucinated *citation* (right
   content, wrong source) or a prompt-injection attempt trying to get the
   model to drop its citation requirement — so I added dedicated checks for
   both.

## Lessons learned (the honest version)

I'd rather show you the real process than a polished-after-the-fact story:

- **10 real bugs were found and fixed by actually running the code**, not
  by review alone — a version-pin conflict, a Qdrant server-side inference
  feature that doesn't work reliably self-hosted, a Streamlit `sys.path`
  gotcha that crashed the UI (never caught by `python -c` testing, only by
  opening it in a browser), a dashboard chart crash from an unserializable
  pandas type, a free-tier rate limit that blew through mid-eval, and a
  citation-format bug in my own eval tooling. Full list with fixes in
  [`STEPS.md`](STEPS.md#-completed).
- **The eval-tooling bug is the one I'd flag first**: my citation-integrity
  checker initially reported Gemini "hallucinating" 4/10 citations. It
  wasn't hallucinating — it formats multi-source citations differently than
  Claude (`[a.md, b.md]` vs. `[a.md][b.md]`), and my regex only handled
  Claude's style. Fixed the regex, both providers came back 0/10. Lesson:
  eval tooling needs testing across the systems it evaluates, not validated
  against just one — otherwise it can produce a confident, wrong conclusion.
- **Reranking didn't win on this eval set** — plain `hybrid` edged out
  `hybrid+rerank` on MRR (0.920 vs 0.883). With only 10 ground-truth queries
  and every method already at a perfect Hit-Rate, there's a ceiling effect;
  I don't read this as "don't use reranking," but I also didn't hide the
  number to make the best-practices checklist look cleaner. See the
  README's Evaluation section for the full reasoning on why it still ships.
- **Gemini vs. Claude, measured, not assumed**: same eval suite, same 10
  queries, both providers — quality was a statistical tie (both near-ceiling
  on faithfulness/relevance, both 0/10 citation violations, both 3/3
  resisted the injection probes), and Gemini used ~24% fewer tokens for
  identical work. That's the actual basis for shipping Gemini as the
  default, not a guess.

---

## What to verify — mapped to the grading rubric

| Rubric line | Where to look | What "good" looks like |
|---|---|---|
| Problem description | [README](README.md) top | Clear who this is for and why an ungrounded answer is a real compliance risk, not just a UX nitpick |
| Retrieval flow (KB + LLM) | `app/rag.py`, `app/search.py` | Hybrid search (dense + BM25 via Qdrant RRF) feeding an LLM, not just a vector lookup |
| Retrieval evaluation | [README § Evaluation](README.md#retrieval-eval-retrieval_evalpy) | 4 methods actually compared with real numbers, not just claimed |
| LLM evaluation | [README § Evaluation](README.md#llm-answer-quality-eval_llm_evalpy) | 2 prompt variants judged, **run against 2 different providers** for a real comparison |
| Interface | Screenshots in `assets/screenshots/`, or run it yourself | 3 modes (chat/evidence/briefing) actually working, not just designed |
| Ingestion pipeline | `ingestion/flows/ingest_transcripts.yaml` (Kestra) | Automated, not a manual one-off script (though the plain script path also exists and works) |
| Monitoring | `assets/screenshots/05-monitoring-dashboard.png`, `monitoring/dashboard.py` | 6 charts + feedback, populated with real logged interactions |
| Containerization | `docker-compose.yml` | Everything (Qdrant, Postgres, app, dashboard, Kestra) in one compose file |
| Reproducibility | This whole repo, `requirements.txt` pinned | Could *you* actually get this running from a clean clone? (See quick-start below.) |
| Best practices | Hybrid search, reranking, query rewriting | All 3 implemented — see whether you agree reranking still belongs given the eval result above |
| Bonus / extra | `mcp_server/server.py`, `eval/integrity_checks.py` | MCP server (Claude Desktop integration); citation-integrity + prompt-injection checks — do these feel like a real "something extra," or padding? Genuinely want your read on this |

**What I'd specifically appreciate your judgment on:**
1. Does the honest "reranking didn't win" writeup read as good scientific
   practice, or does it undercut the best-practices claim? I went back and
   forth on this.
2. Is `eval/integrity_checks.py` (citation integrity + security probes) a
   legitimate "bonus/extra," or does it feel like scope creep beyond what
   the course asked for?
3. Anything in the briefing-mode output (`assets/screenshots/04-briefing-mode-answer.png`)
   that reads as *not* board-ready, if you imagine actually handing it to a
   compliance officer?

---

## Quick verification (optional, ~10 min if you want to run it)

```bash
git clone https://github.com/MarioLazo/llm-zoomcamp.git
cd llm-zoomcamp/cohorts/2026/project-aria
cp .env.example .env        # add a free GEMINI_API_KEY: aistudio.google.com/apikey
make up
docker compose exec app python ingestion/download_model.py
docker compose exec app python -m ingestion.ingest
# open http://localhost:8501 (app) and http://localhost:8502 (dashboard)
```

If you'd rather not run it, the screenshots in `assets/screenshots/` and the
eval output captured in the README's Evaluation section cover the same
ground.

---

Thanks again for reviewing — happy to answer anything that's unclear, and
looking forward to returning the favor on yours.
