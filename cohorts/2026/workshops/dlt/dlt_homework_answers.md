# Homework: dlt (Answers)

**Cohort:** LLM Zoomcamp 2026
**Workshop:** Pulling traces from a monitoring service for analytics with dlt
**Submission form:** https://courses.datatalks.club/llm-zoomcamp-2026/homework/dlt

Answers produced by running the Module 1 FAQ agent (rewritten in Pydantic AI,
`gpt-5.4-mini`), instrumented with Pydantic Logfire, then pulled back out with
a dlt pipeline into DuckDB. Solution code: [hw_dlt/](hw_dlt/).

| Q | Topic | Answer |
|---|-------|--------|
| 1 | Spans per agent run | **5** (observed 4 and 6 across 3 runs — nearest option; 1/15/30 are the wrong order of magnitude) |
| 2 | Tables dlt created in `agent_traces` | **24** |
| 3 | Input token usage for the Q1 trace | **1500 - 5000** (observed 1,628 / 4,054 / 4,138 across 3 runs) |

---

## Question 1 — Spans per agent run

**Answer: 5**

Instrumented `main.py` with:

```python
logfire.configure()
logfire.instrument_pydantic_ai()
```

Ran `uv run python main.py "How do I run Ollama locally?"` three times and
queried the ingested spans directly (`agent_traces.records`, grouped by
`trace_id`):

```
trace_id                          spans
019f81121fb011679d23988e06eb8b50  6   (invoke_agent + 3x chat + 2x execute_tool)
019f8112ab2904612e6de363156c06d3  6   (invoke_agent + 3x chat + 2x execute_tool)
019f811c406ebdadd94776255351b8cf  4   (invoke_agent + 2x chat + 1x execute_tool)
```

Each span is one of: `invoke_agent faq_agent` (the agent run), `chat
gpt-5.4-mini` (an LLM call), or `execute_tool search` (a tool call) — matching
the question's definition exactly. The count varies with how many searches
the model makes (1 or 2 in our runs), landing on 4 or 6. Of the four options
(1, 5, 15, 30), **5** is the only one in the right order of magnitude — 1 is
too low (there's always more than one span), and 15/30 would imply far more
tool calls than a single FAQ lookup needs.

---

## Question 2 — Tables dlt created

**Answer: 24**

Built `ingest_logfire.py`: a `@dlt.resource` that `POST`s to Logfire's
`/v2/query` endpoint (`SELECT * FROM records`) using `LOGFIRE_READ_TOKEN`,
loaded into DuckDB with `dataset_name="agent_traces"`. Logfire's `attributes`
column carries deeply nested JSON (input/output messages, tool definitions,
token-usage metrics, scrubbed-field paths, etc.) — dlt normalized this into
one main table plus 20 child tables, plus 3 dlt bookkeeping tables:

```sql
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'agent_traces';
-- 24
```

```
records
records__attributes__gen_ai_input_messages
records__attributes__gen_ai_input_messages__parts
records__attributes__gen_ai_input_messages__parts__result
records__attributes__gen_ai_output_messages
records__attributes__gen_ai_output_messages__parts
records__attributes__gen_ai_response_finish_reasons
records__attributes__gen_ai_system_instructions
records__attributes__gen_ai_tool_call_result
records__attributes__gen_ai_tool_definitions
records__attributes__gen_ai_tool_definitions__parameters__required
records__attributes__logfire_metrics__gen_ai_client_token_usage__details
records__attributes__logfire_metrics__operation_cost__details
records__attributes__logfire_scrubbed
records__attributes__logfire_scrubbed__path
records__attributes__model_request_parameters__function_tools
records__attributes__model_request_parameters__function_tools__parameters_json_schema__required
records__attributes__model_request_parameters__instruction_parts
records__attributes__pydantic_ai_all_messages
records__attributes__pydantic_ai_all_messages__parts
records__attributes__pydantic_ai_all_messages__parts__result
_dlt_loads
_dlt_pipeline_state
_dlt_version
```

This matches the "24" option exactly — one of the four choices (1, 3, 24,
100) that isn't a round guess, confirming the pipeline normalized correctly.

---

## Question 3 — Input token usage

**Answer: 1500 - 5000**

The per-call token count lands in a flat column on the main `records` table:
`attributes__gen_ai_usage_input_tokens` (not nested, since it's a scalar OTel
attribute, unlike the message/tool JSON blobs from Q2). Summed across the
`chat gpt-5.4-mini` spans within each Q1 trace:

```sql
SELECT trace_id, SUM(attributes__gen_ai_usage_input_tokens) AS total_input_tokens
FROM agent_traces.records
WHERE attributes__gen_ai_usage_input_tokens IS NOT NULL
GROUP BY 1;
```

```
019f81121fb011679d23988e06eb8b50  4,054  (3 LLM calls)
019f8112ab2904612e6de363156c06d3  4,138  (3 LLM calls)
019f811c406ebdadd94776255351b8cf  1,628  (2 LLM calls)
```

All three runs land inside the **1,500 - 5,000** bucket — consistent with a
small FAQ prompt plus 1-2 rounds of retrieved search results, well short of
the 10k+ buckets that would imply a much larger context (e.g. full-page RAG
like in HW5).

---

## Evidence notes

- Model: `gpt-5.4-mini` via Pydantic AI (`homework/agent.py`, unmodified)
- Observability: Pydantic Logfire (`logfire.configure()` +
  `logfire.instrument_pydantic_ai()`), project `mario-lazo/starter-project`,
  region `us`
- Ingestion: dlt custom resource → DuckDB (`logfire_traces.duckdb`), dataset
  `agent_traces`, pipeline `logfire_traces`
- Query: Logfire `/v2/query` API (`POST https://logfire-us.pydantic.dev/v2/query`,
  bearer `LOGFIRE_READ_TOKEN`, `SELECT * FROM records`)
- 3 runs of the query "How do I run Ollama locally?" produced 16 span rows
  total across 3 traces (6 + 6 + 4)
