# Peer review — `wc2026_rag` (romadvincula)

Assigned peer review, LLM Zoomcamp 2026, Project Attempt 2. Repo:
[romadvincula/wc2026_rag](https://github.com/romadvincula/wc2026_rag), commit
`c516557`. Rubric scores were submitted on the course platform; this
document is the deeper analysis — design decisions, what's actually strong,
what's actually weak, and what it illustrates by contrast with the other
project I reviewed this cycle
([`knowledge-base-assistant-bot`](knowledge-base-assistant-bot.md)).

Verification method: cloned the repo at the pinned commit, ran `uv sync`
(clean), and — rather than trusting the code by reading — actually executed
the ingestion path (`ingest.load_indices()`) against the committed
`data/wc_news.csv`, with no API key, and confirmed it builds both indices
and returns a sensible result. Also read `demo.ipynb` cell-by-cell (80
cells) to reconstruct the actual retrieval-evaluation work, since the README
doesn't describe it — it only lives in the notebook.

## Start here: plain-English summary

### What it is

A chatbot that answers questions about the 2026 World Cup using a database
of about 11,000 real news articles — ask "when did France leave the
tournament?" and it searches the news archive and answers from what it
actually finds, styled as a sports reporter.

### The report card

**13 out of 21** on the course's grading checklist — a real, working
project with some significant, identifiable gaps.

### What we found, the good part

I didn't just read the code — I downloaded it and ran the core
search-and-answer logic myself, with no shortcuts, and it correctly found
and used the real news data with zero errors. There's also careful work
hiding in a notebook that the project's own README never mentions: a proper
progression from plain keyword search, to several tuned versions of
AI-based ("semantic") search, to a combined approach — the combined
approach clearly won, and that's the one actually wired into the live app.

### What we found, the gaps

- **A monitoring feature that looks built but isn't.** There's a database
  set up to store user feedback (thumbs up/down) and usage stats for a
  dashboard — but nothing in the actual app ever writes to it. The tables
  exist; nothing uses them. Looking at just the database structure, you'd
  assume monitoring works. It doesn't.
- **No one-command setup.** The course (and good practice generally) wants
  a project packaged so anyone can run it with one command (a "Docker"
  setup). This one has none — which is a fixable gap, not a hard one.
- **Only one version of the final "answer" step was ever tested.** So there's
  no real evidence the way it's built now beats some alternative — a second
  version was never compared against it.
- **The write-up doesn't explain why this beats just asking a general
  chatbot the same question** — a good compliance/finance-facts assistant
  needs that "why us, not ChatGPT" argument, and this one skips it.

### Bottom line

The hard, technical middle of the project — search, retrieval, actually
working code — is solid, arguably stronger than expected once you dig in.
What's missing clusters almost entirely in the "ran out of time" tier:
packaging, finishing the feedback feature, and a second layer of testing.
None of it requires touching the parts that already work.

---

## Detailed rubric score, with evidence

| # | Criterion | Score | Evidence — what I actually checked |
|---|---|---|---|
| 1 | Retrieval evaluation | 2/2 | `demo.ipynb` runs keyword-only → vector search (5 field combinations tested) → hybrid/RRF; hybrid wins and is the config actually wired into `wc2026_assistant/rag.py` |
| 2 | RAG evaluation | 1/2 | Only one prompt/retrieval configuration is judged for answer quality — no second variant is compared against it |
| 3 | Interface | 2/2 | Flask API (`/question` route in `app.py`) plus a Streamlit chat frontend (`frontend.py`) |
| 4 | Ingestion pipeline | 2/2 | `ingest.load_indices()` builds both search indices automatically on startup — I ran this function myself against the real 11,158-row dataset with no API key and it worked cleanly |
| 5 | Monitoring | 0/2 | `db/db_init.py` creates real `conversations`/`feedback` tables, but `db/transactions.py`'s `save_conversations()` has no actual `INSERT` statement and nothing calls it; no `/feedback` route in `app.py`; no rating UI in `frontend.py` — verified by reading all three files directly |
| 6 | Containerization | 0/2 | No Dockerfile, no docker-compose file anywhere in the repository — confirmed by listing the full repo tree |
| 7 | Problem description | 1/2 | README states what the app does and how to run it in about five lines, but never argues why this beats a general chat model directly |
| 8 | RAG flow | 2/2 | Real knowledge base (the news dataset, indexed) feeding a real LLM call |
| 9 | Reproducibility | 2/2 | `uv sync` installed cleanly; I personally ran the ingestion path against the committed `data/wc_news.csv` (11,158 rows) with zero API key and it produced a correct result |
| 10 | Best practices | 1/3 | Hybrid search implemented and evaluated (1 point). I grepped the entire codebase for "rerank," "rewrite," and "reformulat" and found no matches outside article body text — no reranking, no query rewriting (0 of the remaining 2 points) |
| **Total** | | **13/21** | No bonus |

---

## The detailed version

Everything above is the plain-English summary and the scored evidence.
Everything below is the full narrative review.

---

## What it is

A RAG assistant answering questions about FIFA World Cup 2026 news as a
"sports reporter," over an ~11,000-record cleaned news dataset. Flask
backend (`/question` endpoint) + Streamlit chat frontend. Keyword (minsearch)
+ vector (sentence-transformers) + RRF hybrid retrieval.

## What's genuinely strong, and easy to miss because the README undersells it

**The retrieval evaluation in `demo.ipynb` is real, methodologically sound
work that the README doesn't even mention.** The notebook runs a proper
progression: keyword-only baseline (hit_rate 0.373, mrr 0.267) → vector
search with *five different field combinations tested* (title+description
wins at 0.355/0.236, beating content-only and description-only) → hybrid via
RRF, which wins outright (hit_rate 0.5, mrr 0.307 at k=10) — and the winning
configuration is what's actually wired into `wc2026_assistant/rag.py`. That
field-combination sweep for the vector index is more thorough than most
projects manage for their own embedding inputs. The comment "results are
very poor when using keyword search only" in the notebook is also a small,
honest, unprompted admission worth noting — it's just less visible because
it's buried in a notebook comment rather than surfaced in the README.

**I verified the core loop actually runs, not just that it reads
plausibly.** Running `ingest.load_indices()` directly built both the
minsearch keyword index and the sentence-transformer vector index from the
real 11,158-row CSV and returned a correct top result for "France exit
tournament" with zero errors, zero missing files, and no API key required.
Given that neither Docker nor a database is required for the actual
retrieval+ingestion path, this is meaningfully more validated than a README
read-through would suggest — the essential rubric requirements (ingestion,
retrieval, RAG flow, interface) are solid engineering; the gaps below are
concentrated almost entirely in the "extra credit" tier.

## Weaknesses — with the reasoning behind each score, not just the number

**Monitoring (0/2) is the most instructive gap in this review cycle, and
worth explaining precisely because it's a specific, avoidable failure mode
rather than "didn't get to it."** `db/db_init.py` creates real
`conversations` and `feedback` tables with a sensible schema (model used,
response time, token counts, relevance label, timestamp). But
`db/transactions.py`'s `save_conversations()` has a function signature and
nothing else — it computes a timestamp and returns; it never executes an
`INSERT`. Nothing in the repo calls it. `app.py`'s only route is
`/question`; there is no `/feedback` endpoint, and `frontend.py` has no
rating UI. From first principles: **a monitoring feature that exists in the
schema but not in the code path is worth strictly less than no monitoring
feature at all** — it creates the appearance of infrastructure without
delivering any of the actual value, and it's dead code a future maintainer
has to understand and decide whether to finish or delete. The fix is small,
though: the schema and the RAG pipeline's returned dict already line up.
Writing the actual `INSERT` and adding one Flask route plus two Streamlit
buttons is a few hours, not a redesign.

**Containerization (0/2) is a similarly low-cost, high-value gap.** There is
no Dockerfile and no docker-compose anywhere in the repo. This is a sharper
critique than it might first appear, because this app's actual runtime
dependency surface is just Python packages and an `OPENAI_API_KEY` — no
Qdrant, no Postgres, no orchestrator. A single-stage Dockerfile
(`FROM python:3.12-slim`, `uv sync`, `CMD`) would very likely have been
achievable in under an hour and would have recovered 2 rubric points
essentially for free.

**RAG evaluation (1/2) — one configuration, evaluated once.** `rag.py`'s
`evaluate_relevance()` runs a single LLM-as-judge pass (NON_RELEVANT /
PARTLY_RELEVANT / RELEVANT) over `hybrid_search` answers with one fixed
prompt. There's no second prompt variant, no comparison across retrieval
methods at the *answer* level (only at the retrieval-metric level), and no
model comparison. The retrieval-evaluation rigor here (the field-combination
sweep, the keyword/vector/hybrid comparison) doesn't carry through to the
RAG-answer layer, and it's the one place this project's evaluation
discipline visibly drops rather than being simply absent from the start.

**Best practices (1/3) — hybrid implemented and evaluated; reranking and
query rewriting, neither.** Given the field-combination tuning already
shown for the vector index, a lightweight rerank pass (even a simple
cross-encoder) would likely have been within reach of the same skill level
already demonstrated elsewhere in this notebook.

**Problem description (1/2) — functional, not framed.** The README states
what the app does and how to run it in five lines, but never argues why a
WC2026-specific assistant beats asking a general chat model directly — a
couple of sentences on freshness (news moves faster than model training
cutoffs) or citation trust (a chat model can't point to which article said
what) would likely move this to a 2 without any code changes.

**A leftover scaffold file.** `main.py` is the unmodified `uv init` template
("Hello from wc2026-rag!"), never touched or removed. Trivial on its own,
but it's a small, free-to-fix polish signal.

## Insight for the author

The gaps here cluster almost entirely in the "was there time left" tier —
monitoring, containerization, deeper RAG eval, best-practice #2/#3 — while
the core technical work (the retrieval progression, the actual ingestion and
retrieval code, which I ran myself) is genuinely solid and, in the vector
field-combination sweep specifically, more careful than most projects
manage. If there's a next iteration, the fix priority by effort-to-reward
ratio is roughly: a one-file Dockerfile first (cheapest, 2 points), then
wiring the already-designed feedback path (schema and Flask route both
nearly exist already), then a second RAG-eval configuration, then
reranking. None of these require touching the parts that already work.
