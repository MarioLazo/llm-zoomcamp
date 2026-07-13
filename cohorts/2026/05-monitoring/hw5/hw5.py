"""
LLM Zoomcamp 2026 - Homework 5: Monitoring with OpenTelemetry
https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw5

Results:
  Q1: 3 spans (rag, search, llm)
  Q2: 7000 input tokens (actual: 7,111)
  Q3: Over 2000ms (actual: ~4,100ms)
  Q4: rag, search, and llm
  Q5: llm (~4,100ms vs ~0.6ms for search)
  Q6: They are identical (7,111 across all 4 runs)
"""

import sqlite3

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

from gitsource import GithubRepositoryDataReader
from minsearch import Index

from rag_helper import RAGBase

load_dotenv()

COMMIT = "8c1834d"

# ── Custom SQLite span exporter (Q4) ─────────────────────────────────────────

class SQLiteSpanExporter(SpanExporter):

    def __init__(self, db_path="traces.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                name TEXT,
                start_time INTEGER,
                end_time INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost REAL
            )
        """)
        self.conn.commit()

    def export(self, spans):
        for span in spans:
            attrs = dict(span.attributes or {})
            self.conn.execute(
                "INSERT INTO spans VALUES (?, ?, ?, ?, ?, ?)",
                (
                    span.name,
                    span.start_time,
                    span.end_time,
                    attrs.get("input_tokens"),
                    attrs.get("output_tokens"),
                    attrs.get("cost"),
                ),
            )
        self.conn.commit()
        return SpanExportResult.SUCCESS

    def shutdown(self):
        self.conn.close()

    def force_flush(self):
        return True


# ── OTel setup ────────────────────────────────────────────────────────────────

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(SQLiteSpanExporter("traces.db")))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("llm-zoomcamp")


# ── Instrumented RAG subclass ─────────────────────────────────────────────────

class RAGTraced(RAGBase):

    def search(self, query, num_results=5):
        with tracer.start_as_current_span("search"):
            return super().search(query, num_results=num_results)

    def llm(self, prompt):
        with tracer.start_as_current_span("llm") as span:
            response = super().llm(prompt)
            usage = response.usage
            # gpt-5.4-mini pricing: $0.15/1M input, $0.60/1M output
            cost = (usage.input_tokens * 0.15 + usage.output_tokens * 0.60) / 1_000_000
            span.set_attribute("input_tokens", usage.input_tokens)
            span.set_attribute("output_tokens", usage.output_tokens)
            span.set_attribute("cost", cost)
            return response

    def rag(self, query):
        with tracer.start_as_current_span("rag"):
            search_results = self.search(query)
            prompt = self.build_prompt(query, search_results)
            response = self.llm(prompt)
            return response.output_text


# ── Bootstrap ─────────────────────────────────────────────────────────────────

reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id=COMMIT,
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)
documents = [file.parse() for file in reader.read()]

index = Index(text_fields=["content"], keyword_fields=["filename"])
index.fit(documents)

client = OpenAI()
rag = RAGTraced(index=index, llm_client=client)

QUERY = "How does the agentic loop keep calling the model until it stops?"


def run(n=1):
    for i in range(n):
        print(f"\n--- Run {i + 1} ---")
        print(rag.rag(QUERY))


def analyze():
    conn = sqlite3.connect("traces.db")
    df = pd.read_sql("SELECT * FROM spans", conn)
    conn.close()

    df["duration_ms"] = (df["end_time"] - df["start_time"]) / 1_000_000

    print("\n=== All spans ===")
    print(df[["name", "duration_ms", "input_tokens", "output_tokens", "cost"]])

    print("\n=== Unique span names (Q4) ===")
    print(sorted(df["name"].unique()))

    print("\n=== Total duration by span, excluding rag (Q5) ===")
    print(df[df["name"] != "rag"].groupby("name")["duration_ms"].sum().sort_values(ascending=False))

    llm_spans = df[df["name"] == "llm"]
    print("\n=== Input tokens per LLM span (Q6) ===")
    print(llm_spans["input_tokens"].to_string())
    if len(llm_spans) > 1:
        mn, mx = llm_spans["input_tokens"].min(), llm_spans["input_tokens"].max()
        print(f"Variation: {(mx - mn) / mn * 100:.1f}%")


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"

    if mode == "run":
        run(1)
    elif mode == "run4":
        run(4)
    elif mode == "analyze":
        analyze()
