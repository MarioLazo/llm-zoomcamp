"""Unit tests for app/mou_tracker.py — pure functions over the bundled
mou_items.json, no API key or Qdrant needed.
"""
from app.mou_tracker import coverage_report, flagged_items, load_items

ITEMS = [
    {"id": "A", "item": "Adopt revised checklist", "status": "complete", "target_date": "2026-07-01", "owner": "x"},
    {"id": "B", "item": "Remediate documentation exceptions", "status": "at_risk", "target_date": "2026-08-15", "owner": "x"},
    {"id": "C", "item": "Formalize board minute-taking standard", "status": "overdue", "target_date": "2026-08-01", "owner": "x"},
    {"id": "D", "item": "First quarterly progress report", "status": "not_yet_due", "target_date": "2026-09-30", "owner": "x"},
]


def test_flagged_items_returns_only_overdue_and_at_risk():
    flagged = flagged_items(ITEMS)
    assert {i["id"] for i in flagged} == {"B", "C"}


def test_flagged_items_excludes_complete_and_not_yet_due():
    flagged = flagged_items(ITEMS)
    ids = {i["id"] for i in flagged}
    assert "A" not in ids
    assert "D" not in ids


def test_coverage_report_passes_when_every_flagged_item_is_mentioned():
    answer = (
        "Documentation exceptions remain at risk pending the Riverside appraisal. "
        "The board minute-taking standard is overdue and needs formal approval."
    )
    report = coverage_report(answer, ITEMS)
    assert report["clean"] is True
    assert report["missed"] == []


def test_coverage_report_catches_a_silently_dropped_flagged_item():
    # Only mentions the at-risk item, silently omits the overdue one -
    # exactly the governance failure this module exists to catch.
    answer = "Documentation exceptions remain at risk. Everything else is on track."
    report = coverage_report(answer, ITEMS)
    assert report["clean"] is False
    assert [m["id"] for m in report["missed"]] == ["C"]


def test_coverage_report_catches_a_report_that_claims_no_issues():
    answer = "All remediation items are progressing well this quarter, no concerns."
    report = coverage_report(answer, ITEMS)
    assert report["clean"] is False
    assert len(report["missed"]) == 2


def test_load_items_reads_the_real_bundled_data():
    items = load_items()
    assert len(items) > 0
    assert all({"id", "item", "status", "target_date", "owner"} <= set(i.keys()) for i in items)
