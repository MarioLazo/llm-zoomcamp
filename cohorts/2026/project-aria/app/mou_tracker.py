"""Deterministic deadline tracking for MOU remediation items.

Reads the structured mou_items.json (owner, target date, status) and
identifies what must be flagged, independent of any LLM narrative. Used to
cross-check a `briefing`-mode answer: did the drafted board report actually
mention every item that's overdue or at-risk, or did something slip through
silently — the exact governance failure Finding 8 in mou_summary.md was
issued for.
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data" / "sample" / "mou_items.json"

FLAGGED_STATUSES = {"overdue", "at_risk"}


def load_items(path: Path | str = DEFAULT_PATH) -> list[dict]:
    return json.loads(Path(path).read_text())


def flagged_items(items: list[dict]) -> list[dict]:
    """Items whose recorded status is overdue or at-risk — the ones a board
    report must not silently omit."""
    return [item for item in items if item["status"] in FLAGGED_STATUSES]


def coverage_report(answer: str, items: list[dict] | None = None) -> dict:
    """Check whether a briefing-mode answer mentions every flagged item.

    A flagged item counts as "mentioned" if a distinctive word from its
    description appears in the answer — a blunt substring check on purpose:
    this is meant to catch the failure mode where an overdue item never
    appears anywhere in the report at all, not to judge how well it's
    covered.
    """
    items = items if items is not None else load_items()
    flagged = flagged_items(items)
    answer_lower = answer.lower()

    missed = []
    for item in flagged:
        keywords = [w.strip(",.") for w in item["item"].lower().split() if len(w) > 4]
        hit = any(kw in answer_lower for kw in keywords)
        if not hit:
            missed.append(item)

    return {
        "flagged_count": len(flagged),
        "missed": missed,
        "clean": not missed,
    }


if __name__ == "__main__":
    items = load_items()
    flagged = flagged_items(items)
    print(f"{len(flagged)} flagged item(s) (overdue/at-risk):")
    for item in flagged:
        print(f"  [{item['status']}] {item['item']} (target {item['target_date']}, owner {item['owner']})")
