---
name: acceptance-verifier
description: Verify requirements against inspectable code and tests with canonical evidence statuses. Use for PRD coverage or acceptance verification. For evidence-only chat without inspectable code or tests, answer directly without invoking. Do not use for general code review or when no requirements can be identified.
---

# Acceptance Verifier

Compare authoritative requirements with code and executed checks; fix gaps only
when requested. Preserve source IDs and the user's output schema.

## Evidence

- Inspect relevant implementation and run proportionate checks. Cite code
  locations, commands, outcomes, and what remains unobserved.
- Use one canonical status per requirement: `verified`,
  `implemented-not-executed`, `partially-verified`, `not-satisfied`,
  `not-verifiable`, or `not-applicable`.
- A demonstrated requirement violation is `not-satisfied`, even if other
  examples pass. `partially-verified` requires a demonstrated subclaim,
  unresolved subclaims, and no demonstrated violation. Missing evidence alone
  is not a failure. Read [evidence matrix](references/evidence-matrix.md) for
  compound claims, contradictory/flaky checks, or external actions.
- If saved WorkGraph state is relevant, run
  `python3 ../../scripts/wigtn.py --root <repository> --json inspect`
  from this skill directory. It validates saved artifacts and previews drift
  without mutation. Source changes invalidate old completion evidence.

## Output

Return the requested report with requirement, status, evidence, and gap.
Keep unrelated findings separate. Use a file-edit/patch tool when saving
reports with command examples to avoid nested shell heredoc collisions.

Custom JSON needs no WIGTN schema. Read
[saved evidence](references/saved-evidence.md) only for a requested WIGTN
handoff or WorkGraph verification. A task becomes `verified` only with its
current linked passing check and a valid evidence reference.
