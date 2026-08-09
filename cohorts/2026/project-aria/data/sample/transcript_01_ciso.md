speaker: Dana Whitfield (CISO, Northfield Mutual Bank)
Interviewer: We're scoping SOC 2 readiness for the website and online banking
portal hosting environment. Walk me through how you own security for that
scope.
Dana: The hosting environment sits in our AWS account, isolated from the core
banking network by design — there's no direct path from the public website
tier into transaction-processing systems. I own the overall control
environment: access control, encryption standards, and incident response for
anything customer-facing. Every engineer with production access goes through
quarterly access review, and we enforce MFA and just-in-time elevation for any
admin action, no standing admin credentials.
Interviewer: What's your biggest concern going into the audit?
Dana: Honestly, evidence consistency. Our controls are real and they work, but
we haven't always been disciplined about capturing evidence at the moment
something happens — a patch, an access grant, an incident. The gap assessment
flagged that, and it's the one thing I'm pushing the team hardest on before
the observation period starts.
Interviewer: How do you handle encryption?
Dana: TLS 1.2 minimum, enforced at the load balancer, for anything in transit
to the website or portal. At rest, everything in the hosting account is
encrypted with AWS KMS-managed keys, and we rotate those keys annually. That's
documented in the Information Security Policy, section on data protection.
Interviewer: And incident response?
Dana: We have a documented plan, owned jointly with the SRE team. I'll let
them speak to execution, but from my seat: every incident gets a severity
rating, a named incident commander, and a post-incident review within five
business days. We tabletop the plan twice a year — that's a control we can
actually evidence cleanly, unlike some of the ad hoc stuff.
