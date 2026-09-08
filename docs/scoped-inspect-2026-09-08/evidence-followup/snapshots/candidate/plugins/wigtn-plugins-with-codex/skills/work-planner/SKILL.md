---
name: work-planner
description: Save requirements as a resumable dependency-aware WIGTN WorkGraph with tasks, checks, paths, and drift invalidation. Use only for saved plans, cross-session resume, WorkGraph maintenance, or stale-work analysis. Do not use for conversational plans, implementation, PRDs, or releases.
---

# Work Planner

Save a resumable plan whose requirement IDs, dependencies, executable checks,
and source freshness can be validated. Use the smallest useful graph; ordinary
conversation does not need lifecycle files.

## Workflow

- Preserve authoritative requirement IDs. For existing state with known task
  IDs, run `python3 ../../scripts/wigtn.py --root <repository> --json inspect --task TASK-ID`
  from this skill directory; repeat `--task` for multiple IDs. Omit `--task`
  for graph-wide analysis. Both views validate the whole graph and report
  global source drift. The task view includes transitive dependencies and
  states what was omitted. Reinspect after relevant changes or incomplete
  results; do not repeat unchanged queries.
- Read [WorkGraph contract](references/workgraph-contract.md) for mutations
  or additional state semantics. Mutations require `--apply`; preview when
  the scope or effect is uncertain, rather than duplicating decided commands.
- Define tasks by independently verifiable outcomes. Link requirements,
  dependencies, intended/protected paths, and relevant checks. Unknown test
  commands remain unknown, not invented. A seed plan is editable, not a fixed
  one-task-per-requirement prescription.
- Use CLI task mutations where supported; preserve concurrent changes with
  `--expected-revision` when needed. Keep incomplete task definitions `draft`.
  Only tasks whose dependencies are verified may be `ready`.

## State and completion

Source drift invalidates linked artifacts, tasks, checks, and release gates.
Do not preserve old `verified` claims or grant verification from a plan alone.
Executed checks and valid evidence are required; a ready release gate does
not grant Git or deployment permission. Continue other work already authorized.

Return the saved path, revision, actionable next tasks, and unresolved gaps.
A successful mutation validates graph structure; inspect again when source
freshness or other saved artifacts may have changed.
