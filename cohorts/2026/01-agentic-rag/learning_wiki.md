# Personal Learning Wiki — Module 1: Agentic RAG

**Cohort:** LLM Zoomcamp 2026 · **Module:** 1 — Agentic RAG
**Stack:** OpenAI `gpt-5.4-mini` + minsearch + `gitsource` + toyaikit

---

## TL;DR

- **RAG is three steps, not magic.** Search → build a prompt with the
  retrieved context → call the LLM. Everything else (chunking, hybrid
  search, agents) is a refinement on top of this loop.
- **Retrieval quality gates answer quality.** The LLM can only answer from
  what `search` hands it — a bad match means a bad or "I don't know" answer,
  regardless of how good the model is.
- **Chunking trades index size for retrieval precision.** Splitting long
  pages into overlapping windows means each retrieved unit is smaller and
  more topically focused, which shrinks the context you send to the model.
- **Context size is a token cost lever you control directly.** The same
  query against a chunked vs unchunked index costs roughly 3× fewer input
  tokens — with no change to the model or the question.
- **An agent is RAG with the loop inverted.** Instead of you calling search
  once and handing the results to the model, you hand the model a `search`
  tool and let it decide when and how many times to call it.

---

## 1. RAG from scratch

The minimal RAG loop, independent of any framework:

```python
def rag(query):
    results = search(query)                  # 1. retrieve
    prompt = build_prompt(query, results)     # 2. augment
    answer = llm(prompt)                      # 3. generate
    return answer
```

`RAGBase` (from the module's `rag_helper.py`) packages this as a class with
overridable `search`, `build_context`, `build_prompt`, and `llm` methods —
the homework's core exercise is adapting it from the course FAQ schema
(`section`/`question`/`answer`) to a different schema (`filename`/`content`)
by overriding just `search` and `build_context`. The `rag()`/`build_prompt()`
orchestration doesn't need to change — a sign the abstraction is at the
right level.

**Key habit:** make the LLM call return the full response object (not just
`.output_text`), so you can read `response.usage.input_tokens` — you can't
manage a cost you can't see.

---

## 2. Indexing and search with minsearch

`minsearch.Index` is a small, dependency-light in-memory search engine:
declare `text_fields` (matched with TF-IDF-style scoring) and
`keyword_fields` (exact-match filters/boosts), `fit(documents)`, then
`search(query)`.

For "How does the agentic loop keep calling the model until it stops?", the
top hit is the lesson that names the concept directly
(`14-agentic-loop.md`) — keyword search rewards exact term overlap. This is
the same lesson carried into Module 2 (vector vs. keyword search) and
Module 4 (measuring which one wins where).

---

## 3. Chunking — why and how

Full lesson pages run thousands of characters and mix several subtopics. A
single page-level match on a long document still pulls in the *entire*
page as context, even if only one paragraph is relevant — imprecise
retrieval, bloated prompts.

`gitsource.chunk_documents(documents, size=2000, step=1000)` fixes this
with a sliding window:

- Each chunk is `size` (2000) characters of the page.
- The window advances by `step` (1000) characters, so consecutive chunks
  overlap by `size - step` (1000) characters — a passage that straddles a
  window boundary still appears whole in at least one chunk.
- 72 pages → **295 chunks**.

**Measured effect:** indexing chunks instead of full pages and re-running
the same RAG query cut input tokens to about **⅓** of the unchunked
version (Q3 → Q5). Same query, same model, same answer quality goal — just
a smaller, more targeted context window.

---

## 4. Turning RAG into an agent

Static RAG always searches exactly once, with the exact user query. An
**agent** flips this: give the LLM a `search` tool (a typed function with a
docstring the framework turns into a tool schema) and a system prompt, and
let the model decide *whether*, *when*, and *with what query* to call it.

```python
def search(query: str) -> list:
    """Search the course lesson pages for relevant content."""
    return index.search(query, num_results=3)

tools = Tools()
tools.add_tool(search)
runner = OpenAIResponsesRunner(tools=tools, developer_prompt=SYSTEM_PROMPT, llm_client=llm_client)
runner.loop("How does the agentic loop work, and how is it different from plain RAG?")
```

Nudged with *"make multiple searches with different keywords before
answering,"* the agent called `search` **4** times on its own — trying
different phrasings to triangulate the answer instead of relying on a
single keyword match. This is the same behavior [`toyaikit`](https://github.com/alexeygrigorev/toyaikit)
demonstrates in the lessons: the loop keeps calling the model, which keeps
calling tools, until the model decides it has enough to answer.

**The core distinction (RAG vs. agentic RAG):** in plain RAG, *you* decide
when to search. In agentic RAG, *the model* decides — trading determinism
for adaptivity, the same tradeoff Module 3 revisits at the workflow level.

---

## 5. SA Connection — agentic RAG in enterprise AI delivery

- **RAG is the default entry point for enterprise knowledge questions.**
  Before reaching for an agent, most "answer questions over our docs" asks
  are solved by the three-step loop — simpler to build, test, and explain.
- **Chunking strategy is a real design decision, not a footnote.** Chunk
  size/overlap directly trades off retrieval precision against prompt size
  and cost — this is a conversation worth having explicitly with a customer
  rather than defaulting silently.
- **Token visibility from day one.** Surfacing `usage.input_tokens` on the
  very first RAG call (not bolted on later, as in Module 5's monitoring)
  means cost is never a surprise once the prototype ships.
- **Agentic retrieval is a scope decision, not a default.** Giving the
  model a `search` tool buys adaptivity (it can retry with better
  keywords) at the cost of determinism and extra latency/token spend per
  extra tool call — worth it for open-ended Q&A, often not worth it for a
  narrow, well-defined lookup.

---

## 6. Certification relevance — Anthropic Claude Architect

- 🟢 **RAG architecture** — the retrieve → augment → generate loop, and
  where each stage can fail. *(High relevance — foundational.)*
- 🟢 **Tool use / function calling** — typed function signatures + docstrings
  become tool schemas; the model chooses when to call them.
  *(High relevance.)*
- 🟢 **Agentic loops** — the model-driven loop of tool calls until it
  decides to stop, vs. a single deterministic search call.
  *(High relevance — core agent competency.)*
- 🟡 **Chunking strategy** — window size/overlap tradeoffs for retrieval
  precision vs. prompt size. *(Medium — practical RAG tuning.)*
- 🟡 **Token/cost observability** — reading usage off the LLM response to
  make cost visible per call. *(Medium — operational habit.)*
- ⚪ **minsearch specifics** — a teaching tool; production uses Elasticsearch,
  OpenSearch, pgvector, etc. The *patterns* (text/keyword fields, boosting,
  filtering) transfer directly.

---

## 7. Quick reference

```python
# Load pinned course data
from gitsource import GithubRepositoryDataReader, chunk_documents
reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub", repo_name="llm-zoomcamp",
    commit_id="8c1834d", allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)
documents = [f.parse() for f in reader.read()]   # 72 pages
chunks = chunk_documents(documents, size=2000, step=1000)  # 295 chunks

# Index + search
import minsearch
index = minsearch.Index(text_fields=["content"], keyword_fields=["filename"])
index.fit(documents)
index.search(query)

# RAG loop
def rag(query):
    results = search(query)
    prompt = build_prompt(query, results)
    return llm(prompt)   # return the full response to read .usage.input_tokens

# Agent (toyaikit)
def search(query: str) -> list:
    """Docstring becomes the tool description."""
    return index.search(query, num_results=3)
tools = Tools(); tools.add_tool(search)
OpenAIResponsesRunner(tools=tools, developer_prompt=SYSTEM_PROMPT, llm_client=llm_client).loop(question)
```

---

*See [`homework1_answers.md`](./homework1_answers.md) for the graded Q&A
with observed values.*
