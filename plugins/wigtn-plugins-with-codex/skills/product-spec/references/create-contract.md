# PRD Create Contract

Use the smallest implementation-ready contract. Preserve the three
applicability row names and table shapes so the deterministic validator can
check them. Mark each conditional row `Required` or `N/A` with a concrete
reason.

```markdown
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
