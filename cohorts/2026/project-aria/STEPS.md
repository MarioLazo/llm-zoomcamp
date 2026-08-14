# ARIA — Build Status & Submission Steps

Companion to [`README.md`](README.md) (product/architecture) — this file tracks
**what's done, what's left, and the peer review plan** for the LLM Zoomcamp 2026
capstone.

## ⏰ Deadline

**Project Attempt 2 — due Monday, 17 August 2026, 23:00 UTC.**
Submit/update here: https://courses.datatalks.club/llm-zoomcamp-2026/project/project2

## Origin

ARIA started as a general "research assistant over interview transcripts" idea
(working name: Interview Vault), then was repositioned as a **compliance /
regulatory intelligence agent** — a better fit for real-world use (audit
evidence trails, briefing drafts, grounded-not-guessed answers) and for a
portfolio aimed at regulated-industry AI delivery work. The architecture didn't
change; the framing, UI modes, and prompts did.

The sample corpus was then replaced with a single coherent, fully synthetic
demo scenario — SOC 2 Type II readiness for a fictional bank's website
hosting environment — instead of generic, unrelated interviews. See
[`SCENARIO.md`](SCENARIO.md) for the full spec.

## ✅ Completed

- Full architecture designed and scaffolded: Qdrant (hybrid BM25+dense) ·
  Kestra ingestion · ONNX `all-MiniLM-L6-v2` embeddings (reused from HW2) ·
  cross-encoder rerank · query rewriting · Gemini 2.5 Flash primary with
  Claude (Sonnet 5 / Haiku 4.5) fallback · Streamlit UI (chat/evidence/
  briefing) · Postgres-backed monitoring dashboard (6 charts + feedback) ·
  full `docker-compose.yml` · retrieval + LLM + integrity/security
  evaluation scripts · MCP server bonus.
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
- **Demo scenario built:** replaced the generic sample data with a coherent,
  fully synthetic SOC 2 Type II readiness engagement for a fictional bank
  (Northfield Mutual) — 5 interview transcripts (CISO, infrastructure, SRE,
  vendor risk, compliance) + 4 policy excerpts + a gap assessment memo. Spec
  in [`SCENARIO.md`](SCENARIO.md); `eval/ground_truth.json` rewritten to match
  (10 queries mapped to the new corpus).
- **Second review pass (2026-08-14), cross-checked against a purpose-built
  LLM Zoomcamp knowledge base** (official course repo lessons + video
  playlist, extracted to `mario-dev/kb/llm-zoomcamp/`) — found and fixed 4
  more issues before the first real run:
  1. UI placeholders (`app/streamlit_app.py`) were still pre-rebrand "AI
     adoption fear" copy, not the SOC 2 scenario — updated to match.
  2. Claude model IDs were Oct 2024 snapshots, likely retired — updated to
     current (`claude-sonnet-5` / `claude-haiku-4-5-20251001`).
  3. `app/embedder.py` never called `enable_truncation()` despite chunks up
     to 2000 chars vs. the model's 512-token limit — added an explicit
     `MAX_SEQ_LEN=512` truncation guard.
  4. `db/init.sql`'s `mode` column comment still listed pre-rebrand mode
     names (`chat | quotes | slides`) — fixed to `chat | evidence | briefing`.
- **`PRIMARY_LLM` switched to Gemini by default** — free tier, avoids metered
  API cost on the ~40+ calls `eval/llm_eval.py` makes per run. Claude stays
  wired as fallback only. Also fixed inline-comment formatting in
  `.env`/`.env.example` (`VALUE   # comment` on one line) that Docker
  Compose's `env_file` parser doesn't reliably strip — moved comments to
  their own line.
- **Environment re-verified on the actual run machine (canon-beast,
  2026-08-14):** `huggingface.co`, `api.anthropic.com`,
  `generativelanguage.googleapis.com`, and the Docker registry are all
  reachable; Docker/OrbStack is running. The earlier "couldn't reach
  huggingface.co" blocker below was from a different, more restricted
  sandbox — confirmed not to apply on canon-beast.
- **Ingestion source confirmed:** `data/sample/` (10 docs — 5 transcripts +
  4 policies + 1 gap assessment, 2,871 words total) is what gets ingested.
  It already matches every entry in `eval/ground_truth.json` exactly — no
  real corpus needed or planned; `data/real/` stays empty by design
  (privacy, per the README).
- **First real end-to-end run (2026-08-14, canon-beast).** `make up` →
  download model → ingest → smoke-test all 3 modes → both eval scripts →
  monitoring data → screenshots, all actually executed, not just planned.
  Found and fixed **6 more real bugs**, none catchable without actually
  running it:
  1. `onnxruntime==1.20.1` conflicted with `fastembed==0.4.2`'s own pin
     (`<1.20.0`) — pip couldn't resolve `requirements.txt` at all. Downgraded
     to `onnxruntime==1.19.2`.
  2. Qdrant's server-side BM25 inference (`models.Document(text=..., model=
     "Qdrant/bm25")`) errored with `InferenceService is not initialized` —
     that inference path isn't reliably available self-hosted (Cloud-only in
     practice). Moved to client-side BM25 embedding via `fastembed` directly
     (new `app/bm25.py`), used by both `search.py` and `ingestion/ingest.py`.
  3. **The Streamlit UI itself crashed** (`ModuleNotFoundError: No module
     named 'app'`) — `streamlit run app/streamlit_app.py` only adds the
     script's own directory to `sys.path`, not the project root, so `from
     app import monitoring` failed. Every test before this used `python -c`/
     `python -m`, which don't hit this path — only opening the actual UI in
     a browser caught it. Fixed with `ENV PYTHONPATH=/project` in the
     Dockerfile.
  4. **Two dashboard charts crashed** (`SchemaValidationError`) — `pd.cut()`
     produces a pandas `IntervalIndex`, which Vega-Lite (via `st.bar_chart`)
     can't serialize. Cast bin labels to `str` before charting in both
     Chart 2 (latency) and Chart 5 (retrieval score).
  5. Gemini's free tier caps at **20 requests/DAY** (not per-minute) — blew
     through it mid-eval. Added rate-limit-aware retry/backoff to
     `app/llm.py`, and switched to Claude (real key added) to finish the
     first full eval pass while Gemini's daily quota was exhausted.
  6. `eval/integrity_checks.py`'s citation-integrity regex assumed Claude's
     citation style (`[a.md][b.md]`, one file per bracket) and false-flagged
     Gemini's equally-correct `[a.md, b.md]` style as "hallucinated
     citations" (4/10). Fixed to match filenames individually; both
     providers came back 0/10. See README's Evaluation section for the full
     writeup — this is now documented as a lesson, not hidden.
- **Provider switched to Gemini as final default** (`PRIMARY_LLM=gemini`) —
  $25 paid credit added, removing the free-tier cap above. Ran both eval
  scripts fresh on **both** Claude and Gemini for a real comparison (not an
  estimate): Gemini used ~24% fewer tokens for identical quality (0/10
  citation violations, 3/3 injection probes resisted, near-ceiling
  faithfulness/relevance on both). Full comparison table in the README.
- **Real screenshots captured** (`assets/screenshots/`): empty + answered
  chat mode, evidence mode, briefing mode, and the full 6-chart monitoring
  dashboard with real data (17 logged interactions across all 3 modes and
  all 3 models tested).

## 🔜 Remaining steps to submit

1. ✅ ~~Run it for real~~ — done, all 6 bugs above found running it.
2. ✅ ~~Smoke-test the app~~ — all 3 modes confirmed working with correct
   citations; screenshots captured.
3. ✅ ~~Run the eval scripts~~ — `retrieval_eval`, `llm_eval`,
   `integrity_checks` all run (the last two on both providers).
4. ✅ ~~Generate monitoring data~~ — 12 varied queries + 👍/👎 ratings logged;
   dashboard confirmed rendering all 6 charts correctly.
5. ✅ ~~Screenshot everything~~ — captured, dashboard bug found+fixed in the
   process.
6. **Push the final commit** and note the commit hash for submission.
7. **Submit the project form** with the repo link + commit hash:
   https://courses.datatalks.club/llm-zoomcamp-2026/homework/project
   (also asks for optional learning-in-public links, hours spent, and an
   optional FAQ PR link — none of these are decided yet, see below)
8. **(Bonus, optional)** Deploy the app somewhere public (Streamlit Community
   Cloud or similar) for the +2 cloud-deployment bonus point.

## 💡 Optional lessons-learned additions (not yet applied — pending review)

Cheap, high-value additions surfaced by cross-referencing ARIA against the
LLM Zoomcamp knowledge base, held until reviewed:

1. `CREATE INDEX` on `interactions(ts)` in `db/init.sql` — Module 5 and the
   Monitoring video both call out timestamp-index performance as a real
   gotcha hit live in the course.
2. Manually sanity-read the 10 `ground_truth.json` queries once before
   trusting the eval numbers — the Evaluation video repeatedly warns
   synthetic ground truth "can look artificially good."
3. Spot-check 2-3 LLM-judge verdicts by hand once `eval/llm_eval.py` runs,
   and note the check here — same lesson: don't trust a judge blindly.
4. One-line "known limitation" note on prompt-injection/data-leakage
   awareness (a compliance tool handling an audit trail should at least
   name this risk, per a gotcha called out in the Build-First-RAG video).

## ❓ Open items still to decide

- **Learning-in-public links** (submission form allows up to 14, optional) —
  none identified yet.
- **Hours spent** (submission form field) — not tracked yet; estimate before
  submitting.
- **Certificate name** — confirm exact spelling to use on the form.
- **FAQ contribution PR/issue** (optional) — not planned; skip unless there's
  a reason to.
- **Cloud deployment bonus** (+2, optional) — decide after the core
  submission is solid and time remains before the deadline.

## 👥 Peer review plan

Reached out to **4 people** about a reciprocal review exchange, 3 named so
far: **Hoc, Ravi, and Harish** (+ 1 more to confirm/name here). The course
requires reviewing 3 peers' projects to become certificate-eligible — confirm
with each of them that the review is reciprocal (they review ARIA, and I
review theirs), and check the review-submission deadline on the project page
(it may differ from the project submission deadline above):
https://courses.datatalks.club/llm-zoomcamp-2026/project/project2

**[`PEER_REVIEW.md`](PEER_REVIEW.md)** is the reviewer-facing doc — send that
link (at the submitted commit) to each of the 4, not this file. It covers
what the project is, what I was testing/learning, an honest lessons-learned
summary (the 10 bugs, the eval-tooling bug specifically), a rubric-mapped
checklist of what to verify, and 3 specific questions I want their judgment
on. Draft the outreach email/message once the commit is pushed — link to
`PEER_REVIEW.md` at that exact commit, not a moving `main` branch link.

## Certificate requirement (confirmed from the course README)

> Complete the final project → peer review 3 projects → meet the cohort
> deadlines → certificates are issued after all peer reviews are completed.

No minimum point score is stated — the bar is a **complete, reproducible
submission**, reviewed and submitted on time.
