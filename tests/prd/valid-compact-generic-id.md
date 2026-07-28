<!-- wigtn-prd-profile: compact -->
# Organization Invite PRD

## Problem and scope

Administrators need to invite one member. Bulk import is excluded.

## Goals and non-goals

- Goal: accept one valid invitation.
- Non-goal: define the entire role system.

## Users, roles, authorization, and data boundaries

Only an organization administrator can create an invitation for that
organization.

## Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| `ORG-INV-001` | An administrator can create an invitation. | Must |
| ORG-INV-002 | A valid invitation can be accepted once. | Must |

## Acceptance criteria

| ID | Requirement | Given | When | Then | Verification |
|---|---|---|---|---|---|
| `AC-001` | ORG-INV-001 | An administrator and valid email | The administrator creates an invitation | One pending invitation exists | Integration test |
| AC-002 | ORG-INV-002 | A pending invitation | The invited user accepts it | Membership is created and reuse fails | Integration test |

## Assumptions and open decisions

- Invitation expiry is a product decision.

## Release condition

| Requirement IDs | Verifiable exit condition |
|---|---|
| ORG-INV-001, ORG-INV-002 | AC-001 and AC-002 pass. |
