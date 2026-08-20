# ARIA Demo Scenario: SOC 2 Readiness for a Bank's Website Hosting

The sample corpus in [`data/sample/`](data/sample) is a **single coherent,
entirely fictional** engagement, so ARIA's chat/evidence/briefing modes have
something realistic and specific to work over — not generic, unrelated
interviews.

## Client

**Northfield Mutual Bank** — a simulated regional bank. Northfield, its staff,
and every document in `data/sample/` are fictional, generated for this course
capstone. No real institution, person, or engagement is represented.

## Engagement

SOC 2 Type II **readiness** for the infrastructure hosting Northfield's public
website and online banking portal — preparing control narratives and evidence
ahead of an independent SOC 2 audit. Scope is deliberately narrow (the website
hosting stack, not the core banking system) so the corpus stays focused and
the retrieval/eval queries stay answerable from a small set of documents.

## Trust Services Criteria in scope

| Criterion | In scope? | Why |
|-----------|-----------|-----|
| **Security** (Common Criteria) | ✅ | Mandatory baseline for any SOC 2 report |
| **Availability** | ✅ | Uptime commitments matter directly for a bank's public site |
| **Confidentiality** | ✅ | The hosting environment touches customer data |
| Processing Integrity | ❌ | Applies to core transaction processing, not a hosting-only scope |
| Privacy | ❌ | Typically a separate, broader engagement |

## Personas interviewed (LEkE-style transcripts)

1. **CISO** — overall control environment, risk management, incident response ownership
2. **Head of Cloud Infrastructure** — hosting architecture, encryption, network segmentation, change management
3. **Site Reliability Lead** — availability, monitoring/alerting, incident execution
4. **Vendor Risk Manager** — CDN/hosting provider due diligence, subprocessor oversight
5. **Compliance Program Manager** — evidence collection, control mapping, audit readiness status

## Document set (`data/sample/`)

- 5 interview transcripts (`transcript_0N_*.md`, one per persona above)
- `policy_information_security.md` — Information Security Policy (excerpt)
- `policy_incident_response.md` — Incident Response Policy (excerpt)
- `policy_change_management.md` — Change Management Policy (excerpt)
- `policy_vendor_risk_management.md` — Vendor Risk Management Policy (excerpt)
- `soc2_readiness_gap_assessment.md` — internal gap assessment memo

## Why this scenario exercises ARIA well

- 💬 **Chat**: "What encryption do we use for data in transit to the website?"
- 📌 **Evidence**: "Pull evidence that our incident response plan is tested annually"
- 📋 **Briefing**: "Draft a briefing for the audit committee on SOC 2 readiness status"

Each answer should cite specific transcripts/policies — a good test of whether
retrieval actually grounds the response instead of the model guessing at a
plausible-sounding SOC 2 answer.

## Disclaimer

Everything under `data/sample/` — the bank, personnel, policies, and gap
assessment — is synthetic and fictional, written for this capstone to
demonstrate ARIA without exposing real personal or institutional data. See
[`README.md`](README.md#data--privacy-important) for the privacy design
rationale.

---

# Second engagement: MOU Remediation — Underwriting & Board Reporting

Added post-submission as an extension of the same Northfield Mutual
scenario, demonstrating ARIA against a second, distinct compliance domain
for the same fictional client — regulated banking (safety-and-soundness),
not IT/security compliance.

## Engagement

Northfield Mutual received a Memorandum of Understanding (MOU) from its
state banking regulator and the FDIC after a routine examination — a
binding enforcement action with fixed remediation deadlines and ongoing
quarterly progress reporting. Of the MOU's eight findings, this corpus
covers two in depth:

- **Finding 3 — weak underwriting documentation.** Four loan files
  (`data/sample/underwriting_loan_*.md`) with realistic, naturally-occurring
  documentation gaps — not labeled "MISSING," but genuinely absent, stale,
  or substituted with a documented business rationale, the way a real file
  would be.
- **Finding 8 — governance and reporting weaknesses.** A structured
  remediation tracker, board compliance-committee minutes, and structured
  deadline data (`mou_remediation_tracker.md`, `board_minutes_*.md`,
  `mou_items.json`) that a board report must accurately reflect — including
  items that have slipped past their target date.

## New capability: `underwriting` mode

Given a loan file, ARIA assesses three required documentation elements
(repayment source analysis, cash flow analysis, collateral valuation)
against a fixed checklist, tagging each `PRESENT`, `EXCEPTION`, or
`DOCUMENTED DEVIATION` with a citation. A deterministic checker
(`app/underwriting_check.py`) then verifies the model didn't hallucinate a
citation and didn't contradict its own summary count — the same
citation-integrity discipline `eval/integrity_checks.py` already applies to
`chat` mode, applied here to a structured checklist instead of prose.

## Enhanced capability: `briefing` mode for board reporting

No new mode needed — `briefing` already produces grounded, cited,
multi-section outlines. What's new is a deterministic safety net
(`app/mou_tracker.py`) that reads the structured deadline data independent
of any LLM narrative and checks whether the drafted report actually mentions
every item that's overdue or at-risk — catching the exact failure mode
Finding 8 was issued for (a slipping item silently dropped from a board
report).

## Why this exercises ARIA well

- 🏦 **Underwriting**: "Review the Riverside Construction Group loan file
  for documentation completeness" — should correctly flag the missing
  independent equipment appraisal, distinct from Maple Street Retail's
  documented (and legitimate) absence of a traditional cash flow statement.
- 📋 **Briefing**: "Draft a board update on MOU remediation progress this
  quarter" — should surface the overdue board minute-taking standard and
  the at-risk underwriting exceptions, not just the completed items.

## Evaluation

See [`eval/mou_eval.py`](eval/mou_eval.py) — unlike the retrieval/LLM evals
above, this checks against a *known ground truth* of which element is
deliberately incomplete in each loan file, so it measures whether ARIA finds
the actual planted gaps, not just whether it produces well-formed output.

**Real run, 2026-08-19** (`docker compose exec app python -m eval.mou_eval`,
after fixing the two bugs described below):

| Loan file | Retrieved | Verification clean | Elements correct |
|---|---|---|---|
| Harrow Family Farms | ✅ | ✅ | 3/3 |
| Riverside Construction Group | ✅ | ✅ | 3/3 |
| Maple Street Retail Partners | ✅ | ✅ | 3/3 |
| Dunmore Logistics | ✅ | ✅ | 3/3 |

**Element-level accuracy: 12/12.** Board/regulatory reporting: both flagged
(overdue/at-risk) items were correctly mentioned in the drafted briefing —
`coverage_report()` clean, zero missed.

**Two real bugs found and fixed while building this, not before:**

1. **Query rewriting was dropping borrower names.** "Review the Dunmore
   Logistics loan file" was rewritten into a generic "loan documentation
   checklist" — losing the one word retrieval needed — causing the wrong
   file to be retrieved with high confidence. Different borrowers failed on
   different runs, consistent with the LLM-driven rewrite behaving
   non-deterministically. Fixed by skipping the rewrite step for
   `underwriting` mode entirely: exact-entity lookups don't benefit from
   generalization the way open-ended synthesis questions do.
2. **The deterministic checker's own regex had a line-merging bug.**
   `underwriting_check.py`'s element-parsing regex used `[^:]+` (matches
   any character except a colon, including newlines and mid-word hyphens),
   so a bullet containing something like "trailing 3-year statements"
   could make the regex anchor on that hyphen and greedily consume text
   through the *next* colon — silently merging two checklist lines into
   one and dropping a real element. Fixed by anchoring to line start
   (`^-\s*`, `re.MULTILINE`) and excluding newlines from the element
   capture group (`[^:\n]+`). Caught by the project's first unit tests
   ([`tests/test_underwriting_check.py`](tests/test_underwriting_check.py)),
   which is exactly why they were worth writing.

A subtler lesson underneath both: the app container doesn't live-mount the
source, so host-side edits don't take effect until the image is rebuilt —
several eval runs during development silently tested stale, pre-fix code
without any error to signal it. Both bugs above were real; the first
"12/12" figure was not seen until after a clean rebuild confirmed the fixes
were actually running.
