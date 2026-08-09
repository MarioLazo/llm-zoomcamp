speaker: Marcus Oyelaran (Head of Cloud Infrastructure, Northfield Mutual Bank)
Interviewer: Describe the hosting architecture for the website and online
banking portal.
Marcus: It's fronted by Cloudflare for CDN and WAF, then traffic hits an
Application Load Balancer in our AWS VPC, TLS-terminated there, forwarded to
an ECS Fargate cluster running the web and portal services. The VPC is
segmented into public, app, and data subnets — nothing in the data subnet is
internet-routable. Database access from the app tier goes through a security
group that only allows the specific ports and source security groups we've
explicitly approved.
Interviewer: How is encryption handled end to end?
Marcus: TLS 1.2+ from the browser to Cloudflare, and again from Cloudflare to
our load balancer — we don't terminate to plaintext at any hop. At rest, RDS
and S3 are encrypted with KMS. Customer session data in Redis is encrypted at
rest too, which is actually stricter than our policy technically requires,
but it was cheap to turn on and it closes an obvious gap.
Interviewer: What's your change management process?
Marcus: Every change to production infrastructure goes through a pull request
against our Terraform repo, requires one peer approval plus a passing policy
check in CI, and gets applied through our deployment pipeline — nobody applies
Terraform from a laptop. Emergency changes have a documented break-glass
process, but it still requires a second engineer's sign-off after the fact,
logged in the incident ticket. That's in the Change Management Policy.
Interviewer: Any known gaps?
Marcus: The break-glass path is sound, but we've only used it twice in the
last year, and one of those times the after-the-fact sign-off happened four
days late instead of the required 24 hours. That's flagged in the gap
assessment. It's not a design gap, it's a discipline gap — we're adding an
automated reminder to close it.
