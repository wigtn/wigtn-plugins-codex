<!-- wigtn-prd-profile: full -->
# Invite PRD

## Applicability

| Contract | Required / N/A | Evidence |
|---|---|---|
| Pages/routes or screen IDs | N/A | API-only fixture |
| Empty/loading/error/success/recovery state matrix | N/A | No user interface |
| Mermaid user or system flow | N/A | Single request fixture |

## Context and problem

An administrator needs to create an invitation.

## Goals

- Create one invitation.

## Non-goals

- Bulk import.

## Users, roles, and permissions

- Organization administrator.

## Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-INV-01 | An administrator can create an invitation. | Must |

## Authorization and data boundaries

The server limits creation to the administrator's organization.

## Acceptance criteria

| ID | Requirement | Given | When | Then | Verification |
|---|---|---|---|---|---|
| AC-INV-01 | FR-INV-01 | An administrator | An invitation is requested | One invitation exists | Integration test |

## Delivery

| Phase | Requirement IDs | Verifiable exit condition |
|---|---|---|
| MVP | FR-INV-01 | AC-INV-01 passes. |
