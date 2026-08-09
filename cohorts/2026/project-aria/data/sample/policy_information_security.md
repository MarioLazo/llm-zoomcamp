# Information Security Policy (Excerpt) — Northfield Mutual Bank

**Scope:** This excerpt covers sections relevant to the website and online
banking portal hosting environment, in scope for the SOC 2 Type II
examination (Security, Availability, Confidentiality).

## 1. Access Control

All production access requires multi-factor authentication. Standing
administrative credentials are prohibited; administrative access is granted
through just-in-time elevation, logged, and automatically expires after four
hours. Access to production systems is reviewed quarterly by the resource
owner and revoked within one business day for any employee who changes role
or leaves the company.

## 2. Network Segmentation

The hosting environment is deployed in a dedicated AWS VPC with public, app,
and data subnet tiers. The data tier is not internet-routable. No direct
network path exists between the website/portal hosting environment and the
core banking transaction-processing network.

## 3. Data Protection (Encryption)

- **In transit:** TLS 1.2 or higher is enforced at every network hop between
  the client and the application tier, including at the CDN edge and the
  load balancer. No hop terminates to plaintext.
- **At rest:** All storage in the hosting environment (databases, object
  storage, cache) is encrypted using AWS KMS-managed keys. Keys are rotated
  at least annually.

## 4. Vulnerability Management

Production container images are scanned for known vulnerabilities on every
build. Critical and high-severity findings block deployment until remediated
or formally risk-accepted by the CISO.

## 5. Logging and Monitoring

All access to production systems, and all changes to infrastructure
configuration, are logged to a centralized, tamper-evident log store with a
minimum 13-month retention.
