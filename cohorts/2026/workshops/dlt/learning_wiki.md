# Personal Learning Wiki — Workshop: dlt (Data Ingestion for Analytics)

**Cohort:** LLM Zoomcamp 2026 · **Workshop:** Pulling traces from a
monitoring service for analytics with dlt
**Stack:** dlt + DuckDB + Pydantic Logfire + Pydantic AI (`gpt-5.4-mini`)

---

## TL;DR

- **dlt normalizes nested JSON automatically.** One resource can yield
  arbitrarily nested dicts/lists; dlt splits them into a main table plus one
  child table per nested list, linked by `_dlt_id`/`_dlt_parent_id` — no
  manual flattening code.
- **Two source shapes, pick based on the API.** A GET + query-param
  pagination API fits dlt's declarative `RESTAPIConfig`. A POST + JSON-body
  API (like Logfire's query endpoint) doesn't — write a plain
  `@dlt.resource` generator instead and let normalization still do its job.
- **Dotted keys aren't nesting.** OTel-style flat attributes
  (`gen_ai.usage.input_tokens`) are a single-level dict with dotted *string*
  keys — dlt turns each into one column (`attributes__gen_ai_usage_input_tokens`),
  not a child table. Only actual nested dicts/lists produce child tables.
- **The dataset name is just a config value.** Matching a spec's expected
  schema name (`agent_traces`) is a one-line choice in `dlt.pipeline(...)`,
  not a coincidence to work around.
- **One real query can spider into dozens of tables.** A single `SELECT *
  FROM records` against Logfire produced **24 tables** in DuckDB — 1 main +
  17 real child tables (messages, tool calls, token-usage metrics, scrubbed
  fields) + 3 dlt bookkeeping tables (`_dlt_loads`, `_dlt_pipeline_state`,
  `_dlt_version`).

---

## 1. The dlt core loop

Every dlt pipeline is the same three pieces:

```python
@dlt.resource(name="...")
def my_resource():
    yield {...}  # any dict, arbitrarily nested

pipeline = dlt.pipeline(pipeline_name="...", destination="duckdb", dataset_name="...")
info = pipeline.run(my_resource())
```

`@dlt.source` groups multiple resources under one pipeline; a single
`@dlt.resource` is enough when there's one logical stream (like "all
records from this trace query"). `pipeline.run()` does extract → normalize
→ load in one call; `pipeline.last_trace.last_normalize_info` shows exactly
which tables got how many rows on that run.

---

## 2. Two ways to build a source

**Declarative, for GET + pagination** (`code/rest_api_pipeline.py`, from the
workshop's Claude-traces example) — describe the API as config, dlt handles
the request loop:

```python
config: RESTAPIConfig = {
    "client": {
        "base_url": base_url,
        "paginator": {
            "type": "offset", "limit": page_size, "offset": 0,
            "limit_param": "limit", "offset_param": "offset",
            "total_path": "total",
        },
    },
    "resources": [
        {"name": "logs", "endpoint": {"path": "/logs", "data_selector": "logs"}, "primary_key": "index"},
    ],
}
yield from rest_api_resources(config)
```

**Custom generator, for POST + JSON body** (`hw_dlt/ingest_logfire.py`) —
Logfire's query API is a `POST` with the SQL in the request body, which
doesn't fit the paginator model above. A plain resource function calling
`requests.post` directly, then yielding rows, gets the same downstream
normalization for free:

```python
@dlt.resource(name="records", write_disposition="replace")
def logfire_records(lookback_hours=24, limit=10_000):
    response = requests.post(
        f"{base_url}/v2/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"sql": "SELECT * FROM records ORDER BY start_timestamp DESC",
              "min_timestamp": min_timestamp, "limit": limit},
    )
    yield from response.json()["data"]
```

Same `pipeline.run()` call either way — the fetch mechanics differ, the
normalization and loading don't.

---

## 3. What 1 query becoming 24 tables actually looks like

Ran the ingest once against 3 real agent traces (16 span rows total). The
`attributes` column on each span carries everything Logfire captured —
input/output messages, tool definitions, token-usage metrics — and dlt's
normalizer split it by *shape*, not by name:

- **Flat dict → columns on the main table.** `attributes["gen_ai.usage.input_tokens"]`
  is a scalar under a dotted string key → column
  `records.attributes__gen_ai_usage_input_tokens`. No child table, because
  there's nothing to repeat.
- **List of dicts → child table.** `attributes["gen_ai.input_messages"]` is a
  *list* (one entry per message) → table
  `records__attributes__gen_ai_input_messages`, one row per message, linked
  back to `records` by `_dlt_parent_id`.
- **Lists inside those lists → grandchild tables.** Each message's `parts`
  is itself a list →
  `records__attributes__gen_ai_input_messages__parts`, and a tool-call
  part's `result` is a list again →
  `...__parts__result`. Nesting depth becomes table-name depth
  (`__`-joined), one level per generation.

Net result for this run: 1 main table, 17 child/grandchild tables from 6
distinct nested attribute paths (messages, tool calls, tool definitions,
system instructions, scrubbed-field paths, token-usage details), plus 3 dlt
bookkeeping tables = **24**, verified with the same query the homework
grades against:

```sql
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'agent_traces';
-- 24
```

---

## 4. Querying the normalized result

The `dataset_name` passed to `dlt.pipeline()` becomes the DuckDB schema —
`information_schema.tables WHERE table_schema = 'agent_traces'` only works
because that's the literal value used, not a default. Two query shapes came
up constantly:

**Aggregate on the main table** (works when the metric is a flat column,
like token counts):

```sql
SELECT trace_id, SUM(attributes__gen_ai_usage_input_tokens) AS total_input_tokens
FROM agent_traces.records
WHERE attributes__gen_ai_usage_input_tokens IS NOT NULL
GROUP BY 1;
```

**Join parent → child** (needed once the data you want lives in a child
table, e.g. counting message parts per span):

```sql
SELECT r.span_name, COUNT(*) AS parts
FROM agent_traces.records r
JOIN agent_traces.records__attributes__gen_ai_input_messages m ON m._dlt_parent_id = r._dlt_id
JOIN agent_traces.records__attributes__gen_ai_input_messages__parts p ON p._dlt_parent_id = m._dlt_id
GROUP BY 1;
```

`information_schema.columns` doubles as a schema-discovery tool when you
don't know the exact flattened column name in advance — used
`... WHERE column_name ILIKE '%input_tokens%'` to find
`attributes__gen_ai_usage_input_tokens` without guessing dlt's naming
convention ahead of time.

---

## 5. SA Connection — data ingestion in enterprise AI delivery

- **Every monitoring vendor's export format is different — dlt's
  normalization is the constant.** Logfire, Langfuse, Datadog: different
  nesting, different keys, same fix. That's the pitch for standardizing on a
  normalization layer instead of writing a bespoke flattener per vendor.
- **Declarative-first, custom-when-needed is the right default.** Reaching
  for `RESTAPIConfig` first (GET APIs) and only dropping to a raw
  `@dlt.resource` generator when the API genuinely doesn't fit (POST body,
  non-standard auth) keeps most pipelines short and auditable.
- **Schema sprawl is a cost, not a bug.** 24 tables from one query is
  *correct* behavior for deeply nested trace data, but it's also a real
  onboarding cost for whoever queries this warehouse next — worth
  documenting the child-table naming convention (`__`-joined nesting path)
  up front rather than making each analyst rediscover it.
- **`write_disposition="replace"` vs `"append"`/`"merge"` is a real decision
  per pipeline**, not a default to leave unexamined — `replace` was fine
  here for a homework snapshot, but a production traces pipeline usually
  wants incremental loading (dlt supports this natively) to avoid re-pulling
  months of history on every run.

---

## 6. Certification relevance — Anthropic Claude Architect

- 🟢 **Data pipeline design for AI observability** — getting trace/log data
  out of a monitoring vendor and into a queryable warehouse.
  *(High relevance — a recurring "how do we analyze our agent's behavior"
  ask.)*
- 🟢 **Schema normalization of nested LLM payloads** — messages, tool calls,
  and token usage are inherently nested; knowing *why* they explode into
  child tables (not just that they do) matters for explaining warehouse
  costs to a customer.
- 🟡 **REST API integration patterns** — declarative config vs. custom code,
  auth handling, pagination. *(Medium — a general data-engineering skill
  that shows up whenever an agent needs external data.)*
- 🟡 **DuckDB as an analytics destination** — lightweight, embedded,
  SQL-queryable without standing up infrastructure. *(Medium — useful for
  prototypes and small-scale analytics; production usually graduates to a
  warehouse.)*
- ⚪ **dlt-specific API surface** — the exact decorator/config syntax is
  unlikely to be tested directly; the *pattern* (source → resource →
  pipeline → normalized destination) transfers to Airbyte, Fivetran, or a
  hand-rolled ETL script.

---

## 7. Quick reference

```python
# Custom resource against a POST/JSON-body API
import dlt, requests

@dlt.resource(name="records", write_disposition="replace")
def logfire_records():
    resp = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json={"sql": sql})
    yield from resp.json()["data"]

pipeline = dlt.pipeline(pipeline_name="logfire_traces", destination="duckdb", dataset_name="agent_traces")
info = pipeline.run(logfire_records())
print(pipeline.last_trace.last_normalize_info)  # per-table row counts

# Discover a flattened column name without guessing dlt's naming convention
# SELECT column_name FROM information_schema.columns
# WHERE table_schema = 'agent_traces' AND column_name ILIKE '%input_tokens%';

# Join parent -> child table
# ... JOIN child_table c ON c._dlt_parent_id = parent._dlt_id
```

---

*See [`dlt_homework_answers.md`](./dlt_homework_answers.md) for the graded
Q&A with observed values.*
