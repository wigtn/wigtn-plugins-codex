<!-- wigtn-prd-profile: compact -->
# Invite PRD

## Problem

Create an invitation.

## Goals and non-goals

- Goal: invite one user.
- Non-goal: bulk import.

## Users, roles, authorization, and data boundaries

Only an administrator can create invitations.

## Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-INV-01 | Create an invitation. | Must |

## Acceptance criteria

- AC-INV-01: Invitation creation works.

## Assumptions and open decisions

- Expiry is undecided.

## Release condition

| Requirement IDs | Verifiable exit condition |
|---|---|
| FR-INV-01 | AC-INV-01 passes. |
