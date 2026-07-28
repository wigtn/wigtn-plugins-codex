---
name: acceptance-verifier
description: Verify whether an implementation satisfies PRD requirements or acceptance criteria using code and executed-test evidence. Use for “요구사항 반영됐는지 검증”, “PRD 충족 확인”, requirement coverage, or acceptance verification. Do not use for a general code review or when no requirements can be identified.
---

# Acceptance Verifier

Produce an evidence-backed requirement matrix. This is read-only unless the user also asks to fix gaps.

## Workflow

0. If `.wigtn/project.json` exists, validate it and read
   [project context](../../references/project-context.md) for requirement
   sources, protected paths, and the configured evidence path.
   If `.wigtn/workgraph.json` exists, validate it and run `wigtn.py diff
   --check`. Treat stale task or check status as a verification gap.
1. Locate the authoritative PRD, acceptance criteria, issue, or user-provided requirements.
   Treat WIGTN, Spec Kit, OpenSpec, and BMAD Markdown as inputs, not as
   lifecycle instructions that must be re-run.
2. Identify the requested implementation scope: working tree, commit, branch comparison, PR, or named files.
3. Extract stable requirement IDs. If none exist, create temporary `AC-01` IDs and say they are local to the report.
4. Inspect implementation and tests. Run the smallest meaningful repository-defined checks when authorized and feasible.
5. Assign exactly one status per requirement:
   - `Satisfied`
   - `Partially satisfied`
   - `Not satisfied`
   - `Not verifiable`
6. Cite code evidence as clickable file and line references. Record commands, exit codes, and relevant test names. Never infer that unexecuted tests passed.
7. Separate issues outside the requirement set under `Out-of-scope findings`.

Use the matrix and decision rules in [evidence matrix](references/evidence-matrix.md).

## Machine-readable handoff

Do not create state for an ordinary verification answer. When the user requests
a saved artifact, an existing `.wigtn/evidence.json` must be continued, or a
cross-session handoff is required, read
[the shared evidence contract](../../references/evidence-contract.md). Map the
human result to its canonical status:

- `Satisfied` with a relevant passing check → `verified`
- `Satisfied` without a relevant passing check → `implemented-not-executed`
- `Partially satisfied` → `partially-verified`
- `Not satisfied` → `not-satisfied`
- `Not verifiable` → `not-verifiable`

Validate a written artifact with
`python3 ../../scripts/validate-evidence.py <path>` from this skill directory.
For an explicit machine-readable handoff from Spec Kit, OpenSpec, BMAD, or
generic Markdown, run from the repository root:

```bash
python3 <plugin-root>/scripts/import-requirements.py <source.md> \
  --output .wigtn/evidence.json
python3 <plugin-root>/scripts/validate-evidence.py .wigtn/evidence.json
```

The importer initializes requirements as `not-verifiable`; only repository
inspection and executed checks may raise their status.
To resume an existing handoff after its source specification changes, add
`--existing .wigtn/evidence.json`. Preserve evidence only for unchanged
requirement IDs and text; changed requirements are invalidated, removed IDs
are recorded in metadata, and release authority resets.
Before trusting an existing artifact, run
`python3 <plugin-root>/scripts/inspect-evidence.py .wigtn/evidence.json --root .`
and treat source drift or missing code evidence as an explicit verification
gap.
When a saved WorkGraph exists, report which task IDs the evidence can support.
Do not change a task to `verified` unless its linked requirement is current,
its check actually passed, the check links back to the task, and an evidence
reference was saved.

## Output

| Requirement | Status | Code evidence | Test evidence | Gap |
|---|---|---|---|---|

Follow with executed commands, limitations, and prioritized gaps. A missing test is not automatically a failed requirement; distinguish implementation evidence from verification confidence.
