# Homework 4 — Evaluation (Answers)

**Cohort:** LLM Zoomcamp 2026
**Module:** 4 — Evaluation
**Submission form:** https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw4

Answers produced by running the evaluation pipeline locally with `gpt-5.4-mini`,
ONNX `all-MiniLM-L6-v2` embeddings, and 360 pre-generated ground truth questions
across 72 lesson pages (commit `8c1834d`).

| Q | Topic | Answer |
|---|-------|--------|
| 1 | Avg input tokens, first 3 lesson pages | **1400** (actual: ~1,354) |
| 2 | text_search — first result filename | **`01-agentic-rag/lessons/03-rag.md`** |
| 3 | vector_search — first result filename | **`01-agentic-rag/lessons/01-intro.md`** |
| 4 | text_search Hit Rate | **0.76** (actual: 0.7583) |
| 5 | vector_search MRR | **0.55** (actual: 0.5486) |
| 6 | Best k for hybrid_search MRR | **1** (MRR=0.6482 vs 0.6379 for k=50/100/200) |

---

## Question 1 — Generating questions for first 3 pages

**Answer: 1400**

Generated 5 questions per page for the first 3 lesson pages using `llm_structured`
with a `Questions` Pydantic model. Actual input tokens across the 3 calls:

```
01-agentic-rag/lessons/01-intro.md:        1,021 input tokens
01-agentic-rag/lessons/02-environment.md:  1,287 input tokens
01-agentic-rag/lessons/03-rag.md:          1,754 input tokens

Average: 1,354 → closest option: 1400
```

Input tokens vary with page length; the average lands firmly in the 1400 range.

---

## Question 2 — text_search first result

**Answer: `01-agentic-rag/lessons/03-rag.md`**

First ground truth question:
> "What exactly is a retrieval-augmented generation system, and why does it help
> with answers that the model wouldn't know on its own?"

Running `text_search` (minsearch `Index`, `content` as text field) returns
`01-agentic-rag/lessons/03-rag.md` as the top result. The keyword index matches
on "retrieval-augmented generation" terms found directly in the RAG lesson.

---

## Question 3 — vector_search first result

**Answer: `01-agentic-rag/lessons/01-intro.md`**

Same question, run through `vector_search` (minsearch `VectorSearch` + ONNX
`all-MiniLM-L6-v2` embeddings) returns `01-agentic-rag/lessons/01-intro.md` first.

The semantic embedding matches the *concept* of RAG-as-motivation discussed in
the intro lesson, rather than the exact keyword occurrence in lesson 03. This
illustrates the core difference: keyword search finds exact terms; vector search
finds conceptual meaning — and they don't always agree on what's most relevant.

---

## Question 4 — text_search Hit Rate

**Answer: 0.76**

Evaluated `text_search` across all 360 ground truth questions:

```
Hit Rate: 0.7583
MRR:      0.5943
```

Hit Rate = fraction of questions where the correct page appears anywhere in the
top-5 results. At 0.76, keyword search finds the right page about 3 out of 4
times — reasonable, but leaves room for improvement.

---

## Question 5 — vector_search MRR

**Answer: 0.55**

Evaluated `vector_search` across all 360 ground truth questions:

```
Hit Rate: 0.7250
MRR:      0.5486
```

MRR (Mean Reciprocal Rank) rewards finding the correct page near the top.
Vector search's MRR (0.55) is lower than text search's (0.59), meaning keyword
search tends to rank the correct page higher when it finds it. Vector search
compensates with semantic matching but loses precision on top-rank placement.

---

## Question 6 — best k for hybrid_search

**Answer: k=1**

Evaluated `hybrid_search` (RRF combining text + vector results) for k ∈ {1, 50, 100, 200}:

```
k=1:   MRR=0.6482  Hit Rate=0.8389  ← best
k=50:  MRR=0.6379  Hit Rate=0.8361
k=100: MRR=0.6379  Hit Rate=0.8361
k=50:  MRR=0.6379  Hit Rate=0.8361
```

Hybrid search beats either method alone on both metrics. `k=1` gives the best MRR
because a smaller `k` sharpens the gap between rank positions — being at the top
of a list counts for more. With `k=1`, documents ranked #1 in either search are
weighted much more heavily than those ranked #5, which better matches our goal
of finding the right page at the top.

---

## Evidence notes

- Model: `gpt-5.4-mini` for question generation
- Embeddings: `all-MiniLM-L6-v2` via ONNX runtime (identical vectors to sentence-transformers)
- Ground truth: 360 questions, 5 per page, 72 pages (commit `8c1834d`)
- Chunks: 295 (size=2000, step=1000)
- All metrics computed over the full 360-question dataset
