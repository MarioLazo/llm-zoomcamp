# SOC 2 Readiness Gap Assessment — Northfield Mutual Bank

**Scope:** Website and online banking portal hosting environment.
**Criteria assessed:** Security (Common Criteria), Availability, Confidentiality.
**Prepared by:** Compliance Program Manager, ahead of the SOC 2 Type II
observation period.

## Summary

Control design is sound across all three in-scope criteria. Every control has
a documented owner and narrative. The gaps identified below are evidence and
process-discipline gaps, not control-design failures, and are all scoped for
remediation before the observation period begins.

## Gap 1 — Evidence timestamping is inconsistent

**Finding:** Controls such as access grants and infrastructure changes are
executed correctly, but evidence is not always captured at the moment the
control operates — it is sometimes reconstructed afterward from logs.
**Risk:** An auditor may not accept reconstructed evidence as sufficient for
a Type II examination, which tests operating effectiveness over the
observation period.
**Remediation:** Automated evidence capture hooked into the ticketing system
for access grants and infrastructure changes, timestamped at the moment of
action. Owner: Compliance Program Manager. Target: this quarter.

## Gap 2 — Break-glass change sign-off timing

**Finding:** The break-glass emergency change process requires a second
engineer's sign-off within 24 hours. In one of two break-glass changes in the
past year, sign-off occurred approximately four days late.
**Risk:** A control exception during the observation period would be noted by
the auditor as a deviation from the documented control.
**Remediation:** Automated reminder (Slack bot) triggered at break-glass
change time, escalating if sign-off is not recorded within the 24-hour
window. Owner: Head of Cloud Infrastructure. Target: this quarter.

## Gap 3 — No automated vendor SOC 2 report expiration tracking

**Finding:** Vendor SOC 2 report expiration is tracked via a manual calendar
reminder rather than an automated alert tied to the vendor risk register.
**Risk:** A missed manual reminder could result in an expired vendor report
going unnoticed until the annual review, outside the intended review cadence.
**Remediation:** Calendar automation tied to the vendor register, alerting
the Vendor Risk Manager 30 days before any in-scope vendor's SOC 2 report
expires. Owner: Vendor Risk Manager. Target: this quarter.

## Strong evidence areas (no action needed)

- Quarterly automated disaster-recovery restore testing, with self-logging
  results — one of the strongest pieces of evidence in the current program.
- Twice-yearly incident response tabletop exercises with retained notes and
  action items.
- Encryption in transit and at rest, consistently enforced and documented in
  the Information Security Policy.

## Next steps

All three gaps are scoped for closure this quarter, ahead of the SOC 2 Type
II observation period start. No control redesign is required — this is
process discipline and automation work layered on top of controls that
already operate correctly.
