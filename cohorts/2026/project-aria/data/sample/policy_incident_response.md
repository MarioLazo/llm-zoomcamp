# Incident Response Policy (Excerpt) — Northfield Mutual Bank

**Scope:** Applies to the website and online banking portal hosting
environment, jointly owned by the CISO and the Site Reliability team.

## 1. Detection

Customer-facing systems are monitored continuously. Any event that trips a
defined threshold — elevated error rate, degraded latency, failed health
checks, or a security alert — automatically pages the on-call engineer within
two minutes of detection.

## 2. Severity Classification

Every incident is assigned a severity level (SEV1–SEV4) based on customer
impact and data exposure risk. SEV1 and SEV2 incidents require an assigned
incident commander and trigger the full response process below; SEV3/SEV4 are
handled by the on-call engineer with a lighter-weight record.

## 3. Response Process

1. Incident commander assigned and incident channel opened.
2. Customer-facing status page updated if the incident is customer-visible.
3. Mitigation actions taken and logged in real time in the incident ticket.
4. Incident declared resolved once customer impact ends.

## 4. Post-Incident Review

Every SEV1/SEV2 incident receives a post-incident review within five business
days of resolution, documenting root cause, timeline, and corrective actions.
Corrective actions are tracked to closure.

## 5. Plan Testing

The incident response plan is tested via a tabletop exercise at least twice
per year, using a simulated scenario not previously exercised. Exercise notes
and resulting action items are retained as evidence of plan effectiveness.
