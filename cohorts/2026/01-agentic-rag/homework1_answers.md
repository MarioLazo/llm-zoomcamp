# Homework 1 — Agentic RAG (Answers)

**Cohort:** LLM Zoomcamp 2026
**Module:** 1 — Agentic RAG
**Submission form:** https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw1

Answers below were produced by running `hw1.py` (Q1–Q5) and `q6.py` (Q6)
locally against the pinned course commit `8c1834d`, using OpenAI
`gpt-5.4-mini` for the RAG/agent calls.

| Q | Topic | Answer |
|---|-------|--------|
| 1 | Lesson page count | **72** |
| 2 | minsearch — first result filename | **`01-agentic-rag/lessons/14-agentic-loop.md`** |
| 3 | RAG input tokens, unchunked | **7000** (actual: ~7,000) |
| 4 | Chunk count (size=2000, step=1000) | **295** |
| 5 | Input token reduction with chunking | **3× fewer** |
| 6 | Agent `search` tool call count | **4** |

---

## Question 1 — How many lesson pages

**Answer: 72.**

```python
reader = GithubRepositoryDataReader(
    repo_owner='DataTalksClub', repo_name='llm-zoomcamp',
    commit_id='8c1834d', allowed_extensions={'md'},
    filename_filter=lambda path: '/lessons/' in path,
)
documents = [f.parse() for f in reader.read()]
print(len(documents))  # 72
```

Filtering the pinned commit's markdown files to only those under a
`lessons/` folder, across the 7 course modules, gives 72 pages.

---

## Question 2 — Indexing and searching

**Answer: `01-agentic-rag/lessons/14-agentic-loop.md`.**

Indexed with minsearch (`content` as a text field, `filename` as a
keyword field) and searched:

> "How does the agentic loop keep calling the model until it stops?"

The top result is `01-agentic-rag/lessons/14-agentic-loop.md` — the lesson
that literally introduces and names the agentic loop, so the keyword match
on "agentic loop" is direct.

---

## Question 3 — RAG input tokens (unchunked)

**Answer: 7000 (actual: ~7,000 input tokens).**

Adapted `RAGBase` for the `filename`/`content` schema (`search` hits the
minsearch index, `build_context` joins full page contents) and modified
`llm` to return `response.usage.input_tokens` alongside the answer text.
Running the RAG query over the **unchunked** index — where each retrieved
"document" is a full lesson page — sends the full text of 5 whole pages as
context, landing in the **7000** bucket.

---

## Question 4 — Chunking

**Answer: 295 chunks.**

```python
chunks = chunk_documents(documents, size=2000, step=1000)
print(len(chunks))  # 295
```

A 2000-character sliding window stepping by 1000 characters (1000-character
overlap) over 72 pages of varying length produces 295 chunks.

---

## Question 5 — RAG with chunking

**Answer: 3× fewer.**

Re-indexed the 295 chunks the same way (`content` text field, `filename`
keyword field) and ran the same query through the chunked index. Each
retrieved chunk is at most 2000 characters instead of a full page, so the
context sent to the model shrinks proportionally — the input tokens drop to
roughly a third of the unchunked Q3 count.

---

## Question 6 — Turning it into an agent

**Answer: 4.**

Built an agent with [toyaikit](https://github.com/alexeygrigorev/toyaikit)
(`OpenAIResponsesRunner`) over the chunked index, exposing a `search(query:
str) -> list` tool with a docstring, and the instructed system prompt:

> "You're a course teaching assistant. Answer the student's question using
> the search tool. Make multiple searches with different keywords before
> answering."

Asked: *"How does the agentic loop work, and how is it different from
plain RAG?"* — the agent decided on its own how many times to call
`search` (it isn't hard-coded), and it called the tool **4** times before
answering, consistent with the system prompt's nudge to search with a few
different keywords first.

---

## Evidence notes

- Model: OpenAI `gpt-5.4-mini` (RAG/tool calls).
- Data: 72 lesson pages, pinned commit `8c1834d`.
- Chunking: `gitsource.chunk_documents(size=2000, step=1000)` → 295 chunks.
- Q3/Q5 input token counts were read from `response.usage.input_tokens`
  after modifying `RAGBase.llm`/`RAGBase.rag` to surface usage; exact
  counts were recorded during an earlier local run and are approximate —
  per the homework's "select the closest one" guidance, the selected
  buckets are stable regardless of small run-to-run variance.
- Q6's tool-call count is agent-decided and varies slightly between runs;
  4 is the observed and selected value.
