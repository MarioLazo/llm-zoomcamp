# Vendor Risk Management Policy (Excerpt) — Northfield Mutual Bank

**Scope:** Applies to third-party subprocessors with access to the website
and online banking portal hosting environment or its data.

## 1. Vendor Onboarding

Before onboarding, a vendor with access to in-scope systems or data must
provide its most recent SOC 2 Type II report (or equivalent). The exceptions
and complementary user entity controls sections are reviewed specifically,
not just the report's existence.

## 2. Ongoing Review

Each in-scope vendor is reassessed annually. An off-cycle review is triggered
immediately upon:

- A change in the vendor's subprocessors.
- A security incident disclosure from the vendor, regardless of whether
  Northfield's data or traffic was affected.
- A material change in the services the vendor provides.

## 3. Vendor Risk Register

Each vendor in scope has a documented risk profile including: data or systems
the vendor can access, the date of their most recent SOC 2 report, contractual
security requirements, and the date of the next scheduled review. The
register is reviewed at the quarterly risk committee meeting.

## 4. Current In-Scope Vendors (Website Hosting)

| Vendor | Role | Data/Access |
|--------|------|--------------|
| AWS | Cloud hosting infrastructure | Full infrastructure |
| Cloudflare | CDN and WAF | Network traffic (edge) |
| Datadog | Monitoring and alerting | Telemetry, logs |

## 5. Incident Disclosure Handling

When a vendor discloses a security incident, the Vendor Risk Manager reviews
the vendor's post-incident report, determines whether Northfield's systems or
traffic were affected, and documents the determination — whether or not
Northfield was impacted.
