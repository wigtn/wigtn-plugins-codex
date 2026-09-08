---
name: verified-delivery
description: Implement and verify with proportional evidence only when explicitly invoked as $wigtn-plugins-with-codex:verified-delivery; never auto-invoke for ordinary coding, specs, review, or Git requests.
---

# Verified Delivery

Implement the requested scope and retain proportionate execution evidence.
Use the repository's implementation and testing conventions. Choose the
approach rather than replaying a fixed development sequence.

## Workflow

- Use a compact coverage census only when the request names multiple material requirements
  or interfaces. Track relevant invariants for auth, tenancy, secrets, migration, persistence, concurrency
  and compatibility when involved.
- Do not duplicate a passing repository oracle without a coverage gap.
  Investigate failures before choosing whether code, tests, or the test command
  is wrong. A suggested verification command is evidence, not an exclusive rule.
- Read [delivery evidence](references/delivery-evidence.md) for compound claims
  or uncertain check provenance. For benchmark or independent evaluation work,
  read its isolation rules before implementation.
- Finish with changed behavior, relevant checks and results, and material
  verification gaps. Do not add a matrix when prose expresses the coverage.

## Saved state

Do not create stable IDs, WorkGraph state, or evidence JSON by default.
For requested WIGTN handoff or existing saved state, read
[shared evidence contract](../../references/evidence-contract.md).
Saved task verification requires a current linked passing check and evidence.
Preserve unrelated work and reuse the user's existing authorization.
