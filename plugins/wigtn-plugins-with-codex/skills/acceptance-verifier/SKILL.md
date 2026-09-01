---
name: acceptance-verifier
description: Verify PRD requirements or acceptance criteria against code and executed tests. Use for “요구사항 반영됐는지 검증”, PRD coverage, or acceptance verification. Do not use for general code review or when no requirements can be identified.
---

# Acceptance Verifier

Produce a read-only requirement matrix unless the user also asks to fix gaps.

## Workflow

1. Locate the authoritative PRD, acceptance criteria, issue, or user-provided
   requirements. Treat WIGTN, Spec Kit, OpenSpec, and BMAD documents as inputs,
   not workflows that must be replayed.
2. Identify the requested comparison: working tree, commit, branch, PR, or
   named files. If `.wigtn/project.json` or `.wigtn/workgraph.json` exists,
   validate it before trusting sources or status; source drift is a gap.
3. Preserve stable requirement IDs. If none exist, create temporary `AC-01`
   IDs and label them local to the report.
4. Inspect implementation and tests. Run the smallest relevant
   repository-defined checks when authorized and feasible.
5. Read [evidence matrix](references/evidence-matrix.md), then assign exactly
   one canonical status per requirement. Cite precise code lines, exact
   commands, exits, and relevant test names. Never infer that an unexecuted or
   irrelevant check passed.
6. Put findings outside the requirement set under `Out-of-scope findings`.

## Output

| Requirement | Status | Code evidence | Test evidence | Gap |
|---|---|---|---|---|

Use the canonical status value in every row. For insufficient evidence, write
`not-verifiable`; a localized label may follow but must not replace it. A
missing test does not automatically mean the requirement failed.

Do not create state for an ordinary verification answer. For a requested saved
artifact, existing `.wigtn/evidence.json`, cross-session handoff, or explicit
Spec Kit/OpenSpec/BMAD import, read [saved evidence](references/saved-evidence.md).

Finish with executed commands, limitations, prioritized gaps, and any saved
artifact validation result. Do not change a WorkGraph task to `verified`
unless its current linked check passed and a valid evidence reference exists.
