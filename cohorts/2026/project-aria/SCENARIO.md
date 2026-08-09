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
