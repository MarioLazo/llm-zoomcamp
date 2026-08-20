"""Unit tests for app/underwriting_check.py — pure functions, no API key or
Qdrant needed. These are the first tests this project has, deliberately for
the deterministic verification layer: the part that has to be provably
correct, not just plausible-looking.
"""
from app.underwriting_check import parse, verify

CLEAN_ANSWER = """- Repayment Source Analysis: PRESENT [loan.md] — verified capacity/coverage
- Cash Flow Analysis: EXCEPTION — reconciliation not received
- Collateral Valuation: PRESENT [loan.md] — independent appraisal on file
Overall: 2 of 3 elements documented, 1 exception(s), 0 documented deviation(s)."""

DEVIATION_ANSWER = """- Repayment Source Analysis: PRESENT [loan.md] — lease income verified
- Cash Flow Analysis: DOCUMENTED DEVIATION [loan.md] — single-purpose leasing entity, rationale on file
- Collateral Valuation: PRESENT [loan.md] — appraisal on file
Overall: 2 of 3 elements documented, 0 exception(s), 1 documented deviation(s)."""

HALLUCINATED_CITATION = """- Repayment Source Analysis: PRESENT [nonexistent.md] — looks fine
- Cash Flow Analysis: EXCEPTION — missing
- Collateral Valuation: EXCEPTION — missing
Overall: 1 of 3 elements documented, 2 exception(s), 0 documented deviation(s)."""

INCONSISTENT_SUMMARY = """- Repayment Source Analysis: PRESENT [loan.md] — fine
- Cash Flow Analysis: EXCEPTION — missing
- Collateral Valuation: EXCEPTION — missing
Overall: 2 of 3 elements documented, 1 exception(s), 0 documented deviation(s)."""

MISSING_ELEMENT = """- Repayment Source Analysis: PRESENT [loan.md] — fine
- Cash Flow Analysis: PRESENT [loan.md] — fine
Overall: 2 of 3 elements documented, 0 exception(s), 0 documented deviation(s)."""


def test_parse_extracts_all_three_elements_in_order():
    rows = parse(CLEAN_ANSWER)
    assert [r["element"] for r in rows] == [
        "Repayment Source Analysis",
        "Cash Flow Analysis",
        "Collateral Valuation",
    ]
    assert [r["status"] for r in rows] == ["PRESENT", "EXCEPTION", "PRESENT"]


def test_parse_does_not_merge_lines_across_mid_word_hyphens():
    # Regression test: an earlier version of LINE_RE used `[^:]+` without
    # excluding newlines, so a mid-word hyphen (e.g. "3-year") anywhere in a
    # bullet's free text could make the regex greedily consume everything up
    # to the *next* colon, silently merging two checklist lines into one and
    # dropping the real "Collateral Valuation" row entirely.
    answer = (
        "- Repayment Source Analysis: PRESENT [loan.md] — fine\n"
        "- Cash Flow Analysis: PRESENT [loan.md] — trailing 3-year statements reviewed\n"
        "- Collateral Valuation: PRESENT [loan.md] — appraisal dated 2025-11-02\n"
        "Overall: 3 of 3 elements documented, 0 exception(s), 0 documented deviation(s)."
    )
    rows = parse(answer)
    assert len(rows) == 3
    assert rows[2]["element"] == "Collateral Valuation"


def test_verify_clean_answer_with_valid_citations():
    report = verify(CLEAN_ANSWER, {"loan.md"})
    assert report["clean"] is True
    assert report["missing_elements"] == []
    assert report["uncited_claims"] == []
    assert report["summary_consistent"] is True


def test_verify_recognizes_documented_deviation_as_a_distinct_status():
    report = verify(DEVIATION_ANSWER, {"loan.md"})
    assert report["counts"]["DOCUMENTED DEVIATION"] == 1
    assert report["clean"] is True


def test_verify_catches_a_hallucinated_citation():
    report = verify(HALLUCINATED_CITATION, {"loan.md"})
    assert report["clean"] is False
    assert len(report["uncited_claims"]) == 1
    assert report["uncited_claims"][0]["citation"] == "nonexistent.md"


def test_verify_catches_a_self_contradicting_summary():
    # The model's own text says "2 of 3" but only reports 1 PRESENT row.
    report = verify(INCONSISTENT_SUMMARY, {"loan.md"})
    assert report["summary_consistent"] is False
    assert report["counts"]["PRESENT"] == 1
    assert report["clean"] is False


def test_verify_catches_a_missing_required_element():
    report = verify(MISSING_ELEMENT, {"loan.md"})
    assert "Collateral Valuation" in report["missing_elements"]
    assert report["clean"] is False


def test_verify_treats_empty_answer_as_missing_everything():
    report = verify("", set())
    assert report["clean"] is False
    assert len(report["missing_elements"]) == 3
