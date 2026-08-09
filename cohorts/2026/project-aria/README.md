# 🛡️ ARIA — Automated Regulatory Intelligence Agent

A privacy-preserving **RAG assistant for compliance and regulatory research**
over interview transcripts and policy documents. Ask grounded questions, pull
verbatim quotes as an auditable evidence trail, and draft compliance briefings
— all cited to source, evaluated for quality, and monitored in production.

Built as the capstone for **LLM Zoomcamp 2026**.

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

**Stack:** Qdrant · Kestra · ONNX `all-MiniLM-L6-v2` · Claude (Haiku+Sonnet) with
Gemini Flash fallback · cross-encoder rerank · Streamlit · Postgres · Docker Compose.

---

## How to run

```bash
# 1. configure secrets
cp .env.example .env        # add ANTHROPIC_API_KEY (and/or GEMINI_API_KEY)

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
python -m eval.retrieval_eval    # text vs vector vs hybrid vs hybrid+rerank
python -m eval.llm_eval          # prompt variants judged by LLM-as-judge
```

- **Retrieval** ([`eval/retrieval_eval.py`](eval/retrieval_eval.py)) — Hit-Rate@5
  and MRR@5 across **four** approaches against [`eval/ground_truth.json`](eval/ground_truth.json);
  the best (hybrid+rerank) is what the app uses.
- **LLM** ([`eval/llm_eval.py`](eval/llm_eval.py)) — **two** system-prompt variants
  scored on faithfulness + relevance by an LLM judge; the winner ships.

---

## Monitoring

Every interaction is logged to Postgres with latency, tokens (cost proxy),
retrieval score, and mode; users rate answers 👍/👎. The dashboard
([`monitoring/dashboard.py`](monitoring/dashboard.py)) renders **6 charts** plus a
feedback summary: query volume, latency distribution, tokens by model, usage by
mode, retrieval-score distribution, and feedback breakdown.

---

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
| Bonus | MCP server (`mcp_server/server.py`) |

See [`STEPS.md`](STEPS.md) for build status, remaining steps to submit, and
the peer review plan.

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
