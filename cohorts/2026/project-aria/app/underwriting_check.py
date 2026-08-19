"""Deterministic verification for the `underwriting` mode's structured output.

The underwriting-mode answer follows a strict per-line format (see
MODE_SYSTEM["underwriting"] in app/rag.py): one line per required element
tagged PRESENT / EXCEPTION / DOCUMENTED DEVIATION, plus a summary line. This
parses that format and checks two things a "trust the model" read can't:

  1. Does every citation on a PRESENT/DOCUMENTED DEVIATION line actually
     resolve to a source that was retrieved — the same class of check
     eval/integrity_checks.py already runs for chat-mode citations, applied
     here to a structured checklist instead of free-text prose.
  2. Does the model's own "X of 3 ... Y exception(s) ... Z documented
     deviation(s)" summary line match what it reported line by line, or did
     it contradict its own count.
"""
from __future__ import annotations

import re

REQUIRED_ELEMENTS = ("Repayment Source Analysis", "Cash Flow Analysis", "Collateral Valuation")

LINE_RE = re.compile(
    r"^-\s*(?P<element>[^:\n]+):\s*(?P<status>PRESENT|EXCEPTION|DOCUMENTED DEVIATION)"
    r"(?:\s*\[(?P<citation>[\w\-.]+\.md)\])?",
    re.IGNORECASE | re.MULTILINE,
)
SUMMARY_RE = re.compile(
    r"Overall:\s*(?P<present>\d+)\s*of\s*3\s*elements documented,\s*"
    r"(?P<exceptions>\d+)\s*exception\(?s?\)?,\s*"
    r"(?P<deviations>\d+)\s*documented deviation\(?s?\)?",
    re.IGNORECASE,
)


def parse(answer: str) -> list[dict]:
    """Extract the per-element checklist lines from an underwriting-mode answer."""
    rows = []
    for match in LINE_RE.finditer(answer):
        rows.append(
            {
                "element": match.group("element").strip(),
                "status": match.group("status").upper(),
                "citation": match.group("citation"),
            }
        )
    return rows


def verify(answer: str, retrieved_sources: set[str]) -> dict:
    """Verify an underwriting-mode answer against what was actually retrieved.

    Returns the parsed checklist, any required element the model never
    addressed, any PRESENT/DOCUMENTED DEVIATION claim whose citation was
    never actually retrieved (a hallucinated citation), and whether the
    model's own summary line is internally consistent with its own rows.
    """
    rows = parse(answer)
    covered = {row["element"] for row in rows}
    missing_elements = [e for e in REQUIRED_ELEMENTS if e not in covered]

    uncited_claims = [
        row
        for row in rows
        if row["status"] in ("PRESENT", "DOCUMENTED DEVIATION")
        and (row["citation"] is None or row["citation"] not in retrieved_sources)
    ]

    counts = {"PRESENT": 0, "EXCEPTION": 0, "DOCUMENTED DEVIATION": 0}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    summary_match = SUMMARY_RE.search(answer)
    summary_consistent = None
    if summary_match:
        summary_consistent = (
            int(summary_match.group("present")) == counts["PRESENT"]
            and int(summary_match.group("exceptions")) == counts["EXCEPTION"]
            and int(summary_match.group("deviations")) == counts["DOCUMENTED DEVIATION"]
        )

    return {
        "rows": rows,
        "missing_elements": missing_elements,
        "uncited_claims": uncited_claims,
        "counts": counts,
        "summary_found": summary_match is not None,
        "summary_consistent": summary_consistent,
        "clean": not missing_elements and not uncited_claims and summary_consistent is True,
    }
