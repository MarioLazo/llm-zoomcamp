speaker: Sofia Marchetti (Compliance Program Manager, Northfield Mutual Bank)
Interviewer: You're running point on SOC 2 readiness overall. Where does the
program stand?
Sofia: We're roughly ten weeks from the start of the observation period. Every
control has an owner and a documented narrative — that part's done. What's
still in progress is wiring up consistent, timestamped evidence collection so
we're not scrambling to reconstruct it after the fact. That's the theme
across almost every interview I've run for this readiness effort.
Interviewer: How do you map interviews and policies to actual controls?
Sofia: I keep a control matrix mapping each Trust Services Criterion —
Security, Availability, Confidentiality for this engagement — to the specific
policy section and the person who owns the evidence. For example, encryption
in transit maps to the Information Security Policy, section 3, and Marcus's
team owns the evidence: TLS configuration exports and the Cloudflare
dashboard settings.
Interviewer: What did the gap assessment surface as the top risks before the
audit?
Sofia: Three things. One, evidence timestamping — controls exist but aren't
always captured the moment they happen. Two, the break-glass change sign-off
that slipped past 24 hours once. Three, no automated alert for vendor SOC 2
report expiration. None of these are control failures, they're evidence and
process discipline gaps, which is actually the easier category to fix before
an audit.
Interviewer: What's the plan to close them?
Sofia: Automated evidence capture hooked into our ticketing system for access
grants and changes, a Slack reminder bot for the break-glass sign-off window,
and a calendar automation tied to the vendor register for SOC 2 report
expiration. All three are scoped for this quarter, well ahead of the
observation period start.
