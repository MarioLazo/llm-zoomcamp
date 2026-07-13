# Personal Learning Wiki — Module 5: Monitoring with OpenTelemetry

**Cohort:** LLM Zoomcamp 2026 · **Module:** 5 — Monitoring
**Stack:** OpenTelemetry SDK + SQLite + `gpt-5.4-mini` + minsearch

---

## TL;DR

- **OpenTelemetry is the instrumentation standard.** Logfire, Langfuse, Arize Phoenix, and Jaeger are all built on it. Learning OTel directly means understanding what every monitoring framework does under the hood.
- **Traces and spans model causality.** A trace is one request end-to-end; spans are the operations inside it. Nesting them shows you *which step caused the latency*.
- **Attributes turn spans into metrics.** Any value you care about (tokens, cost, model name) can be attached as a key-value pair and queried later.
- **Exporters decouple instrumentation from storage.** The same instrumented code can print to console (development), write to SQLite (homework), or stream to a remote collector (production) — just swap the exporter.
- **The LLM call dominates.** In a typical RAG trace, search takes ~1ms and the LLM takes 2–5 seconds. If you're optimizing latency, start with the model or prompt size.
- **Token counts are a stability signal.** If the same query produces identical input tokens every run, your retrieval is deterministic and consistent.

---

## 1. OpenTelemetry concepts

**Trace** — the complete story of one request through your system. For a RAG pipeline, one trace = one call to `rag()`.

**Span** — one named operation within a trace, with a start time, end time, and attributes. Spans form a tree: a parent span can contain child spans. Our trace has:

```
rag  (parent, ~4,100ms)
├── search (~0.6ms)
└── llm (~4,100ms)
```

**Attributes** — key-value pairs you attach to a span with `span.set_attribute(key, value)`. Used here for `input_tokens`, `output_tokens`, and `cost`.

**Tracer** — the object you use to create spans (`tracer.start_as_current_span(...)`).

**Span processor** — receives finished spans and forwards them to an exporter. `SimpleSpanProcessor` does this synchronously (one span at a time, blocking). Production systems use `BatchSpanProcessor` instead.

**Exporter** — decides where spans go: console, file, database, or a remote collector. You can swap exporters without touching your instrumentation code.

---

## 2. Instrumentation pattern

The cleanest way to add tracing without modifying the original class is subclassing:

```python
class RAGTraced(RAGBase):

    def search(self, query, num_results=5):
        with tracer.start_as_current_span("search"):
            return super().search(query, num_results=num_results)

    def llm(self, prompt):
        with tracer.start_as_current_span("llm") as span:
            response = super().llm(prompt)
            usage = response.usage
            cost = (usage.input_tokens * 0.15 + usage.output_tokens * 0.60) / 1_000_000
            span.set_attribute("input_tokens", usage.input_tokens)
            span.set_attribute("output_tokens", usage.output_tokens)
            span.set_attribute("cost", cost)
            return response

    def rag(self, query):
        with tracer.start_as_current_span("rag"):
            results = self.search(query)
            prompt = self.build_prompt(query, results)
            return self.llm(prompt).output_text
```

`start_as_current_span` automatically makes any nested span calls children of the current span. The tree structure emerges from the call hierarchy — no manual parent-linking needed.

---

## 3. Custom SQLite exporter

The exporter interface is simple: implement `export(spans)`, `shutdown()`, and `force_flush()`. The spans list contains `ReadableSpan` objects with `.name`, `.start_time`, `.end_time`, and `.attributes`.

```python
class SQLiteSpanExporter(SpanExporter):

    def __init__(self, db_path="traces.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                name TEXT, start_time INTEGER, end_time INTEGER,
                input_tokens INTEGER, output_tokens INTEGER, cost REAL
            )
        """)
        self.conn.commit()

    def export(self, spans):
        for span in spans:
            attrs = dict(span.attributes or {})
            self.conn.execute(
                "INSERT INTO spans VALUES (?, ?, ?, ?, ?, ?)",
                (span.name, span.start_time, span.end_time,
                 attrs.get("input_tokens"), attrs.get("output_tokens"), attrs.get("cost"))
            )
        self.conn.commit()
        return SpanExportResult.SUCCESS
```

Times are stored in nanoseconds. Convert to milliseconds for readability:

```python
df["duration_ms"] = (df["end_time"] - df["start_time"]) / 1_000_000
```

---

## 4. What the traces tell us

**Latency breakdown** (one query, one trace):

| Span | Duration | % of total |
|------|----------|------------|
| rag | ~4,100ms | 100% |
| llm | ~4,100ms | ~99.9% |
| search | ~0.6ms | ~0.01% |

The LLM API call is the bottleneck by orders of magnitude. Optimizations worth measuring:
- Reduce prompt size (chunking, fewer retrieved docs)
- Use a faster/cheaper model
- Stream the response to reduce perceived latency

**Token stability** (same query, 4 runs):

```
input_tokens: 7111, 7111, 7111, 7111
```

Identical every run → retrieval is deterministic. If tokens varied, it would
signal non-determinism in search (e.g., random tie-breaking, changing index state).

---

## 5. Production path: beyond SQLite

What this homework builds manually, production systems handle with the full OTel stack:

| Component | Homework | Production |
|-----------|----------|------------|
| Instrumentation | Manual subclass | Auto-instrumentation libraries |
| Processor | `SimpleSpanProcessor` | `BatchSpanProcessor` |
| Exporter | SQLite | OTel Collector → Jaeger / Tempo / Grafana |
| Dashboard | pandas queries | Jaeger UI / Grafana |

**Auto-instrumentation** (`opentelemetry-instrumentation-openai`) adds spans for
every OpenAI call with zero code changes — token counts, model names, durations,
all captured automatically.

**Frameworks** like Pydantic Logfire and Langfuse wrap OTel and add hosted
dashboards, agent tracing, and structured logging with minimal setup.
The underlying protocol is the same — understanding OTel means you can
read what any of these tools produce.

---

## 6. SA Connection — observability in enterprise AI delivery

- **Traces replace print-debugging at scale.** In a multi-step agent or RAG
  pipeline, knowing *which span* added latency is the difference between a 5-minute
  fix and a 2-day investigation. OTel gives you that visibility in production.
- **Cost is a span attribute.** Attaching `cost` to each LLM span means your
  monitoring dashboard is also a cost dashboard — no separate billing integration
  needed. Enterprise customers always ask "what does this cost per request?"
- **Determinism is a compliance signal.** Showing that input tokens are identical
  across runs (Q6) is a concrete answer to "is the system behaving consistently?"
  That matters in regulated industries.
- **The exporter pattern maps to vendor choice.** "Switch from Jaeger to Datadog"
  is a one-line config change — swap the exporter. Customers locked into a
  monitoring vendor are often surprised this is possible. Knowing OTel lets you
  make that case.
- **Async processing for production.** `SimpleSpanProcessor` is synchronous and
  adds latency to the request path. `BatchSpanProcessor` decouples span export
  from the request — important for latency-sensitive APIs.

---

## 7. Certification relevance — Anthropic Claude Architect

- 🟢 **Observability and tracing** — instrumenting LLM calls; measuring tokens,
  cost, and latency per request. *(High relevance — production readiness.)*
- 🟢 **Span/trace model** — understanding traces as causal trees; spans as
  bounded operations with attributes. *(High relevance — foundational concept.)*
- 🟡 **Custom exporters / integrations** — how monitoring frameworks connect to
  backends; the exporter swap pattern. *(Medium — architectural literacy.)*
- 🟡 **Token economics in practice** — why input tokens dominate cost; how
  retrieval strategy affects prompt size. *(Medium — operational judgment.)*
- ⚪ **OTel SDK specifics** — the exact Python API is unlikely to be tested;
  the *patterns* (instrument → process → export → query) transfer to any stack.

---

## 8. Quick reference

```python
# OTel setup
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(your_exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("llm-zoomcamp")

# Creating a span
with tracer.start_as_current_span("operation_name") as span:
    result = do_work()
    span.set_attribute("key", value)

# Duration from SQLite (nanoseconds → ms)
df["duration_ms"] = (df["end_time"] - df["start_time"]) / 1_000_000

# Cost formula (gpt-5.4-mini)
cost = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
```

---

*See [`homework5_answers.md`](./homework5_answers.md) for the graded Q&A with observed values.*
