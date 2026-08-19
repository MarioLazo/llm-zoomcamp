# 🛡️ ARIA — Automated Regulatory Intelligence Agent

A privacy-preserving **RAG assistant for compliance and regulatory research**
over interview transcripts and policy documents. Ask grounded questions, pull
verbatim quotes as an auditable evidence trail, and draft compliance briefings
— all cited to source, evaluated for quality, and monitored in production.

Built as the capstone for **LLM Zoomcamp 2026**. Building this hit 10 real
bugs and a couple of eval results I didn't expect — see
[**`LESSONS_LEARNED.md`**](LESSONS_LEARNED.md) for the honest, learning-in-public
writeup (gotchas, root causes, and what I'd tell the next person).

> **Post-submission enhancement.** The course project was graded at commit
> `e1f4162` (2026-08-14). Everything below describing a fourth mode
> (`underwriting`) and a second engagement (MOU remediation) was added
> afterward, extending the same Northfield Mutual scenario into a second,
> distinct compliance domain — regulated banking, not just IT/security. See
> [`SCENARIO.md`](SCENARIO.md) for the full second-engagement writeup.

> **Why this exists.** Compliance and regulatory officers sit on stacks of
> interview transcripts, policy documents, and governance discussions that are
> nearly impossible to search by memory. When a question comes in — "what did
> we say about vendor AI risk?" — the answer has to be grounded and citable,
> not guessed. ARIA turns that pile of documents into a queryable knowledge
> base with retrieval-augmented, cited answers, themed evidence extraction,
> and briefing drafts — so research that used to take hours takes seconds.

**Demo scenario:** the sample corpus simulates SOC 2 Type II readiness for a
fictional bank's website hosting environment — interview transcripts across
five roles (CISO, infrastructure, SRE, vendor risk, compliance) plus policy
documents and a gap assessment. See [`SCENARIO.md`](SCENARIO.md) for the full
spec (client, scope, Trust Services Criteria, personas, document set).
Everything in `data/sample/` is synthetic and fictional.

---

## Status & remaining to-dos

**Project submitted** 2026-08-14 (commit `e1f4162`) for LLM Zoomcamp 2026,
Project Attempt 2. What's actually left is not code — it's a course-process
step with a real deadline:

- [ ] **Peer review — not yet assigned, watch for it.** DataTalksClub
  assigns 3 other projects to review (and 3 reviewers to ARIA) via random
  platform assignment, announced on Slack/Telegram once the cohort lead
  opens the review period. No notification pushes this — check the course
  dashboard after the announcement. **The review deadline is ~1 week from
  assignment, not from the project deadline** — per the course's own docs,
  missing it fails the project regardless of the scores received, and is
  the most common reason a passing project doesn't get a certificate.
- [ ] Complete the 3 assigned reviews within that window.
- [ ] Check back 1-2 weeks after the review deadline for ARIA's own
  scores/certificate status (also not pushed — check the platform).
- [ ] *(Optional, not required)* Deploy publicly (Streamlit Community Cloud
  or similar) for the +2 cloud-deployment bonus point, if time allows.

Full build log: [`STEPS.md`](STEPS.md). Reviewing this project?
See [`PEER_REVIEW.md`](PEER_REVIEW.md) instead.

---

## Problem description

Compliance officers, risk teams, and regulatory analysts accumulate interview
transcripts, policy discussions, and governance interviews. Finding "what did
we say about X", building an evidence trail on a risk theme, or assembling a
briefing for an audit committee is slow, manual, and error-prone — and in a
regulated context, an ungrounded or hallucinated answer isn't a minor bug,
it's a compliance incident. ARIA ingests the corpus into a hybrid-search
knowledge base and uses an LLM to answer questions, extract evidence, and
draft briefings — **grounded in the source material, with citations**, not
the model's imagination.

The included demo scenario ([`SCENARIO.md`](SCENARIO.md)) makes this concrete:
a fictional bank, Northfield Mutual, preparing SOC 2 Type II evidence for the
infrastructure hosting its public website and online banking portal.

## Data & privacy (important)

Interview transcripts contain personal, often un-consented, third-party
voices — the exact kind of data a compliance-minded design should never
expose carelessly. This repo ships with **synthetic, anonymized sample
transcripts** in [`data/sample/`](data/sample) so it is fully reproducible
without exposing anyone. A real corpus goes in `data/real/` (git-ignored) and
is ingested by pointing `TRANSCRIPTS_DIR` at it. Privacy is a **design
constraint here, not an afterthought** — fitting, for a compliance tool.

---

## Architecture

```
transcripts / policy docs (LEkE output / data/sample)
        │
        ▼   Kestra flow  (ingestion/flows/ingest_transcripts.yaml)
  chunk → embed (ONNX all-MiniLM) → upsert
        │
        ▼
   Qdrant  (dense + BM25 sparse, hybrid)
        │
        ▼   RAG (app/rag.py)
  query rewrite → hybrid search → cross-encoder rerank → LLM
        │                                     │
        ▼                                     ▼
  Streamlit UI (chat/evidence/briefing)  Postgres (logs + feedback)
                                              │
                                              ▼
                                   Monitoring dashboard (6 charts)
```

**Stack:** Qdrant · Kestra · ONNX `all-MiniLM-L6-v2` · Gemini 2.5 Flash (primary,
paid tier) with Claude (Sonnet 5 / Haiku 4.5) fallback · cross-encoder rerank ·
Streamlit · Postgres · Docker Compose. Provider choice is a deliberate,
measured decision — see [Evaluation](#evaluation) below.

---

## How to run

```bash
# 1. configure secrets
cp .env.example .env        # add GEMINI_API_KEY (primary); ANTHROPIC_API_KEY optional (fallback)

# 2. start everything (Qdrant, Postgres, app, dashboard, Kestra)
make up                     # docker compose up -d --build

# 3. download the embedding model + ingest the sample transcripts
docker compose exec app python ingestion/download_model.py
docker compose exec app python -m ingestion.ingest
#    (or trigger the Kestra flow at http://localhost:8080)

# 4. open the app
#    App:       http://localhost:8501
#    Dashboard: http://localhost:8502
#    Kestra:    http://localhost:8080
```

Local (no Docker) equivalents are in the `Makefile`: `make model`, `make ingest`,
`make app`, `make dashboard`.

### Example (using the SOC 2 demo scenario — see [`SCENARIO.md`](SCENARIO.md))

| Mode | Input | Output |
|------|-------|--------|
| 💬 Chat | "What encryption do we use for data in transit to the website?" | Grounded answer citing `[transcript_02_infra_lead.md]`, `[policy_information_security.md]` |
| 📌 Evidence | "evidence our incident response plan is tested annually" | Verbatim quotes + sources (auditable trail) |
| 📋 Briefing | "SOC 2 readiness status for the audit committee" | 4-6 section briefing outline with sources |

---

## Evaluation

Run after ingestion:

```bash
python -m eval.retrieval_eval     # text vs vector vs hybrid vs hybrid+rerank
python -m eval.llm_eval           # prompt variants judged by LLM-as-judge
python -m eval.integrity_checks   # citation integrity + prompt-injection probes
```

### Retrieval ([`eval/retrieval_eval.py`](eval/retrieval_eval.py))

Hit-Rate@5, MRR@5, and Recall@5 (completeness — several ground-truth queries
have 2-3 correct source docs, so Hit-Rate alone can hide a method missing half
the evidence trail) across **four** approaches, against
[`eval/ground_truth.json`](eval/ground_truth.json):

| Method | Hit@5 | MRR@5 | Recall@5 |
|---|---:|---:|---:|
| text (BM25) | 1.000 | 0.875 | 1.000 |
| vector | 1.000 | 0.820 | 0.917 |
| hybrid | 1.000 | **0.920** | 1.000 |
| hybrid+rerank | 1.000 | 0.883 | 1.000 |

**Honest result, not cherry-picked:** plain `hybrid` narrowly edged out
`hybrid+rerank` on MRR this run. At only 10 ground-truth queries with every
method already at a perfect 1.000 Hit-Rate, there's a ceiling effect — little
room for reranking to show a measurable lift, and the gap is plausibly noise
at this sample size. The app still ships hybrid+rerank: it's the more
principled default (reranking is a well-established practice, not something
this narrow a probe should overturn), and it costs nothing extra to keep.
Independent of the ranking question, retrieval is provider-agnostic — it
doesn't call an LLM, so this table is identical regardless of which model
answers the question.

### LLM answer quality ([`eval/llm_eval.py`](eval/llm_eval.py))

Two system-prompt variants (baseline vs. citation-strict) scored on
faithfulness + relevance (1-5) by an LLM judge, run against **both** provider
configurations for a real comparison, not an estimate:

| Provider | Variant | Faithfulness | Relevance | Tokens (40 calls) |
|---|---|---:|---:|---:|
| Claude (Sonnet+Haiku) | baseline | 5.00 | 5.00 | 115,913 |
| Claude (Sonnet+Haiku) | citation_strict | 4.80 | 4.80 | ↑ |
| Gemini 2.5 Flash | baseline | 5.00 | 5.00 | 84,548 |
| Gemini 2.5 Flash | citation_strict | 5.00 | 5.00 | ↑ |

Both providers hit or nearly hit the ceiling — with 10 queries and a 1-5
scale, this isn't enough signal to call a real quality winner between them.
**Gemini used ~27% fewer tokens** for the identical workload (mostly shorter
outputs: 2,042 vs 4,588 output tokens), which is the more decisive
difference — see [Provider comparison](#provider-comparison-claude-vs-gemini)
below.

### Citation integrity & security ([`eval/integrity_checks.py`](eval/integrity_checks.py))

Two checks a standard accuracy/relevance eval doesn't cover for a compliance
tool:

1. **Citation integrity** — does every `[filename]` cited in an answer match
   a source that was actually retrieved, or is it hallucinated? Distinct from
   "faithfulness" above — an answer can be faithful to the *wrong* cited
   source.
2. **Security** — 3 prompt-injection probes (fake system overrides, requests
   to drop citations or invent findings). Reported for manual review, not
   auto-graded, since detecting a jailbreak by string-matching is unreliable.

| Provider | Citation violations | Injection probes resisted |
|---|---:|---:|
| Claude | 0 / 10 | 3 / 3 |
| Gemini | 0 / 10 | 3 / 3 |

**A bug worth documenting, not hiding:** the first Gemini run showed 4/10
"violations." It wasn't a real gap — Gemini formats multi-source citations as
`[a.md, b.md]` in one bracket, while Claude uses separate brackets per source
(`[a.md][b.md]`). The citation-checker's regex only handled Claude's style,
so it flagged Gemini's correctly-cited, differently-formatted answers as
hallucinations. Fixed the regex to match filenames individually rather than
whole bracket contents; both providers came back at 0/10. Kept as a reminder
that eval tooling itself needs to be tested across the systems it evaluates,
not validated against just one.

### Provider comparison: Claude vs Gemini

| | Claude (Sonnet 5 + Haiku 4.5) | Gemini 2.5 Flash |
|---|---:|---:|
| `llm_eval` tokens (40 calls) | 115,913 | 84,548 |
| `integrity_checks` tokens (13 calls) | 32,828 | 29,067 |
| **Combined** | **148,741** | **113,615** |
| Citation integrity | 0/10 violations | 0/10 violations |
| Injection resistance | 3/3 | 3/3 |
| Free tier | none used (metered) | 20 req/day cap — hit it mid-eval |
| Cost | metered, pay-per-token | paid tier ($25 credit added) |

**Why Gemini ships as the default:** quality is a genuine tie on this corpus
and task, Gemini used ~24% fewer tokens for the same work, and it's already
funded. Claude stays wired as the fallback (`app/llm.py`) so a Gemini outage
degrades gracefully rather than failing closed. Worth noting: "tokens" aren't
a strictly identical unit across providers (different tokenizers), so this
comparison is directional evidence for a real decision, not a precise
cost-per-token benchmark — see `.env.example` for the free-tier gotcha that
forced this investigation in the first place (20 requests/**day**, not
per-minute, easy to blow through with an eval script that fires dozens of
calls).

---

## Monitoring

Every interaction is logged to Postgres with latency, tokens (cost proxy),
retrieval score, and mode; users rate answers 👍/👎. The dashboard
([`monitoring/dashboard.py`](monitoring/dashboard.py)) renders **6 charts** plus a
feedback summary: query volume, latency distribution, tokens by model, usage by
mode, retrieval-score distribution, and feedback breakdown.

---

## Fourth mode: `underwriting` (post-submission)

Given a loan file, ARIA assesses three required documentation elements
(repayment source, cash flow, collateral valuation) against a fixed
checklist and tags each `PRESENT` / `EXCEPTION` / `DOCUMENTED DEVIATION`
with a citation. A deterministic checker
([`app/underwriting_check.py`](app/underwriting_check.py)) verifies no
citation was hallucinated and the model's own summary count is internally
consistent — see [`SCENARIO.md`](SCENARIO.md#new-capability-underwriting-mode)
for the full design and [`eval/mou_eval.py`](eval/mou_eval.py) for the eval,
which checks against a *known* ground truth of which element is deliberately
incomplete in each of the four sample loan files.

`briefing` mode also gained a deterministic safety net for this scenario:
[`app/mou_tracker.py`](app/mou_tracker.py) reads structured MOU deadline
data independent of any LLM narrative and flags whether a drafted board
report actually mentions every overdue/at-risk item.

## Best practices implemented

- ✅ **Hybrid search** — dense + BM25 fused with RRF (Qdrant)
- ✅ **Document re-ranking** — cross-encoder over the fused candidates
- ✅ **User query rewriting** — LLM rewrite before retrieval
- 🎁 **Bonus:** [MCP server](mcp_server/server.py) exposing ARIA to Claude Desktop

---

## Rubric map (for reviewers)

| Criterion | Where |
|-----------|-------|
| Problem description | this README (top) |
| Retrieval flow (KB + LLM) | `app/rag.py`, `app/search.py` |
| Retrieval evaluation (multiple) | `eval/retrieval_eval.py` |
| LLM evaluation (multiple) | `eval/llm_eval.py` |
| Interface | `app/streamlit_app.py` (Streamlit UI) |
| Ingestion pipeline (automated) | `ingestion/flows/ingest_transcripts.yaml` (Kestra) |
| Monitoring (feedback + 6 charts) | `monitoring/dashboard.py`, `app/monitoring.py` |
| Containerization | `docker-compose.yml` (all services) |
| Reproducibility | this section + pinned `requirements.txt` + sample data |
| Best practices | hybrid search · reranking · query rewriting (above) |
| Bonus | MCP server (`mcp_server/server.py`); citation-integrity + security probes (`eval/integrity_checks.py`); measured Claude-vs-Gemini provider comparison (Evaluation section) |

See [`STEPS.md`](STEPS.md) for build status, remaining steps to submit, and
the peer review plan. **Reviewing this project?** Start with
[`PEER_REVIEW.md`](PEER_REVIEW.md) instead — it's written for you.

---

## Project layout

```
app/           RAG pipeline, search, rerank, LLM, embedder, UI, monitoring
ingestion/     model download + ingest script + Kestra flow
eval/          retrieval + LLM evaluation, ground truth
monitoring/    Streamlit monitoring dashboard
mcp_server/    MCP server (bonus)
data/sample/   synthetic transcripts (public, reproducible)
data/real/     your private corpus (git-ignored)
db/            Postgres schema
```
