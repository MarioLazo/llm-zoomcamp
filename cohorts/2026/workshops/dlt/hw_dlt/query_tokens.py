"""Q3: sum gen_ai.usage.input_tokens across the LLM-call spans of one trace.

Usage:
    uv run python query_tokens.py             # most recent trace
    uv run python query_tokens.py <trace_id>  # a specific trace

The exact flattened column name for `attributes["gen_ai.usage.input_tokens"]`
depends on how dlt sanitizes the nested key, so this looks it up from
information_schema instead of hardcoding it.
"""

import sys

import duckdb


def find_token_column(con):
    rows = con.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'agent_traces'
          AND table_name = 'records'
          AND column_name ILIKE '%input_tokens%'
        """
    ).fetchall()
    if not rows:
        raise SystemExit(
            "No input_tokens column found under agent_traces.records. "
            "Run: DESCRIBE agent_traces.records; to see actual column names."
        )
    names = [r[0] for r in rows]
    # Prefer the plain per-call metric over aggregated/cache-read variants,
    # which also match the ILIKE pattern above.
    for name in names:
        if name == "attributes__gen_ai_usage_input_tokens":
            return name
    return names[0]


def main(trace_id=None):
    con = duckdb.connect("logfire_traces.duckdb")
    token_col = find_token_column(con)

    if trace_id is None:
        trace_id = con.execute(
            "SELECT trace_id FROM agent_traces.records ORDER BY start_timestamp DESC LIMIT 1"
        ).fetchone()[0]

    total = con.execute(
        f'SELECT SUM("{token_col}") FROM agent_traces.records WHERE trace_id = ?',
        [trace_id],
    ).fetchone()[0]

    print(f"trace_id: {trace_id}")
    print(f"token column: {token_col}")
    print(f"total input tokens: {total}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
