# PRD Create Contract

Choose one profile. Never emit both.

## Compact

Use when the user explicitly asks for a concise, brief, or MVP PRD. Start with
the exact marker so the validator applies the smaller contract:

```markdown
<!-- wigtn-prd-profile: compact -->
# <Feature> PRD
## Problem and scope
## Goals and non-goals
## Users, roles, authorization, and data boundaries
## Functional requirements
| ID | Requirement | Priority |
## Acceptance criteria
| ID | Requirement | Given | When | Then | Verification |
## Assumptions and open decisions
## Release condition
| Requirement IDs | Verifiable exit condition |
```

Use at most eight material FRs and ten ACs. Do not add applicability, page,
state-matrix, flow, risk, or phased-delivery sections unless the user switches
to Full. A Compact PRD is smaller, not less testable.

## Full

Use by default or when the user requests full detail. Preserve the three
applicability row names and table shapes so the deterministic validator can
check them. Mark each conditional row `Required` or `N/A` with a concrete
reason.

```markdown
<!-- wigtn-prd-profile: full -->
# <Feature> PRD
## Applicability
| Contract | Required / N/A | Evidence |
|---|---|---|
| Pages/routes or screen IDs |  |  |
| Empty/loading/error/success/recovery state matrix |  |  |
| Mermaid user or system flow |  |  |
## Context and problem
## Goals
## Non-goals
## Users, roles, and permissions
## Functional requirements
| ID | Requirement | Priority |
## Pages and routes
| Page or screen ID | Route, deep link, or explicit TBD + owner | Roles | Purpose |
## State matrix
| Surface | Empty | Loading | Error | Success | Recovery |
## User or system flow
```mermaid
flowchart TD
```
## Authorization and data boundaries
## Non-functional requirements
## Acceptance criteria
| ID | Requirement | Given | When | Then | Verification |
## Assumptions and open decisions
## Risks and mitigations
## Delivery
| Phase | Requirement IDs | Verifiable exit condition |
```

Always require problem, goals/non-goals, roles, stable FR IDs,
authorization/data boundaries, acceptance mapping, risks, open decisions, and
FR-mapped delivery.

Conditional:

- Require pages/routes or stable screen IDs and the state matrix for a
  user-visible feature. If routing is genuinely unknown, use `TBD` with an owner
  and decision point.
- Require Mermaid flow for a multi-step user or system lifecycle.
- Require a numeric NFR only when evidence supports its target. Otherwise name
  the metric, owner, and decision point.

Describe necessary behavior, not a preferred implementation unless the
constraint is real. Avoid duplicate FRs and ACs, speculative enterprise policy,
exhaustive edge-case catalogs, and open decisions that do not affect
implementation or release.

A plausible policy is not evidence: move unprovided identity, token, retry,
route, or expiry choices to one-line open decisions instead of silently
adopting them.
