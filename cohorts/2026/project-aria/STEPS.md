# ARIA — Build Status & Submission Steps

Companion to [`README.md`](README.md) (product/architecture) — this file tracks
**what's done, what's left, and the peer review plan** for the LLM Zoomcamp 2026
capstone.

## Origin

ARIA started as a general "research assistant over interview transcripts" idea
(working name: Interview Vault), then was repositioned as a **compliance /
regulatory intelligence agent** — a better fit for real-world use (audit
evidence trails, briefing drafts, grounded-not-guessed answers) and for a
portfolio aimed at regulated-industry AI delivery work. The architecture didn't
change; the framing, UI modes, and prompts did.

## ✅ Completed

- Full architecture designed and scaffolded: Qdrant (hybrid BM25+dense) ·
  Kestra ingestion · ONNX `all-MiniLM-L6-v2` embeddings (reused from HW2) ·
  cross-encoder rerank · query rewriting · Claude (Haiku+Sonnet) with Gemini
  fallback · Streamlit UI (chat/evidence/briefing) · Postgres-backed
  monitoring dashboard (6 charts + feedback) · full `docker-compose.yml` ·
  retrieval + LLM evaluation scripts · MCP server bonus.
- **Review pass found and fixed 4 real bugs** before this had ever been run:
  1. `fastembed` was missing from `requirements.txt` — BM25 sparse embedding
     would have crashed on first ingest/search.
  2. The local `mcp/` folder name collided with the installed `mcp` pip
     package (Anthropic's MCP SDK) — renamed to `mcp_server/`.
  3. The Kestra service had no Docker socket mounted, so the ingest flow
     (which launches the app image as a task container) had no way to reach
     the Docker daemon — added the socket mount + explicit `depends_on`.
  4. Evaluation scripts resolved `ground_truth.json` relative to the process's
     working directory instead of the script's own location — fixed to be
     CWD-independent.
- Rebranded to ARIA: renamed UI modes to match a compliance officer's actual
  workflow (`chat` → grounded Q&A, `evidence` → auditable verbatim quotes,
  `briefing` → compliance briefing outline), updated system prompts, Docker
  image names, and the Kestra flow/namespace accordingly.
- Sample data: 4 synthetic, anonymized interviews already themed around AI
  governance in regulated industries (healthcare CISO, bank head of data,
  manufacturing VP, privacy counsel) — a natural fit for the compliance
  framing, no rework needed there.

## 🔜 Remaining steps to submit

1. **Run it for real**, locally (this environment couldn't reach
   `huggingface.co` to download the ONNX model, so it's unverified end-to-end):
   - `cp .env.example .env` and add `ANTHROPIC_API_KEY` (and/or `GEMINI_API_KEY`)
   - `make up`
   - `docker compose exec app python ingestion/download_model.py`
   - `docker compose exec app python -m ingestion.ingest` (or trigger the
     Kestra flow in the UI)
2. **Smoke-test the app** — run a query in each mode (chat / evidence /
   briefing), confirm citations are correct and the sources panel populates.
3. **Run the eval scripts** — `python -m eval.retrieval_eval` and
   `python -m eval.llm_eval` — capture the printed comparison tables.
4. **Generate monitoring data** — run ~10-15 varied queries so the dashboard
   has something to chart; rate a few 👍/👎.
5. **Screenshot everything** — chat/evidence/briefing modes, the eval output,
   and the dashboard — and drop them into the README.
6. **Push the final commit** and note the commit hash for submission.
7. **Submit the project form** with the repo link + commit hash:
   https://courses.datatalks.club/llm-zoomcamp-2026/homework/project
8. **(Bonus, optional)** Deploy the app somewhere public (Streamlit Community
   Cloud or similar) for the +2 cloud-deployment bonus point.

## 👥 Peer review plan

Planning to exchange peer reviews with **Hoc, Ravi, and Harish**. The course
requires reviewing 3 peers' projects to become certificate-eligible — confirm
with each of them that the review is reciprocal (they review ARIA, and I
review theirs) and check the cohort's review-submission deadline before it
closes: https://courses.datatalks.club/llm-zoomcamp-2026/homework/project

## Certificate requirement (confirmed from the course README)

> Complete the final project → peer review 3 projects → meet the cohort
> deadlines → certificates are issued after all peer reviews are completed.

No minimum point score is stated — the bar is a **complete, reproducible
submission**, reviewed and submitted on time.
