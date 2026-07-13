# Homework 2 — Vector Search (Answers)

**Cohort:** LLM Zoomcamp 2026
**Module:** 2 — Vector Search
**Submission form:** https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw2

Answers produced by running `hw2-vector-search.ipynb` / `hw2.py` locally
with the ONNX `all-MiniLM-L6-v2` embedder (`Embedder` in `embedder.py`)
against the pinned course commit `8c1834d` (72 lesson pages).

| Q | Topic | Answer |
|---|-------|--------|
| 1 | Query embedding, `v[0]` | **-0.02** (actual: -0.0206) |
| 2 | Cosine similarity to a specific page | **0.37** (actual: 0.3611) |
| 3 | Highest-scoring chunk, by hand | **`02-vector-search/lessons/07-sqlitesearch-vector.md`** |
| 4 | `VectorSearch` first result | **`04-evaluation/lessons/05-search-metrics.md`** |
| 5 | Vector-only result vs. text search | **`02-vector-search/lessons/08-pgvector.md`** |
| 6 | Hybrid search (RRF) first result | **`01-agentic-rag/lessons/13-function-calling.md`** |

---

## Question 1 — Embedding a query

**Answer: -0.02 (actual: -0.0206).**

```python
emb = Embedder()  # ONNX all-MiniLM-L6-v2, mean-pooled + normalized, 384-dim
v = emb.encode('How does approximate nearest neighbor search work?')
v[0]  # -0.0206
```

The ONNX runtime produces the same normalized vectors as
`sentence-transformers` would, without the PyTorch/CUDA dependency —
`v[0] = -0.0206` lands closest to the **-0.02** option.

---

## Question 2 — Cosine similarity

**Answer: 0.37 (actual: 0.3611).**

```python
page = next(d for d in documents if d['filename'] == '02-vector-search/lessons/07-sqlitesearch-vector.md')
page_vec = emb.encode(page['content'])
cos = float(page_vec.dot(v))  # vectors are normalized -> dot product == cosine similarity
# 0.3611
```

A moderate similarity: the query is about ANN search in general, and this
page covers vector search specifically with SQLite — related but not an
exact topical match, hence 0.36 rather than something closer to 1.0.

---

## Question 3 — Chunking and search by hand

**Answer: `02-vector-search/lessons/07-sqlitesearch-vector.md`.**

Chunked the 72 pages the same way as homework 1
(`chunk_documents(size=2000, step=1000)` → 295 chunks), embedded every
chunk with `encode_batch`, stacked the vectors into `X`, and scored by hand:

```python
scores = X.dot(v)
chunks[int(scores.argmax())]['filename']
# 02-vector-search/lessons/07-sqlitesearch-vector.md
```

The highest-scoring chunk comes from the same page as Q2 — chunking sharpens
the match further because the winning chunk is the specific paragraph
about ANN-style vector search, not the whole page's average.

---

## Question 4 — Vector search with minsearch

**Answer: `04-evaluation/lessons/05-search-metrics.md`.**

```python
vindex = VectorSearch(keyword_fields=[])
vindex.fit(X, chunks)
q = 'What metric do we use to evaluate a search engine?'
vindex.search(emb.encode(q), num_results=5)[0]['filename']
# 04-evaluation/lessons/05-search-metrics.md
```

Vector search matches the *concept* of "evaluating a search engine" — it
finds the metrics lesson in Module 4 even though the query doesn't mention
Hit Rate or MRR by name, because the embedding captures the semantic intent
of the question rather than requiring exact keyword overlap.

---

## Question 5 — Text search vs. vector search

**Answer: `02-vector-search/lessons/08-pgvector.md`.**

For the query "How do I store vectors in PostgreSQL?", comparing the top-5
results from `VectorSearch` against the top-5 from a keyword `Index` (both
over the same chunks):

```python
vector_files = [r['filename'] for r in vindex.search(emb.encode(q5), num_results=5)]
text_files = [r['filename'] for r in tindex.search(q5, num_results=5)]
[f for f in vector_files if f not in text_files]
# ['02-vector-search/lessons/08-pgvector.md']
```

`08-pgvector.md` is the pgvector lesson — it's semantically the *most*
relevant page, and vector search finds it, but its exact wording apparently
diverges enough from "store vectors in PostgreSQL" that keyword search's
top-5 misses it. A clean illustration of the two methods' different failure
modes: vector search misses exact terms, keyword search misses paraphrases.

---

## Question 6 — Hybrid search

**Answer: `01-agentic-rag/lessons/13-function-calling.md`.**

Fused the vector and text top-5 result lists for "How do I give the model
access to tools?" with Reciprocal Rank Fusion (`k=60`):

```python
def rrf(result_lists, k=60, num_results=5):
    scores, docs = {}, {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            key = (doc['filename'], doc['start'])
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
            docs[key] = doc
    ranked = sorted(scores, key=scores.get, reverse=True)
    return [docs[key] for key in ranked[:num_results]]

rrf([vector_results, text_results])[0]['filename']
# 01-agentic-rag/lessons/13-function-calling.md
```

This page — the function-calling / tool-use lesson — isn't necessarily
first in *either* search on its own, but it ranks well in both, so RRF's
summed reciprocal-rank score pushes it to the top after fusion. This is the
core value of hybrid search: rewarding documents both methods agree on,
not just whichever method happens to score highest on raw similarity.

---

## Evidence notes

- Embedder: ONNX `Xenova/all-MiniLM-L6-v2` via `onnxruntime` (`embedder.py`),
  384-dim, mean-pooled, L2-normalized — identical vectors to
  `sentence-transformers`, without the PyTorch/CUDA dependency.
- Data: 72 lesson pages, pinned commit `8c1834d`; 295 chunks
  (`chunk_documents(size=2000, step=1000)`), same parameters as homework 1.
- Search: `minsearch.VectorSearch` (vector), `minsearch.Index` (keyword),
  RRF with `k=60` (hybrid) — all over the same chunk set.
- Exact numeric values (Q1, Q2) recorded directly from the notebook run;
  Q3–Q6 are filename matches, stable across runs since the embedder and
  index are deterministic.
