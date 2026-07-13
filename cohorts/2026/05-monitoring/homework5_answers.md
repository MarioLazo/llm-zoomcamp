# Homework 5 — Monitoring with OpenTelemetry (Answers)

**Cohort:** LLM Zoomcamp 2026
**Module:** 5 — Monitoring
**Submission form:** https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw5

Answers produced by running the instrumented RAG locally (`gpt-5.4-mini`,
ONNX `all-MiniLM-L6-v2`, SQLite) with the custom `SQLiteSpanExporter`.

| Q | Topic | Answer |
|---|-------|--------|
| 1 | Spans in a single trace | **3** (rag, search, llm) |
| 2 | Input tokens for the LLM call | **7000** (actual: 7,111) |
| 3 | LLM call duration | **Over 2000ms** (actual: ~4,100ms) |
| 4 | Span names in the spans table | **rag, search, and llm** |
| 5 | Most time excluding rag | **llm** (~4,100ms vs ~0.6ms for search) |
| 6 | Input token variation across 4 runs | **They are identical** (7,111 every run) |

---

## Question 1 — Spans in a single trace

**Answer: 3**

`RAGTraced` wraps each of the three methods in its own span:

```python
def rag(self, query):
    with tracer.start_as_current_span("rag"):     # span 1
        results = self.search(query)               # span 2 (child)
        prompt  = self.build_prompt(query, results)
        response = self.llm(prompt)               # span 3 (child)
        return response.output_text
```

One parent span (`rag`) and two child spans (`search`, `llm`) = **3 spans** per trace.

---

## Question 2 — Input tokens

**Answer: 7000**

Observed in the `llm` span attribute after adding `set_attribute`:

```
input_tokens: 7,111
```

The prompt is large because we pass the full content of 5 retrieved lesson pages
as context — this is the same reason the chunked RAG from HW1 used ~10× fewer
tokens than the full-page version.

---

## Question 3 — LLM call duration

**Answer: Over 2000ms**

Observed durations from SQLite:

```
llm span:    ~4,100ms
search span: ~0.6ms
```

The LLM call dominates — the API round-trip to OpenAI takes 2–5 seconds for
typical queries. `gpt-5.4-mini` is fast, but network latency and generation
time push it well past 2 seconds.

---

## Question 4 — Span names in the table

**Answer: rag, search, and llm**

After switching from `ConsoleSpanExporter` to `SQLiteSpanExporter` and running
the query:

```sql
SELECT DISTINCT name FROM spans;
-- rag
-- search
-- llm
```

All three span names are saved because all three `with tracer.start_as_current_span(...)` 
blocks fire, finish, and are forwarded to the exporter by the `SimpleSpanProcessor`.

---

## Question 5 — Most time excluding rag

**Answer: llm**

Total duration by span type (excluding `rag`):

```
llm:    ~4,100ms
search: ~0.6ms
```

`search` is minsearch over an in-memory index — essentially instantaneous. The
LLM API call accounts for virtually all of the non-rag time.

---

## Question 6 — Token stability across 4 runs

**Answer: They are identical**

Input tokens for all 4 `llm` spans:

```
Run 1: 7,111
Run 2: 7,111
Run 3: 7,111
Run 4: 7,111
```

The same query hits the same deterministic minsearch index and retrieves the
same 5 chunks every time. The prompt is built identically → the same number of
input tokens every run. This confirms retrieval consistency — exactly the kind
of stability check a monitoring dashboard should surface.

---

## Evidence notes

- Model: `gpt-5.4-mini`
- Storage: SQLite (`traces.db`) via custom `SQLiteSpanExporter`
- Span processor: `SimpleSpanProcessor` (synchronous, one-at-a-time)
- LLM durations are network-dependent; range observed: 2,200–5,000ms
- Token counts are deterministic for this query and index
