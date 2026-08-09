speaker: Priya Ramaswamy (Site Reliability Lead, Northfield Mutual Bank)
Interviewer: What availability commitments do you carry for the website and
online banking portal?
Priya: We commit to 99.9% monthly uptime for the portal, a bit looser for the
marketing website since it's not transaction-critical. We run across two
availability zones with auto-scaling on the ECS service, and Route 53 health
checks that fail over the DNS if a whole AZ goes unhealthy. We've held that
99.9% for the last four quarters straight.
Interviewer: How do you detect and respond to incidents?
Priya: Datadog for metrics and synthetic checks, PagerDuty for on-call
routing. Anything that trips a customer-facing threshold — elevated error
rate, latency, failed health checks — pages the on-call SRE within two
minutes. From there we follow the incident response plan Dana's team owns:
severity rating, incident commander, status page update if it's customer
visible.
Interviewer: Do you test the incident response plan itself, not just
individual incidents?
Priya: Yes, twice a year we run a tabletop exercise with a simulated scenario
— last one was a simulated AZ failure combined with a bad deploy, to test
whether people follow the runbook under pressure instead of improvising. We
keep the exercise notes and the post-exercise action items as evidence.
Interviewer: What's your backup and recovery posture?
Priya: RDS automated backups with a 35-day retention, point-in-time recovery
enabled. We test a full restore into a scratch environment quarterly — that's
actually one of our stronger pieces of evidence, because it's fully automated
and logs its own results. RTO target is four hours, RPO is fifteen minutes
given the backup frequency, and we've met both in every quarterly test this
year.
