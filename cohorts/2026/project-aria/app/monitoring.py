"""Persist interactions + user feedback to Postgres for the dashboard."""
from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from . import config


def _conn():
    return psycopg.connect(config.POSTGRES_DSN, row_factory=dict_row)


def log_interaction(result: dict) -> int:
    """Store one RAG result; return its interaction id (for feedback linkage)."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO interactions
                (mode, query, rewritten, answer, model, latency_ms,
                 tokens_in, tokens_out, top_score, num_sources)
            VALUES (%(mode)s, %(query)s, %(rewritten)s, %(answer)s, %(model)s,
                    %(latency_ms)s, %(tokens_in)s, %(tokens_out)s,
                    %(top_score)s, %(num_sources)s)
            RETURNING id
            """,
            result,
        )
        return cur.fetchone()["id"]


def log_feedback(interaction_id: int, rating: str, note: str = "") -> None:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO feedback (interaction_id, rating, note) VALUES (%s, %s, %s)",
            (interaction_id, rating, note),
        )


def fetch_interactions(limit: int = 1000):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM interactions ORDER BY ts DESC LIMIT %s", (limit,)
        )
        return cur.fetchall()


def fetch_feedback(limit: int = 1000):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM feedback ORDER BY ts DESC LIMIT %s", (limit,))
        return cur.fetchall()
