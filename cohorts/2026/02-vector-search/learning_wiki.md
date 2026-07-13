# Personal Learning Wiki — Module 2: Vector Search

**Cohort:** LLM Zoomcamp 2026 · **Module:** 2 — Vector Search
**Stack:** ONNX `all-MiniLM-L6-v2` (via `onnxruntime`) + minsearch + numpy

---

## TL;DR

- **Embeddings turn text into vectors; similarity becomes geometry.**
  Once text is a normalized vector, "how similar are these two passages"
  is just a dot product.
- **ONNX gets you the same vectors without the PyTorch/CUDA weight.** A
  lightweight runtime + tokenizer reproduces `sentence-transformers`
  output almost exactly, at a fraction of the install size.
- **Vector search finds meaning; keyword search finds words.** Same query,
  different top results — neither approach is strictly better, they fail
  differently.
- **Hybrid search (RRF) rewards agreement, not just top scores.** Fusing
  ranked lists by position (not raw score) surfaces documents both methods
  independently rate highly.
- **This module deliberately stops before evaluation.** Comparing search
  methods on a handful of manual queries is anecdote, not evidence — Module
  4 turns "which is best" into an actual measured answer.

---

## 1. Embeddings without the heavy stack

The module's key infrastructure lesson: you don't need
`sentence-transformers` (PyTorch + CUDA) to get transformer embeddings. An
ONNX export of the same model, run through `onnxruntime` + a `tokenizers`
tokenizer, produces **identical vectors** at ~30× smaller install size —
light enough to run in a basic Codespace.

```python
class Embedder:
    def __init__(self, path="models/Xenova/all-MiniLM-L6-v2"):
        self.tokenizer = Tokenizer.from_file(str(path / "tokenizer.json"))
        self.session = ort.InferenceSession(str(path / "model.onnx"))

    def encode_batch(self, texts, normalize=True):
        encoded = self.tokenizer.encode_batch(texts)
        hidden = self.session.run(None, feed)[0]          # token embeddings
        pooled = (hidden * mask).sum(1) / mask.sum(1)      # mean pooling
        return pooled / np.linalg.norm(pooled, axis=1, keepdims=True) if normalize else pooled
```

Mean pooling collapses per-token hidden states into one 384-dim vector per
text; normalizing means a **dot product doubles as cosine similarity** —
no separate similarity function needed.

---

## 2. Similarity by hand vs. by library

The module deliberately has you compute similarity manually before reaching
for a library, so the abstraction isn't a black box later:

```python
scores = X.dot(v)              # X: (n_chunks, 384) matrix, v: (384,) query vector
best_chunk = chunks[int(scores.argmax())]
```

Once that's understood, `minsearch.VectorSearch` is the same idea,
packaged: `fit(X, payload)` stores the matrix and metadata,
`search(query_vector, num_results)` does the dot-product-and-sort for you.

**Chunking still matters here** — the same 2000/1000 sliding window from
Module 1. A full-page embedding averages over every topic on the page; a
chunk embedding stays close to one topic, so the highest-scoring *chunk*
for a query is a sharper match than the highest-scoring *page* would be.

---

## 3. Vector search vs. keyword search — where they diverge

| | Keyword search (`Index`) | Vector search (`VectorSearch`) |
|---|---|---|
| Matches on | Exact terms / token overlap | Semantic similarity |
| Strength | Exact names, codes, rare terms | Paraphrases, synonyms, concepts |
| Weakness | Misses different wording for the same idea | Misses exact rare terms; can drift semantically nearby but not quite right |
| This module's example | "PostgreSQL" query top-5 misses the pgvector page | Vector top-5 finds the pgvector page by concept, even without exact phrase match |

Running the *same* query through both and diffing the top-5 filenames is
the fastest way to see this concretely — it's not abstract, it's a
one-line list comprehension away from a real example (`homework2_answers.md`
Q5).

---

## 4. Hybrid search: combining ranked lists, not raw scores

Vector similarity scores and keyword TF-IDF-style scores live on
**incomparable scales** — you can't just average them. Reciprocal Rank
Fusion (RRF) sidesteps this by using only *rank position*:

```
RRF(doc) = Σ  1 / (k + rank(doc))
           lists
```

```python
def rrf(result_lists, k=60, num_results=5):
    scores, docs = {}, {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            key = (doc["filename"], doc["start"])
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
            docs[key] = doc
    return [docs[k] for k in sorted(scores, key=scores.get, reverse=True)[:num_results]]
```

A document that ranks well in **both** lists accumulates score from each
one, so it can outrank a document that's #1 in a single list but absent
from the other. That's exactly what happened for "How do I give the model
access to tools?" — the function-calling lesson wasn't necessarily top in
either search alone, but ranked first after fusion (`homework2_answers.md`
Q6). `k=60` is the RRF paper's default; smaller `k` sharpens the importance
of top ranks, larger `k` flattens it (revisited with real tuning data in
Module 4).

---

## 5. SA Connection — vector search in enterprise AI delivery

- **The embedding model choice is an infrastructure decision, not just an
  accuracy one.** ONNX vs. full `sentence-transformers` vs. a hosted
  embeddings API trades install footprint, latency, and cost differently —
  worth surfacing explicitly when scoping a customer's retrieval stack.
- **"Vector search vs. keyword search" is the wrong framing for customers.**
  The right framing is hybrid-by-default, tuned per corpus — the module's
  own diff-the-top-5 exercise is a fast, concrete way to show a customer
  *why* neither alone is sufficient for their data.
- **RRF is vendor-agnostic.** The fusion technique is identical whether the
  vector store is pgvector, Pinecone, or Elasticsearch's dense vector
  fields — it's a pattern to bring into any stack, not a specific tool.
- **Anecdote isn't evidence.** This module's manual query comparisons are
  for building intuition; recommending a retrieval strategy to a customer
  needs the measured Hit Rate/MRR numbers from Module 4, not "it looked
  better on a couple of queries."

---

## 6. Certification relevance — Anthropic Claude Architect

- 🟢 **Embeddings and vector search** — how dense retrieval works
  mechanically (encode, normalize, dot product); this is foundational RAG
  infrastructure. *(High relevance.)*
- 🟢 **Hybrid search / RRF** — combining ranked retrieval methods without
  needing comparable raw scores. *(High relevance — recurring
  architectural pattern.)*
- 🟡 **Model deployment footprint** — ONNX vs. full framework runtimes as a
  latency/ops tradeoff. *(Medium — infra judgment.)*
- 🟡 **Chunking strategy** — carried over from Module 1, now applied to
  vector retrieval specifically. *(Medium.)*
- ⚪ **minsearch specifics** — a teaching tool; the *interface shape*
  (`fit`, `search`, keyword/text fields) transfers to any production vector
  store.

---

## 7. Quick reference

```python
# ONNX embedder
from embedder import Embedder
emb = Embedder()                       # 384-dim, mean-pooled, normalized
v = emb.encode(text)                   # single text
X = emb.encode_batch(texts)            # batch -> matrix

# Similarity by hand (normalized vectors -> dot == cosine)
scores = X.dot(v)
best = chunks[int(scores.argmax())]

# Vector search with minsearch
from minsearch import VectorSearch, Index
vindex = VectorSearch(keyword_fields=[])
vindex.fit(X, chunks)                  # fit(matrix, payload)
vindex.search(query_vector, num_results=5)

# Keyword search, for comparison / hybrid
tindex = Index(text_fields=["content"], keyword_fields=["filename"])
tindex.fit(chunks)
tindex.search(query_text, num_results=5)

# Hybrid: Reciprocal Rank Fusion
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

*See [`homework2_answers.md`](./homework2_answers.md) for the graded Q&A
with observed values.*
