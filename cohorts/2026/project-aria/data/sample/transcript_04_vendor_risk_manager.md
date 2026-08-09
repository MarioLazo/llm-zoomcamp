speaker: Elias Whitcombe (Vendor Risk Manager, Northfield Mutual Bank)
Interviewer: Which third parties sit in scope for the website hosting
engagement?
Elias: Three subprocessors matter here: AWS as the cloud hosting provider,
Cloudflare for CDN and WAF, and Datadog for monitoring. All three touch
either infrastructure or telemetry for the in-scope systems, so all three are
in our vendor risk register for this engagement.
Interviewer: What does due diligence look like for a vendor like that?
Elias: Before onboarding, we require their most recent SOC 2 Type II report,
review the exceptions section specifically — not just whether they got a
report, but what got flagged and how they remediated it. We reassess annually,
and any material change on their end, like a subprocessor change or a
security incident disclosure, triggers an off-cycle review.
Interviewer: Have any of the three raised concerns?
Elias: Cloudflare disclosed a minor incident last year — a config error that
briefly affected a small percentage of customers globally, not us
specifically. We reviewed their post-incident report, confirmed it didn't
touch our traffic, and documented that review. That's actually a decent piece
of evidence for the audit — it shows the vendor monitoring process working,
not just existing on paper.
Interviewer: How do you track ongoing vendor obligations?
Elias: Each vendor has a one-page risk profile: data they can access, their
last SOC 2 report date, contractual security requirements, and next review
date. I own the vendor register and it's reviewed in our quarterly risk
committee meeting. The gap assessment noted we don't yet have automated
alerting when a vendor's SOC 2 report expires — that's still a manual
calendar reminder today, which is the one piece of this I'd like tightened up
before the audit.
