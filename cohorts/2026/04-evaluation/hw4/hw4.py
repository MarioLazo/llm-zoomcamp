"""
LLM Zoomcamp 2026 - Homework 4: Evaluation
https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw4

Results:
  Q1: ~1400 input tokens (avg across first 3 lesson pages)
  Q2: 01-agentic-rag/lessons/03-rag.md  (text_search first result)
  Q3: 01-agentic-rag/lessons/01-intro.md (vector_search first result)
  Q4: 0.76 Hit Rate (text_search)
  Q5: 0.55 MRR (vector_search)
  Q6: k=1  (best MRR for hybrid_search)
"""

import json
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from tqdm.auto import tqdm
from minsearch import Index, VectorSearch
from gitsource import GithubRepositoryDataReader, chunk_documents

from embedder import Embedder
from evaluation_utils import llm_structured

load_dotenv()

COMMIT = "8c1834d"

# ── Data ──────────────────────────────────────────────────────────────────────

reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id=COMMIT,
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)
documents = [file.parse() for file in reader.read()]
print(f"Loaded {len(documents)} lesson pages")

chunks = chunk_documents(documents, size=2000, step=1000)
print(f"Created {len(chunks)} chunks")

# ── Q1: Generate questions for first 3 pages ──────────────────────────────────

data_gen_instructions = """
You emulate a student who is taking our LLM course.
You are given one lesson page from the course.
Formulate 5 questions this student might ask that are answered by this page.

Rules:
- The page should contain the answer to each question.
- Make the questions complete and not too short.
- Use as few words as possible from the page; don't copy its phrasing.
- The questions should resemble how people actually ask things online:
  not too formal, not too short, not too long.
- Ask about the content of the lesson, not about its formatting or filename.
""".strip()


class Questions(BaseModel):
    questions: list[str]


client = OpenAI()
usages = []
for doc in documents[:3]:
    user_prompt = json.dumps({"filename": doc["filename"], "content": doc["content"]})
    _, usage = llm_structured(client, data_gen_instructions, user_prompt, Questions)
    print(f"  {doc['filename']}: {usage.input_tokens} input tokens")
    usages.append(usage.input_tokens)

avg_tokens = sum(usages) / len(usages)
print(f"Q1 — Average input tokens: {avg_tokens:.0f}")  # ~1400

# ── Build indexes ─────────────────────────────────────────────────────────────

tindex = Index(text_fields=["content"], keyword_fields=["filename"])
tindex.fit(chunks)

embedder = Embedder()
texts = [c["content"] for c in chunks]
batch_size = 64
vecs = []
for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
    vecs.append(embedder.encode_batch(texts[i:i + batch_size]))
X = np.vstack(vecs)

vindex = VectorSearch(keyword_fields=["filename"])
vindex.fit(X, chunks)

# ── Search functions ──────────────────────────────────────────────────────────

def text_search(query, num_results=5):
    return tindex.search(query, num_results=num_results)


def vector_search(query, num_results=5):
    v = embedder.encode(query)
    return vindex.search(v, num_results=num_results)


def rrf(result_lists, k=60, num_results=5):
    scores = {}
    docs = {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            key = (doc["filename"], doc["start"])
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
            docs[key] = doc
    ranked = sorted(scores, key=scores.get, reverse=True)
    return [docs[key] for key in ranked[:num_results]]


def hybrid_search(query, k=60, num_results=5):
    return rrf([text_search(query, 10), vector_search(query, 10)], k=k, num_results=num_results)

# ── Evaluation ────────────────────────────────────────────────────────────────

ground_truth = pd.read_csv("ground-truth.csv").to_dict(orient="records")
print(f"Ground truth: {len(ground_truth)} questions")


def evaluate(ground_truth, search_fn):
    rel = []
    for q in tqdm(ground_truth):
        results = search_fn(q["question"])
        rel.append([int(r["filename"] == q["filename"]) for r in results])
    hit = sum(1 for r in rel if 1 in r) / len(rel)
    mrr_score = sum(
        1 / (r.index(1) + 1) for r in rel if 1 in r
    ) / len(rel)
    return {"hit_rate": hit, "mrr": mrr_score}


# Q2
q = ground_truth[0]["question"]
print(f"\nQ2 — text_search first result: {text_search(q)[0]['filename']}")
# 01-agentic-rag/lessons/03-rag.md

# Q3
print(f"Q3 — vector_search first result: {vector_search(q)[0]['filename']}")
# 01-agentic-rag/lessons/01-intro.md

# Q4
m = evaluate(ground_truth, text_search)
print(f"Q4 — text_search Hit Rate: {m['hit_rate']:.4f}")  # 0.76

# Q5
m = evaluate(ground_truth, vector_search)
print(f"Q5 — vector_search MRR: {m['mrr']:.4f}")  # 0.55

# Q6
print("\nQ6 — hybrid_search MRR by k:")
best_k, best_mrr = None, -1
for k in [1, 50, 100, 200]:
    m = evaluate(ground_truth, lambda q, k=k: hybrid_search(q, k=k))
    print(f"  k={k}: MRR={m['mrr']:.4f}")
    if m["mrr"] > best_mrr:
        best_mrr, best_k = m["mrr"], k
print(f"Best k = {best_k}")  # k=1
