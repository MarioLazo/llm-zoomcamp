"""dlt pipeline: Pydantic Logfire traces -> DuckDB (Q2).

Logfire's query API (https://pydantic.dev/docs/logfire/manage/query-api/) is a
POST endpoint that runs a SQL query against the `records` table (one row per
span/log) and returns JSON rows under `data`. It doesn't fit dlt's declarative
REST API source (built for GET + query-param pagination), so this is a plain
`@dlt.resource` generator that calls the endpoint directly and lets dlt handle
schema inference/normalization on the way into DuckDB.

Requires LOGFIRE_READ_TOKEN in .env (generated in Question 2 of the homework).
Set LOGFIRE_REGION=eu in .env if your Logfire project is hosted in the EU
(default is "us"); check the region in your Logfire project URL.
"""

import os
from datetime import datetime, timedelta, timezone

import dlt
import requests
from dotenv import load_dotenv

load_dotenv()


def _base_url():
    region = os.environ.get("LOGFIRE_REGION", "us")
    return f"https://logfire-{region}.pydantic.dev"


@dlt.resource(name="records", write_disposition="replace")
def logfire_records(lookback_hours: int = 24, limit: int = 10_000):
    token = os.environ["LOGFIRE_READ_TOKEN"]
    min_timestamp = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).isoformat()

    response = requests.post(
        f"{_base_url()}/v2/query",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        json={
            "sql": "SELECT * FROM records ORDER BY start_timestamp DESC",
            "min_timestamp": min_timestamp,
            "limit": limit,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    yield from payload["data"]


def load(lookback_hours: int = 24):
    pipeline = dlt.pipeline(
        pipeline_name="logfire_traces",
        destination="duckdb",
        dataset_name="agent_traces",  # matches the schema name the homework SQL checks
    )
    info = pipeline.run(logfire_records(lookback_hours=lookback_hours))
    print(info)
    print(pipeline.last_trace.last_normalize_info)


if __name__ == "__main__":
    import sys

    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    load(hours)
