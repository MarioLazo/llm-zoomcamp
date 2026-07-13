# Personal Learning Wiki — Module 4: Evaluation

**Cohort:** LLM Zoomcamp 2026 · **Module:** 4 — Evaluation
**Stack:** `gpt-5.4-mini` + ONNX `all-MiniLM-L6-v2` + minsearch + pandas

---

## TL;DR

- **Stop guessing, start measuring.** Intuition about which search method is "better" is unreliable — Hit Rate and MRR give you numbers to compare.
- **Ground truth is generated, not hand-labeled.** Use an LLM to write questions from each document; label each question with its source. This is cheap, fast, and scalable.
- **Keyword and vector search find different things.** For the same query, they return different top results. Neither is always right — that's precisely why you measure.
- **Hybrid search (RRF) reliably outperforms either method alone.** It combines ranked lists without caring about raw scores, which live on different scales.
- **k=1 in RRF sharpens ranking.** Smaller k means being first in a list matters much more. Tune k to match how much your use case rewards precision at the top.

---

## 1. Ground truth generation

To evaluate search, you need questions where you know the correct answer.
Building this dataset manually is expensive. The scalable alternative:
**use an LLM to generate questions from each document**.

```python
data_gen_instructions = """
You emulate a student who is taking our LLM course.
Given one lesson page, formulate 5 questions this student might ask
that are answered by that page.
Use as few words as possible from the page — real users don't phrase
questions the way the source material does.
"""
```

Each question is labeled with the `filename` of the page it came from.
This gives you a **ground truth dataset**: for each question, the correct
answer is the page that generated it.

**Key design choice:** ask the model to use *different wording* from the page.
If the questions copy the page's phrasing, keyword search wins trivially on
exact matches — not because it's better, but because the evaluation is too easy.

Input tokens scale with page length (~1,000–1,800 per page). At 72 pages × 5
questions each = 360 ground truth questions, cost is negligible.

---

## 2. Retrieval metrics: Hit Rate and MRR

Given a search function and a ground truth question, compute a relevance list:
`[1, 0, 0, 0, 0]` means the correct page was the first result; `[0, 0, 1, 0, 0]`
means it was third; `[0, 0, 0, 0, 0]` means it wasn't found at all.

**Hit Rate** — does the correct page appear anywhere in the top-5?

```
Hit Rate = (# questions with at least one hit) / (total questions)
```

Answers: "How often does search *find* the right page?"

**MRR (Mean Reciprocal Rank)** — how high in the list is the correct page?

```
MRR = mean of (1 / rank) for each question where the page was found
```

A hit at rank 1 → score 1.0. At rank 2 → 0.5. At rank 5 → 0.2. Not found → 0.

Answers: "When search finds the right page, how close to the top is it?"

MRR is the harder metric: a method can have decent Hit Rate but low MRR if it
buries the right answer at rank 4 or 5 every time.

---

## 3. Keyword vs vector vs hybrid — results

| Method | Hit Rate | MRR |
|--------|----------|-----|
| text_search (minsearch) | 0.758 | 0.594 |
| vector_search (all-MiniLM-L6-v2) | 0.725 | 0.549 |
| hybrid_search RRF k=1 | **0.839** | **0.648** |

**Key observations:**

- Keyword search edges out vector search on MRR — it's more precise when it
  finds a match, because the questions were generated to use *different* wording,
  but the lesson content still contains the original terms.
- Vector search has lower MRR but finds pages through semantic similarity —
  it surfaces the intro page for a question about RAG concepts, while keyword
  search goes to the RAG-specific lesson.
- Hybrid wins on both metrics, consistently. Combining ranked lists is almost
  always better than picking one method.

---

## 4. Reciprocal Rank Fusion (RRF)

RRF merges multiple ranked lists into one. It ignores raw scores (which are on
different, incomparable scales) and uses only rank positions:

```
RRF(doc) = Σ  1 / (k + rank(doc))
           lists
```

A document that appears at rank 1 in both searches gets a high combined score.
One that only appears in one list gets a lower score. The constant `k` controls
how much top positions matter relative to lower positions.

**Tuning k:**

| k | Effect |
|---|--------|
| Small (k=1) | Top-ranked documents dominate; being first matters a lot |
| Large (k=200) | Positions matter less; appearing in both lists matters more |
| k=60 | RRF paper default — a sensible starting point |

In this dataset, `k=1` gave the best MRR (0.648 vs 0.638 for k≥50). The
questions are specific enough that the right page tends to rank first when it's
found — so sharpening that top position improves MRR.

The rule: **lower k when precision at the top matters; higher k when you want
to reward documents that consistently appear across many lists.**

---

## 5. SA Connection — evaluation in enterprise AI delivery

How this shows up when architecting AI for enterprise customers:

- **Evaluation is the credibility story.** "Our RAG is good" is a claim.
  "Our RAG has 0.84 Hit Rate on 360 ground truth questions from production data"
  is evidence. Enterprises buying AI systems want to see the latter before
  deploying.
- **Ground truth generation scales the evaluation.** Manual labeling is
  expensive and slow. LLM-generated ground truth from existing documents is
  cheap, reproducible, and can be regenerated when the knowledge base changes.
  This is the pattern to recommend when customers ask "how do we know it works?"
- **Metrics are communication tools.** Hit Rate is easy to explain to
  stakeholders ("it finds the right document 84% of the time"). MRR is for
  engineers who care about ranking. Have both ready.
- **Hybrid search is the safe default.** In practice, recommending pure keyword
  or pure vector search to a customer is harder to justify than hybrid. The
  numbers make that case automatically.
- **The evaluation framework is reusable.** Once `evaluate(ground_truth, search_fn)`
  exists, any change to search — different embedding model, different k, different
  chunking — gets a number immediately. This is how you de-risk search changes in
  production.

---

## 6. Certification relevance — Anthropic Claude Architect

Flags mapping this module's topics to Claude Architect-style competencies:

- 🟢 **RAG evaluation** — measuring retrieval quality with standardized metrics;
  ground truth generation patterns. *(High relevance — core RAG competency.)*
- 🟢 **Embedding models and vector search** — how dense retrieval works; when it
  wins or loses vs keyword search. *(High relevance.)*
- 🟡 **Hybrid search** — RRF and rank fusion; when to combine methods.
  *(Medium — architectural pattern literacy.)*
- 🟡 **Structured output** — using Pydantic models with LLM responses for
  reliable data extraction. *(Medium — reliable in production.)*
- ⚪ **minsearch specifics** — the library is a teaching tool; in production
  you'd use Elasticsearch, OpenSearch, Pinecone, or similar. The *patterns*
  (text fields, vector fields, filter dicts, boost dicts) transfer directly.

---

## 7. Quick reference

```python
# Ground truth generation
from evaluation_utils import llm_structured
from pydantic import BaseModel

class Questions(BaseModel):
    questions: list[str]

result, usage = llm_structured(client, instructions, user_prompt, Questions)

# Chunking
from gitsource import chunk_documents
chunks = chunk_documents(documents, size=2000, step=1000)  # 295 chunks

# Metrics
hit_rate  = sum(1 for r in relevance if 1 in r) / len(relevance)
mrr_score = sum(1/(r.index(1)+1) for r in relevance if 1 in r) / len(relevance)

# RRF
def rrf(result_lists, k=60, num_results=5):
    scores, docs = {}, {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            key = (doc["filename"], doc["start"])
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
            docs[key] = doc
    return [docs[k] for k in sorted(scores, key=scores.get, reverse=True)[:num_results]]
```

---

*See [`homework4_answers.md`](./homework4_answers.md) for the graded Q&A with observed values.*
