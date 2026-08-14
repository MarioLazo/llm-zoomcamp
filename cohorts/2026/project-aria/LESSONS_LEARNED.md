# Building ARIA: What Broke, Why, and What I'd Tell the Next Person

A learning-in-public writeup for LLM Zoomcamp 2026 — not a polished
after-the-fact story, but the actual thought process, the gotchas, and the
honest evaluation results from building a compliance-RAG capstone
([ARIA](README.md)). If you're building something similar — a RAG app with
hybrid search, a Docker Compose stack, and more than one LLM provider — the
gotchas section below will probably save you an hour or two.

---

## Why this shape, not a simpler one

ARIA started as a generic "research assistant over interview transcripts"
idea, then got reframed as a **compliance/regulatory intelligence agent** —
same architecture, different framing and prompts. That reframe mattered more
than it sounds: "answer questions about transcripts" doesn't force any
design discipline, but "this is a compliance tool where an ungrounded answer
is an audit incident, not a UX bug" does. It's the reason citations aren't
optional decoration here — they're the actual product requirement — and
it's why I ended up adding citation-integrity and prompt-injection checks
that the base rubric doesn't ask for (see [Evaluation](#the-evaluation-results-including-the-ones-i-didnt-like)
below).

The retrieval design (hybrid dense+BM25 fused with RRF, then cross-encoder
rerank, then an LLM) is the standard-issue "good" RAG stack the course
teaches. I didn't second-guess that part going in. What I *did* second-guess
— and measured, not assumed — is whether it actually earns its complexity on
this specific, small corpus. Spoiler: partially. See below.

---

## The gotchas — the part actually worth sharing

Ten real bugs got fixed across this project, in two batches: four found in a
code-review pass before ever running it, and six found by actually running
it end-to-end. The second batch is the interesting one — every single one of
these was invisible to `python -c` / `python -m` testing and only showed up
when the real entrypoints (Docker Compose, the actual Streamlit UI, the
actual free-tier API key) got exercised for real.

### 1. Streamlit doesn't add your project root to `sys.path`

**Symptom:** `docker compose exec app python -c "from app.rag import RAG; ..."`
worked perfectly. `docker compose exec app python -m eval.llm_eval` worked
perfectly. The actual product — `streamlit run app/streamlit_app.py` —
crashed instantly with `ModuleNotFoundError: No module named 'app'`.

**Why:** `streamlit run <script>` adds the *script's own directory* to
`sys.path`, not the working directory the way a plain `python script.py`
invocation (or `-m`) does. So `app/streamlit_app.py` could see everything in
`app/`, but `from app import monitoring` — an absolute import reaching back
up to the package root — had nowhere to resolve from.

**Fix:** one line, `ENV PYTHONPATH=/project` in the Dockerfile.

**The generalizable lesson:** if your test suite only exercises your code
via `python -c`/`-m`/pytest, and your actual product entrypoint is something
else (Streamlit, a WSGI server, a Lambda handler), you have not tested your
product. You've tested that your code is importable in one specific way.
Open the real thing at least once before calling something done.

### 2. Self-hosted Qdrant's server-side BM25 "just works"... until it doesn't

**Symptom:** `qdrant_client.http.exceptions.UnexpectedResponse: 500 ... "Service
internal error: InferenceService is not initialized."` — on the very first
`ingest` call, using the documented pattern
(`models.Document(text=..., model="Qdrant/bm25")`) straight from Qdrant's
own BM25 docs.

**Why:** that pattern relies on server-side inference, which the docs
describe cleanly for Qdrant Cloud but don't spell out the self-hosted
configuration for. After chasing the actual Qdrant config docs and coming
up empty on a documented self-hosted flag, I stopped trying to make the
documented-for-Cloud path work and did the more robust thing instead.

**Fix:** compute the BM25 sparse vector **client-side** with `fastembed`
directly (already a dependency) instead of asking the server to do it —
`SparseTextEmbedding(model_name="Qdrant/bm25")`, batched for ingestion, one
call for queries. Zero server-side dependency, works identically self-hosted
or cloud.

**The generalizable lesson:** when a vendor's "just works" code sample
depends on an unstated server-side feature, and you can't find the config
flag to enable it in your deployment mode, don't burn more time — check if
there's a client-side equivalent. There often is, and it's usually more
portable anyway.

### 3. `pd.cut()` + `st.bar_chart()` is a silent trap

**Symptom:** two of six monitoring-dashboard charts crashed with
`SchemaValidationError` from Vega-Lite: `'(3295.075, 4825.567]' is an
invalid value`.

**Why:** `pd.cut(series, bins=10).value_counts()` produces a Series indexed
by pandas `Interval` objects. That's a perfectly normal pandas object — but
Vega-Lite (which `st.bar_chart` compiles to under the hood) has no schema
type for it, so the chart's spec fails validation the moment Streamlit tries
to serialize the index as axis labels.

**Fix:** `dist.index = dist.index.astype(str)` before charting. One line,
twice.

**The generalizable lesson:** `pd.cut()` output looks chart-ready (it's
already binned and sorted) and *is* chart-ready for matplotlib — but
anything that round-trips through a JSON-based spec (Vega-Lite, Plotly's JSON
mode, most JS charting libraries) needs primitive-typed axis labels, not
pandas' own interval type. This one's easy to miss because the DataFrame
looks completely normal when you `print()` it.

### 4. A version pin can silently make your own dependency uninstallable

**Symptom:** `pip install -r requirements.txt` failed immediately with a
`ResolutionImpossible` error — before any code even ran.

**Why:** `requirements.txt` pinned `onnxruntime==1.20.1`, but the also-pinned
`fastembed==0.4.2` declares its own internal constraint of
`onnxruntime<1.20.0`. Two of your own pins can conflict with each other even
when neither conflicts with anything external.

**Fix:** downgrade to `onnxruntime==1.19.2` (inside fastembed's supported
range).

**The generalizable lesson:** when you pin exact versions for
reproducibility (good practice!), you've taken on the job of keeping those
pins mutually compatible — pip won't do transitive-compatibility checking
for you until install time, and by then the error message names the
symptom, not always the fix.

### 5. "Free tier" rate limits aren't always what you'd guess

**Symptom:** `eval/llm_eval.py` — paced at roughly 1 call per 2-13 seconds,
which comfortably respects a *per-minute* limit — still failed partway
through with a 429.

**Why:** the actual constraint was `GenerateRequestsPerDayPerProjectPerModel-FreeTier`,
**limit 20, per day** — not the per-minute limit I'd designed pacing around.
An eval script making ~40-65 calls will exhaust a 20/day cap in one run, no
matter how well-paced each individual call is.

**Fix, short-term:** added retry-with-backoff to the shared LLM layer for
transient 429s, and switched providers temporarily to finish the eval pass.
**Fix, actual:** moved to a paid tier once real usage was confirmed, which
removed the daily ceiling entirely.

**The generalizable lesson:** "free tier" rate limits come in more than one
shape — per-minute, per-day, sometimes per-project-per-model specifically —
and pacing your calls to respect the one you assumed doesn't protect you
from the one you didn't check. Read the actual error message's
`quota_id`/`quota_metric` field; it usually tells you exactly which
dimension you hit.

### 6. My own eval tooling had a hidden single-provider assumption

**Symptom:** a citation-integrity checker reported Gemini "hallucinating"
citations in 4 of 10 answers — a real-looking, alarming number.

**Why:** Claude formats multi-source citations as separate brackets per
file (`[a.md][b.md]`); Gemini joins them in one bracket, comma-separated
(`[a.md, b.md]`). My regex captured the *entire bracket contents* as one
citation string, so Gemini's perfectly correct, differently-formatted
citation never matched any single retrieved filename — a formatting
mismatch masquerading as a grounding failure.

**Fix:** match filenames individually wherever they appear, rather than
anchoring on the whole bracket. Both providers came back at 0/10 once fixed.

**The generalizable lesson, and probably the one I'd lead with:** eval
tooling you build yourself needs to be validated against every system it's
meant to evaluate, not just the first one you happened to test it with. This
is exactly the failure mode this course's evaluation module warns about
generally (don't trust an eval number blindly) — I just hit the specific,
very concrete version of it: my *ground truth about what counts as a
citation* was itself silently overfit to one model's output style. A wrong
eval result is worse than no eval result, because it looks like evidence.

---

## The evaluation results, including the ones I didn't like

**Reranking didn't win on this eval set.** Plain hybrid search scored higher
MRR (0.920) than hybrid+rerank (0.883) on the 10-query ground truth set. I
could have quietly not mentioned this and just shipped hybrid+rerank with
the standard "best practices" justification. Instead: the honest read is
that with only 10 queries and every method already at a perfect Hit-Rate,
there's a ceiling effect and not much room for reranking to prove itself —
the gap is plausibly noise at this sample size, not evidence reranking is
wrong. I kept hybrid+rerank in production because it's the more principled
default and costs nothing extra, but I didn't hide the number that
complicates the story.

**Claude vs. Gemini, measured, not assumed.** Same eval suite, same 10
queries, run against both providers: statistically tied on quality (both
near-ceiling faithfulness/relevance, both 0/10 citation violations, both 3/3
resisted a set of prompt-injection probes), Gemini used ~24% fewer tokens
for identical work. That's the actual, measured basis for shipping Gemini
as the default — not "Gemini is usually cheaper" as received wisdom.

Full numbers, methodology, and the rubric-mapped writeup are in the
[README's Evaluation section](README.md#evaluation).

---

## What I'd tell someone starting this course today

- **Run the real entrypoint, not just your test harness**, before calling
  anything done — three of six live-run bugs were invisible to `python -c`
  testing and only surfaced by opening the actual UI in a browser.
- **When a vendor's docs describe a Cloud-only feature ambiguously for
  self-hosted, don't fight it — find the client-side equivalent.**
- **Check every rate-limit error's specific quota dimension** — "free tier"
  is not one number.
- **If you build your own eval tooling, test it against every system it
  judges, not just the one you happened to build it against first.** This
  is the single lesson I'd want someone to remember from this whole project.
- **Report the eval result you got, not the one that makes the best-practices
  checklist look cleanest.** A submission that shows real, sometimes
  inconvenient measurement is a stronger portfolio piece than one that only
  shows things working.

---

*Part of the [ARIA](README.md) capstone for
[LLM Zoomcamp 2026](https://github.com/DataTalksClub/llm-zoomcamp). See also
[`STEPS.md`](STEPS.md) for the full build log and [`PEER_REVIEW.md`](PEER_REVIEW.md)
if you're reviewing this project.*
