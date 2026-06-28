"""
LLM Zoomcamp 2026 - Homework 2: Vector Search
https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw2

Setup (run once, in this folder):
    uv init --no-workspace
    uv add onnxruntime tokenizers numpy tqdm minsearch gitsource
    uv add --dev huggingface-hub jupyter
    uv run python download.py    # downloads Xenova/all-MiniLM-L6-v2 (needs huggingface.co)

Then:
    uv run python hw2.py
"""

import numpy as np
from gitsource import GithubRepositoryDataReader, chunk_documents
from minsearch import Index, VectorSearch
from embedder import Embedder

QUERY = 'How does approximate nearest neighbor search work?'


def closest(value, options):
    """Pick the option nearest to the computed value."""
    return min(options, key=lambda o: abs(o - value))


# --- Embedder (ONNX all-MiniLM-L6-v2) ---
emb = Embedder()  # models/Xenova/all-MiniLM-L6-v2

# Q1 - Embed the query, report v[0]
v = emb.encode(QUERY)
print(f"Q1: v[0] = {v[0]:.4f}  (closest: {closest(v[0], [-0.31, -0.02, 0.12, 0.44])})")
assert v.shape == (384,), v.shape

# --- Load the lesson pages (pinned commit, 72 pages) ---
reader = GithubRepositoryDataReader(
    repo_owner='DataTalksClub',
    repo_name='llm-zoomcamp',
    commit_id='8c1834d',
    allowed_extensions={'md'},
    filename_filter=lambda path: '/lessons/' in path,
)
documents = [file.parse() for file in reader.read()]
assert len(documents) == 72, len(documents)

# Q2 - Cosine similarity of the query with one specific page
page = next(d for d in documents
            if d['filename'] == '02-vector-search/lessons/07-sqlitesearch-vector.md')
page_vec = emb.encode(page['content'])
cos = float(page_vec.dot(v))  # vectors are normalized -> dot == cosine
print(f"Q2: cosine = {cos:.4f}  (closest: {closest(cos, [0.07, 0.37, 0.68, 0.92])})")

# --- Chunk the pages (same params as homework 1) ---
chunks = chunk_documents(documents, size=2000, step=1000)
chunk_vectors = emb.encode_batch([c['content'] for c in chunks])
X = np.array(chunk_vectors)

# Q3 - Highest-scoring chunk for the Q1 query, by hand
scores = X.dot(v)
best = chunks[int(scores.argmax())]
print(f"Q3: highest-scoring chunk file = {best['filename']}")

# Q4 - Vector search with minsearch
vindex = VectorSearch(keyword_fields=[])
vindex.fit(X, chunks)
q4_query = 'What metric do we use to evaluate a search engine?'
q4_vec = emb.encode(q4_query)
q4_results = vindex.search(q4_vec, num_results=5)
print(f"Q4: first result file = {q4_results[0]['filename']}")

# Q5 - Text search vs vector search
tindex = Index(text_fields=['content'], keyword_fields=['filename'])
tindex.fit(chunks)
q5_query = 'How do I store vectors in PostgreSQL?'
q5_vec = emb.encode(q5_query)
q5_vector_results = vindex.search(q5_vec, num_results=5)
q5_text_results = tindex.search(q5_query, num_results=5)
vector_files = [r['filename'] for r in q5_vector_results]
text_files = [r['filename'] for r in q5_text_results]
only_in_vector = [f for f in vector_files if f not in text_files]
print(f"Q5: in vector but not text = {only_in_vector}")


# Q6 - Hybrid search with Reciprocal Rank Fusion (k=60)
def rrf(result_lists, k=60, num_results=5):
    scores = {}
    docs = {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            key = (doc['filename'], doc['start'])
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
            docs[key] = doc
    ranked = sorted(scores, key=scores.get, reverse=True)
    return [docs[key] for key in ranked[:num_results]]


q6_query = 'How do I give the model access to tools?'
q6_vec = emb.encode(q6_query)
vector_results = vindex.search(q6_vec, num_results=5)
text_results = tindex.search(q6_query, num_results=5)
fused = rrf([vector_results, text_results])
print(f"Q6: first after RRF = {fused[0]['filename']}")
