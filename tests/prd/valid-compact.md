<!-- wigtn-prd-profile: compact -->
# Invite PRD

## Problem and scope

Administrators need to invite one team member. Bulk import is excluded.

## Goals and non-goals

- Goal: accept one valid invitation.
- Non-goal: design organization roles.

## Users, roles, authorization, and data boundaries

Only an organization administrator can create an invitation for that
organization.

## Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-INV-01 | An administrator can create an invitation. | Must |
| FR-INV-02 | A valid invitation can be accepted once. | Must |

## Acceptance criteria

| ID | Requirement | Given | When | Then | Verification |
|---|---|---|---|---|---|
| AC-INV-01 | FR-INV-01 | An administrator and valid email | The administrator creates an invitation | One pending invitation exists | Integration test |
| AC-INV-02 | FR-INV-02 | A pending invitation | The invited user accepts it | Membership is created and reuse fails | Integration test |

## Assumptions and open decisions

- Invitation expiry is a product decision.

## Release condition

| Requirement IDs | Verifiable exit condition |
|---|---|
| FR-INV-01, FR-INV-02 | AC-INV-01 and AC-INV-02 pass. |
