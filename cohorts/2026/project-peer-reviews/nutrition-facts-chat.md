# Peer review — `nutrition-facts-chat` / `project2` (hadiwehbi)

Assigned peer review, LLM Zoomcamp 2026, Project Attempt 2. Repo:
[hadiwehbi/llm-zoomcamp-submissions](https://github.com/hadiwehbi/llm-zoomcamp-submissions/tree/main/project2),
commit `a468df4`. Third of three assigned reviews this cycle — see
[`knowledge-base-assistant-bot.md`](knowledge-base-assistant-bot.md) and
[`wc2026-rag.md`](wc2026-rag.md) for the other two, and
[ARIA's own README](../project-aria/README.md) for how all three fed back
into my own capstone.

Verification method: cloned the repo at the pinned commit, validated
`docker compose config --quiet` (passes, 7 services), confirmed the
committed dataset (2,500 USDA foods) and ground truth (160 questions) are
real and sized as claimed, confirmed the Grafana dashboard has exactly 7
panels by parsing its JSON, and — the part that changed my score — read
`eval/llm_eval_extractive.py` and `eval/llm_eval.py` line by line rather
than trusting the README's "LLM evaluation" table at face value.

## Start here: plain-English summary

### What it is

A chatbot that answers nutrition questions — "how much protein is in
Pacific herring?" — using real U.S. government (USDA) nutrition data for
2,500 foods. The standout feature: it runs entirely on your own computer,
completely free, no paid subscription to any AI company needed anywhere.
That's different from every other project reviewed this cycle (including my
own), which all require a metered or paid AI account just to run.

### The report card

**20 out of 21** — the strongest "you can actually run this for free" of
anything reviewed, and it also has the biggest, most trustworthy test set:
160 practice questions, versus 10 for my own project.

### What we found, the good part

- The feedback buttons (👍/👎) genuinely save to a database, and the
  background job that loads the nutrition data genuinely runs on its own —
  both checked directly in the code, not assumed.
- 160 test questions is enough that the results are trustworthy rather than
  a fluke — a 10-question test (like my own project's) is small enough that
  a close call between two options can't really be trusted either way, and
  this project simply doesn't have that problem.

### The one real problem, explained simply

The write-up shows a table comparing "two ways of answering a question" and
declares a winner. Tracing through the actual code: **neither of the two
compared answers was actually written by the AI.** One is just a chunk of
raw article text copy-pasted in. The other is a fill-in-the-blank template
that cheats by looking up the correct number directly from the answer key —
not from anything the AI said. So the table looks like it's comparing two
AI-generated answers and picking the better one; it's actually comparing
two shortcuts that never asked the AI anything.

To be fair: this is honestly disclosed in a code comment ("this is a
proxy... run this other script for the real version") — it's just not
mentioned in the main write-up most people would actually read. And the
real version of this test — the one that actually asks the AI — was already
built. It was just never run, and its results were never published.

### Bottom line

About as close to a perfect project as this review cycle produced. One real
gap, and it's a cheap one to close: run the script that's already sitting
there, finished, unused.

---

## Detailed rubric score, with evidence

| # | Criterion | Score | Evidence — what I actually checked |
|---|---|---|---|
| 1 | Retrieval evaluation | 2/2 | 4 search modes compared (keyword/vector/hybrid/hybrid+rerank) across 160 real test questions in `eval/results/retrieval.json`; best (hybrid+rerank) is the one actually used by the app |
| 2 | RAG evaluation | 1/2 | Traced `eval/llm_eval_extractive.py` line by line: neither compared "answer" actually calls the AI model — one slices raw text, the other formats a template using the *answer key's own data*. The real AI-judged version (`eval/llm_eval.py`) exists, correctly built, but was never run — its own output file says so |
| 3 | Interface | 2/2 | Streamlit chat UI |
| 4 | Ingestion | 2/2 | Real background job (`ingest/flow.py`) with an automatic "download the data if it's missing" step — read directly, not assumed |
| 5 | Monitoring | 2/2 | Checked this precisely because I'd just found the opposite problem in a different project (`wc2026_rag`): here, the 👍/👎 buttons really do call a function that does a real database `INSERT`, and I parsed the dashboard's file directly and counted exactly 7 charts |
| 6 | Containerization | 2/2 | Ran `docker compose config --quiet` myself — validates cleanly, 7 services defined including a dedicated evaluation-runner service |
| 7 | Problem description | 2/2 | README states a specific, checkable behavior claim ("if the food isn't in the database, it should say so instead of making up a number") — testable, not just descriptive |
| 8 | RAG flow | 2/2 | Real knowledge base (the USDA food data) feeding a real AI-generated answer |
| 9 | Reproducibility | 2/2 | Confirmed the entire stack (search AI model + answering AI model) runs locally with zero paid account needed anywhere — the strongest reproducibility posture of the projects I looked at this cycle |
| 10 | Best practices | 3/3 | Hybrid search (measurably helps, shown in the 160-question eval), a lighter-weight but real reranking step (also shown to help), and query rewriting — and unlike my own project, this one actually varies the rewrite on/off in its evaluation rather than shipping it unverified |
| **Total** | | **20/21** | No bonus claimed |

---

## The detailed version

Everything above is the plain-English summary and the scored evidence.
Everything below is the full narrative review, including the detailed
walk-through of the RAG-evaluation finding.

---

## What it is

A RAG assistant answering nutrition questions ("how much protein is in
Pacific herring?") over a 2,500-item USDA SR Legacy food subset. Fully
local stack: Qdrant (dense + BM25), Ollama (`llama3.2:1b`) for generation
and query rewrite, FastEmbed/ONNX for embeddings, Prefect for ingestion,
Postgres + Grafana for monitoring — no paid API key required for any part
of it.

## What's genuinely strong, verified against code

**Reproducibility is the best of the projects I've now looked at this
cycle.** Every other project — including my own — requires a metered or
paid API key (OpenAI, Gemini, or Claude) to actually run the answering
layer. This one doesn't: Ollama serves a 1B-parameter local model, FastEmbed
does embeddings via ONNX (no PyTorch, no GPU, no external inference API),
and the README states the resource cost up front (~8GB RAM, Docker Desktop)
instead of a per-token dollar cost. A reviewer with no API budget at all can
run this project end-to-end for free.

**160 ground-truth questions is the largest, most statistically stable eval
set of the projects reviewed.** A 10-query test with every method already
at ceiling Hit-Rate is genuinely too small to distinguish two close options
with any confidence. This project simply started at 160, which is enough
that hit-rate isn't pinned at a ceiling (0.850/0.669/0.850/0.875 across the
four modes — real separation, not noise) and the reranking lift (MRR@5
0.673→0.683, hit_rate@5 0.850→0.875) reads as a genuine, if modest, signal
rather than something indistinguishable from sampling noise.

**Query rewriting is actually varied in the evaluation, not just shipped
unverified.** `nutrition_rag/rewrite.py` calls Ollama to rewrite the user's
question into a search-optimized query, and the LLM-eval table explicitly
varies `query_rewrite: true/false` between the two compared rows (`generic`
= no rewrite, `specialist` = rewrite on) — meaning query rewriting is at
least nominally part of what the fact_match comparison measures. (The next
section complicates how much weight that comparison can actually bear — but
the instinct to vary it at all is the right one.)

**Feedback and Prefect ingestion are both real, checked against a specific
failure mode found in a different peer project.** Having just found
`wc2026_rag`'s feedback schema wired to nothing, I checked this project the
same way: `app/ui.py`'s thumbs buttons call `log_feedback()`, which executes
a real `INSERT INTO feedback` (`nutrition_rag/db.py`), and `ingest/flow.py`
is a genuine Prefect `@flow` with three `@task`s (`ensure_corpus`,
`load_corpus`, `index_foods`), including an idempotent download-if-missing
guard rather than a manual one-off script. Both hold up.

## The real finding — the "LLM evaluation" doesn't call an LLM

This is worth walking through carefully because it's not obvious from the
README, and it changes the RAG-evaluation score from what the README's own
rubric-mapping table claims (2 points) to 1.

The README's "LLM evaluation" section presents this table:

| Approach | fact_match |
|---|---:|
| generic prompt (dump retrieved text) | 0.631 |
| specialist + query rewrite (used in app) | 0.869 |

This reads as: two prompting strategies were run through the model and
scored on whether the answer contains the right number. **Neither one
actually was.** Reading `eval/llm_eval_extractive.py`:

- `generic_answer()` returns the first 400 characters of the top-2
  retrieved documents' raw text — string slicing, no model call.
- `specialist_answer()` looks up the ground-truth `document_id` directly
  among the retrieved hits (falling back to the top hit if the correct one
  wasn't retrieved), pulls the nutrient value out of that document's
  structured `nutrients` dict, and formats it into a hand-written template
  string (`f"{name} contains {amount} {unit} of {nutrient}..."`) — again,
  no model call.

Both "approaches" are deterministic Python functions over retrieved
documents. `contains_value()` then checks whether the expected number
appears in that templated string. What this actually measures is closer to
**"if the correct document was retrieved, does a template extract the right
field from it"** — which is a retrieval-groundedness check wearing an
LLM-evaluation costume, not a comparison of two prompts' output quality.
The file's own docstring says as much, honestly: *"Offline LLM-output
proxy... The live Ollama evaluation is `eval/llm_eval.py`."* That script —
a real Ollama-as-judge on relevance/groundedness/completeness — exists,
is well-written, and was never run: `eval/results/llm.json`'s own `note`
field says "run `python eval/llm_eval.py` for full Ollama-as-judge scores."

So there are three honest, correctly-labeled facts here, and one
README-level presentation gap: the proxy script's docstring discloses
itself as a proxy; `eval/results/llm.json`'s `method` field discloses
"extractive proxy... run eval/llm_eval.py for Ollama-as-judge"; but the
README — which explicitly says it's "for reviewers who did not take the
course" — presents the 0.631/0.869 numbers under a plain "LLM evaluation"
heading with no caveat that the model was never actually invoked to produce
either answer. A reviewer working from the README alone, which is the
primary artifact most reviewers will actually read, would reasonably
believe two prompt variants were LLM-generated and judged.

This isn't a case of hidden or fabricated numbers — everything computed is
real and honestly labeled at the source. It's a case of a genuinely useful
retrieval-groundedness proxy being presented, one layer up, as if it were
the answer-quality evaluation the rubric is asking for. Score-wise: real
evaluation work exists and a decision was made and shipped from it, so this
isn't a 0 — but the actual generation step this project's rubric-mapping
table claims 2 points for ("LLM evaluation... 2 prompt variants") was never
run and its output was never measured, which is what "1/2: only one RAG
approach evaluated" is for. Running `eval/llm_eval.py` once — the script
already exists, correctly built, unused — would close this gap directly and
should push it back to 2/2.

## A genuine, if secondary, design insight

Setting the presentation gap aside, there's a real methodological point
worth crediting: for a domain where the correct answer is an objectively
checkable number (a nutrient value per 100g), a deterministic extractive
metric is arguably a *more* trustworthy signal than an LLM-as-judge's
subjective 1-5 relevance score would be — it sidesteps a whole class of
eval-tooling-trust problems other projects (including my own) had to reason
about explicitly. The flaw here isn't the choice of a deterministic metric
over an LLM judge — that's a defensible, arguably superior choice for this
specific domain. The flaw is narrower: `specialist_answer()`'s template
looks up the correct value directly from structured data associated with
the *ground-truth* document, rather than testing whether the LLM, given
retrieved context, actually states that value correctly and comprehensibly
in its own generated language — which is the part of "RAG evaluation" that's
actually about the L in RAG. The right fix keeps the domain-appropriate
extractive metric (`contains_value` regex matching against a known numeric
ground truth is a sound idea) but applies it to **real Ollama-generated
answers** (`eval/llm_eval.py` already does this) rather than to a
hand-written template standing in for one.

## Other observations

**The reranker is a heuristic blend, not a learned model — a deliberate and
reasonable tradeoff given the project's stated goal.** `rerank()` combines
normalized dense score (45%), query-document token overlap (35%), and
query-name token overlap (20%) — no cross-encoder. Given the project
explicitly optimizes for "a small model so reviewers can run it" on modest
hardware, skipping a second model-inference pass for reranking in favor of a
cheap heuristic is consistent with that goal, and the eval shows it earning
its keep (a real, if modest, MRR/hit-rate lift over hybrid alone) rather
than being included on faith.

**Problem description is concrete and testable, not just descriptive.** The
README's example-question table states expected behavior precisely enough
that a reviewer can check pass/fail without running an eval script ("If the
food is not in the 2,500-item subset, the specialist prompt should say it
is not in the knowledge base instead of inventing numbers") — a falsifiable
claim about the system's behavior, which is a stronger "problem description"
than a paragraph of prose alone would be.

## Insight for the author

This project's engineering is solid across ingestion, retrieval, monitoring,
and containerization, and its reproducibility posture (zero paid API
dependency) is the best of the cycle. The one gap worth fixing is narrow and
cheap relative to the rest of the project: run the already-built
`eval/llm_eval.py` once against the real Ollama answering path, commit its
output alongside (not instead of) the extractive proxy, and adjust the
README's "LLM evaluation" section to describe the two metrics as what they
actually are — a fast, no-Ollama-required retrieval-groundedness proxy used
for quick iteration, and a slower, real generation-quality judge used for
the actual submitted claim. Both numbers are useful; conflating them under
one heading is the only thing costing a rubric point here.
