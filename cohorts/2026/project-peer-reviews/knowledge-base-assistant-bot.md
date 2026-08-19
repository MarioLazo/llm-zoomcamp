# Peer review — `knowledge-base-assistant-bot` (Xue-Zhiming-Bruce)

Assigned peer review, LLM Zoomcamp 2026, Project Attempt 2. Repo:
[Xue-Zhiming-Bruce/knowledge-base-assistant-bot](https://github.com/Xue-Zhiming-Bruce/knowledge-base-assistant-bot),
commit `8015a92`. Rubric scores were submitted on the course platform; this
document is the deeper analysis behind those scores — design decisions,
what's actually strong, what's actually weak, and what I'm borrowing from it
for [ARIA](../project-aria/README.md).

Verification method: cloned the repo at the pinned commit, ran
`docker compose config --quiet` (passes), counted the Grafana dashboard's
panels directly from its JSON (7, matching the README's claim), and read the
domain/application/infrastructure source for the best-practices claims
(hybrid search, reranking, agentic query decomposition) rather than trusting
the README's rubric-mapping table at face value.

## Start here: plain-English summary

### What it is

A "read it later, but you can actually search it" tool. When you save an
article — a newsletter post, a blog essay — this app pulls it into your own
private notes folder and remembers it. Later, you can ask it a question in
plain English ("what did that essay say about hiring senior engineers?")
through a Telegram chat bot, and it answers using only what you've actually
saved, telling you exactly which article the answer came from.

### The report card

Full marks: **21 out of 21** on the course's grading checklist.

### What we found when we double-checked it

This held up better under scrutiny than almost anything else reviewed this
cycle. Three things stood out, explained without jargon:

1. **It never trusts its own search index blindly.** The notes themselves
   are the real, permanent record; the search database built from them is
   treated as disposable — it can always be rebuilt from scratch and you'd
   know for certain it matches what's actually saved, rather than quietly
   serving stale or half-updated results.
2. **Before comparing 5 different search methods, they wrote down the
   rules for picking a winner *before* running the test** — not after
   seeing which one looked best. That matters because it's much harder to
   unconsciously talk yourself into your preferred answer when the rule was
   locked in beforehand.
3. **When something hadn't actually been checked yet** (whether their AI
   grader's scores agree with a real human's judgment), **they said so
   plainly** instead of making up a number or just not mentioning it.

The two real weaknesses: every test in the project only used one AI
company's models (OpenAI) — so there's no evidence the same conclusions
would hold with a different provider. And roughly a third of the app's
advertised ability (saving posts from X/Twitter) needs a paid subscription
service, so most reviewers can't actually test that part for free.

### Bottom line

Genuinely one of the best-engineered projects in this review cycle — the
checklist score and the harder "does it actually hold up when you check"
test agree with each other, which isn't always true.

---

## Detailed rubric score, with evidence

| # | Criterion | Score | Evidence — what I actually checked |
|---|---|---|---|
| 1 | Retrieval evaluation | 2/2 | 5 retrieval strategies benchmarked with real numbers in the README's evaluation table; a written selection policy (`docs/operations/retrieval-selection-policy.md`) determines the winner mechanically |
| 2 | RAG evaluation | 2/2 | 2 answer-prompt versions (`grounded-answer-v1` vs `v2`) compared on real metrics; v2 wins on every reported metric and is the configured production default |
| 3 | Interface | 2/2 | Telegram bot (`application/bot.py`) plus a non-Telegram CLI demo |
| 4 | Ingestion pipeline | 2/2 | Async worker (`application/worker.py`) is the automated path; an optional Prefect flow also exists |
| 5 | Monitoring | 2/2 | Durable feedback collection to Postgres, plus a Grafana dashboard — I parsed `config/grafana/dashboards/knowledge-assistant.json` directly and counted 7 panels, matching the README's claim rather than trusting it |
| 6 | Containerization | 2/2 | Everything defined in `compose.yaml` (app, worker, postgres, admin tools) — I ran `docker compose config --quiet` myself and it validated cleanly |
| 7 | Problem description | 2/2 | README's "Who this is for" / "why generic ChatGPT isn't enough" section states the problem clearly and specifically |
| 8 | RAG flow | 2/2 | Real knowledge base (PostgreSQL + pgvector projection) feeding a real LLM call, not a lookup table |
| 9 | Reproducibility | 2/2 | `uv.lock` pins all dependencies; both eval datasets are committed; `answer-human-labels.jsonl` is genuinely empty (0 bytes, checked directly) with the README honestly stating calibration is `not_run` rather than inventing a number |
| 10 | Best practices | 3/3 | Hybrid search, a deterministic diversity reranker, and bounded agentic query decomposition — I read the actual source (`domain/retrieval.py`, `infrastructure/openai/planning.py`) to confirm all three exist in code, not just in the README's claims |
| **Total** | | **21/21** | No bonus claimed (no cloud deployment) |

---

## The detailed version

Everything above is the plain-English summary and the scored evidence.
Everything below is the full narrative review — design decisions, what's
genuinely strong, what's genuinely weak, and what I'm taking from this
project for my own.

---

## What it is

A personal knowledge engine: saves Substack/Medium/X Article essays as
canonical Markdown into an Obsidian vault, indexes them into a rebuildable
PostgreSQL projection (dense + full-text), and answers grounded, cited
questions through a Telegram bot or a CLI demo. Five selectable retrieval
strategies; two answer-prompt versions; a 7-panel Grafana dashboard fed by
OpenTelemetry.

## Design decisions — the interesting ones

**A modular-monolith with ports/adapters, documented via 12 numbered ADRs.**
`docs/architecture/decisions/` walks from "knowledge engine boundary"
through "versioned derived projections" to "containers as runtime boundary,"
each with its own file. This is unusually disciplined engineering process
for a single-user personal tool. The interesting first-principles question
is whether that discipline is earning its complexity here, or whether it's
mostly serving as a skill demonstration for the course/portfolio audience.
My read: it's earning it, for one specific reason — **ADR-0005
(versioned derived projections)** isn't decorative. The system treats
PostgreSQL as a *disposable, rebuildable projection* of the vault's Markdown
(the actual source of truth), activated atomically via
`projection-rebuild` + `projection-activate`. That single decision is what
makes "evaluation on `projection bd3a3ba7-…`" a meaningful, reproducible
claim rather than "evaluation on whatever the database happened to contain
that day" — and it's also what prevents the failure mode of a half-rebuilt
index silently serving stale or inconsistent results. For a project whose
whole pitch is "grounded, cited answers," having a crisp, versioned
boundary around *what the ground actually was at eval time* is close to a
prerequisite, not an indulgence. The ports/adapters layering around it is
lighter-weight justification (it mostly buys testability and provider
swap-ability, both nice-to-haves for a personal tool), but it's not fighting
the rest of the design either.

**The "no fabricated numbers" discipline, applied consistently.**
`answer-human-labels.jsonl` is genuinely empty (I checked — 0 bytes), and
the README states plainly that judge-vs-human calibration is `not_run`
rather than presenting judge scores as validated ground truth. This is the
same instinct worth naming across this whole review cycle — a project
reporting the gap in its own evidence rather than quietly not mentioning
it.

**A pre-registered retrieval-selection policy, decided before the numbers
came in.** `docs/operations/retrieval-selection-policy.md` states the
promotion criteria for changing the production default *before* running the
comparison, then the README applies it mechanically: `vector-only-v1` wins
on latency/cost/complexity but is disqualified because it regresses the
`exact_lookup` slice beyond a pre-declared tolerance (0.01 MRR), so
`weighted-hybrid-v1` stays the default even though it's not the single
best-scoring strategy on every metric. This is the single practice from
this project I'd most want to import into my own work: a written policy
decided in advance is structurally harder to unconsciously bend toward a
preferred conclusion, even when the person applying it is being honest — it
removes the judgment call from the moment when the incentive to rationalize
is strongest.

## Weaknesses — genuine ones, not rubric nitpicks

**Single-provider evaluation.** Every eval — retrieval and RAG both — runs
against OpenAI only (`text-embedding-3-small`, and whatever generation model
`grounded-answer-v2` targets). The retrieval-selection policy is careful
about *strategy* choice but has no visibility into whether the same
strategy ranking would hold with a different embedding model, and the
prompt-version comparison (v1 vs v2) never asks whether provider choice
interacts with prompt choice.

**X Article sourcing depends on a paid, closed provider (Tempo/Xquik) that
the committed sample dataset deliberately avoids.** This is disclosed
plainly in the README, and the workaround (ship a Substack-only sample
corpus so reviewers can reproduce for free) is the right call — but it does
mean roughly a third of the system's stated capability (X Article ingestion)
is essentially unverifiable by a reviewer who isn't willing to spend real
money, and is coupled to a third-party service's continued existence and
pricing in a way the other two source types aren't.

**The rubric-mapping table doubles the README's own effort.** Minor, but
real: the README is already so thoroughly self-documenting (an
"Evaluation" section with real tables, a "Limitations" section, a
"Reproducibility" section) that the closing rubric-mapping table mostly
repeats pointers the reader has already seen.

## Insight for the author

The strongest thing about this submission isn't any single rubric line —
several capstones this cohort also hit 2/2 across the board. It's that the
engineering discipline (versioned projections, a written selection policy,
an honest `not_run` status) generalizes past this specific project. Those
are practices, not one-off decisions, and they'd transfer directly to a
production system with real stakes. The retrieval evaluation being
single-provider is the one place where the same rigor applied to *strategy*
selection hasn't yet been applied to *provider* selection — that's the
natural next axis to add, not a criticism of what's here.

## What I'm taking from this for ARIA

Expand a small ground-truth set in response to a diagnosed ceiling effect
(this project actually did it — 8 → 25 questions), and write the
rerank/no-rerank decision criteria down *before* looking at the numbers
next time, the way this project's selection policy does.
