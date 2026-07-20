# dlt + Logfire homework — solution

`agent.py` and `ingest.py` are unchanged from [../homework/](../homework/) —
only `main.py` needed edits for instrumentation.

- **`main.py`** (Q1) — adds `logfire.configure()` +
  `logfire.instrument_pydantic_ai()` before the agent runs, and takes the
  question as a CLI arg (defaults to the Q1 query, "How do I run Ollama
  locally?").
- **`ingest_logfire.py`** (Q2) — a dlt resource that POSTs to Logfire's
  `/v2/query` endpoint (`SELECT * FROM records`) and loads the result into
  DuckDB (`logfire_traces.duckdb`, dataset `agent_traces`).
- **`query_tokens.py`** (Q3) — sums the `gen_ai.usage.input_tokens` column
  across the LLM-call spans of one trace.

## Running it

Copy `agent.py` and `ingest.py` from `../homework/` alongside these files (or
symlink them), install deps (`openai`, `minsearch`, `requests`,
`python-dotenv`, `pydantic-ai`, `logfire`, `dlt[duckdb]`), fill in `.env` from
`.env.example`, then:

```bash
# Q1
uv run python main.py "How do I run Ollama locally?"
# check span count for this run in the Logfire UI

# Q2
uv run python ingest_logfire.py
# then: SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'agent_traces';

# Q3
uv run python query_tokens.py <trace_id from the Q1 run>
```

See [../../dlt_homework_answers.md](../dlt_homework_answers.md) for the
observed results.
