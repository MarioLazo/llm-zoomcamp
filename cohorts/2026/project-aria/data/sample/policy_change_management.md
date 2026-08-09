# Change Management Policy (Excerpt) — Northfield Mutual Bank

**Scope:** Applies to all infrastructure and application changes to the
website and online banking portal hosting environment.

## 1. Standard Change Process

All infrastructure changes are made via pull request against the
infrastructure-as-code repository. Every change requires:

- At least one peer approval from a qualified reviewer.
- A passing automated policy check in the CI pipeline (security, cost,
  compliance rules).
- Application through the automated deployment pipeline — direct manual
  application to production is prohibited under standard process.

## 2. Emergency (Break-Glass) Changes

When a production incident requires an immediate change that cannot wait for
standard review, an engineer may apply a break-glass change. Break-glass
changes require:

- The change to be logged in the active incident ticket at the time it is
  made.
- A second engineer's documented sign-off on the change **within 24 hours**
  of application.
- A retrospective pull request capturing the change in infrastructure-as-code
  within one business day.

## 3. Application Deployments

Application deployments follow a staged rollout: a canary deployment to a
small percentage of traffic, automated health-check validation, then full
rollout. Failed health checks automatically roll back the deployment.

## 4. Evidence Retention

Every change — standard or emergency — is retained in the deployment
pipeline's audit log for a minimum of 13 months, including the approver,
timestamp, and change contents.
