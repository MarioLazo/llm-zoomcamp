"""Evaluation for the two new MOU-response capabilities: underwriting
documentation exception tracking, and board/regulatory reporting deadline
coverage.

Unlike eval/retrieval_eval.py and eval/llm_eval.py, this checks against a
KNOWN ground truth of which documentation elements were deliberately left
incomplete in each loan file (see data/sample/underwriting_loan_*.md) — so
this isn't just "did the model produce well-formed output," it's "did the
model correctly find the actual gaps a human underwriting reviewer planted."

Run after ingestion:  python -m eval.mou_eval
"""
from __future__ import annotations

from app.mou_tracker import coverage_report
from app.rag import RAG
from app.underwriting_check import verify

# Ground truth: which element is NOT clean in each file, and how.
# "present" means the model should tag it PRESENT; anything else is the
# element this file was specifically constructed to test.
UNDERWRITING_CASES = [
    {
        "borrower": "Harrow Family Farms",
        "file": "underwriting_loan_harrow_family_farms.md",
        "expected": {
            "Repayment Source Analysis": "PRESENT",
            "Cash Flow Analysis": "PRESENT",
            "Collateral Valuation": "PRESENT",
        },
    },
    {
        "borrower": "Riverside Construction Group",
        "file": "underwriting_loan_riverside_construction.md",
        "expected": {
            "Repayment Source Analysis": "PRESENT",
            "Cash Flow Analysis": "EXCEPTION",
            "Collateral Valuation": "EXCEPTION",
        },
    },
    {
        "borrower": "Maple Street Retail Partners",
        "file": "underwriting_loan_maple_street_retail.md",
        "expected": {
            "Repayment Source Analysis": "PRESENT",
            "Cash Flow Analysis": "DOCUMENTED DEVIATION",
            "Collateral Valuation": "PRESENT",
        },
    },
    {
        "borrower": "Dunmore Logistics",
        "file": "underwriting_loan_dunmore_logistics.md",
        "expected": {
            "Repayment Source Analysis": "EXCEPTION",
            "Cash Flow Analysis": "PRESENT",
            "Collateral Valuation": "PRESENT",
        },
    },
]

BRIEFING_QUERY = "Draft a board update on MOU remediation progress this quarter."


def run_underwriting_eval(rag: RAG) -> list[dict]:
    results = []
    for case in UNDERWRITING_CASES:
        query = f"Review the {case['borrower']} loan file for documentation completeness."
        result = rag.answer(query, mode="underwriting")
        retrieved = {s["source"] for s in result["sources"]}
        report = verify(result["answer"], retrieved)

        # directional accuracy: PRESENT vs not-PRESENT, per element, against
        # the model's own parsed rows (not just "did it look well-formed")
        parsed = {row["element"]: row["status"] for row in report["rows"]}
        correct = 0
        for element, expected_status in case["expected"].items():
            got = parsed.get(element)
            if expected_status == "PRESENT":
                correct += int(got == "PRESENT")
            else:
                correct += int(got is not None and got != "PRESENT")

        results.append(
            {
                "borrower": case["borrower"],
                "file_retrieved": case["file"] in retrieved,
                "verification_clean": report["clean"],
                "elements_correct": f"{correct}/3",
                "uncited_claims": len(report["uncited_claims"]),
                "summary_consistent": report["summary_consistent"],
                "raw_answer": result["answer"],
            }
        )
    return results


def run_briefing_eval(rag: RAG) -> dict:
    result = rag.answer(BRIEFING_QUERY, mode="briefing")
    coverage = coverage_report(result["answer"])
    return {
        "flagged_items": coverage["flagged_count"],
        "missed_items": [m["id"] for m in coverage["missed"]],
        "coverage_clean": coverage["clean"],
        "raw_answer": result["answer"],
    }


if __name__ == "__main__":
    rag = RAG()

    print("=== Underwriting exception tracking (4 loan files, known ground truth) ===")
    uw_results = run_underwriting_eval(rag)
    for r in uw_results:
        print(
            f"  {r['borrower']:<32} retrieved={r['file_retrieved']!s:<5} "
            f"clean={r['verification_clean']!s:<5} elements_correct={r['elements_correct']} "
            f"uncited={r['uncited_claims']} summary_ok={r['summary_consistent']}"
        )
    total_correct = sum(int(r["elements_correct"].split("/")[0]) for r in uw_results)
    print(f"\n  Element-level accuracy: {total_correct}/{3 * len(UNDERWRITING_CASES)}")

    print("\n=== Board/regulatory reporting deadline coverage ===")
    b_result = run_briefing_eval(rag)
    print(f"  Flagged items (overdue/at-risk): {b_result['flagged_items']}")
    print(f"  Missed in briefing: {b_result['missed_items'] or 'none'}")
    print(f"  Coverage clean: {b_result['coverage_clean']}")
