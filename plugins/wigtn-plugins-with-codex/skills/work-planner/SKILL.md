---
name: work-planner
description: Turn stable product requirements and artifacts into a dependency-aware WIGTN WorkGraph with implementation tasks, checks, risks, intended paths, stale propagation, and resumable next work. Use for “구현 계획 세워줘”, “task로 쪼개줘”, “작업 순서”, “resume plan”, or an explicit cross-session lifecycle plan. Do not use for ordinary implementation, a simple conversational checklist, PRD authoring, or release execution.
---

# Work Planner

Create an implementation plan whose IDs, dependencies, checks, and source
freshness can be validated. Planning does not authorize implementation or Git
actions.

## Workflow

1. Read repository instructions and the authoritative PRD, issue, screen spec,
   or acceptance criteria. Preserve existing requirement IDs.
2. If `.wigtn/project.json` exists, validate it. If `.wigtn/workgraph.json`
   exists, run `wigtn.py doctor` and `wigtn.py diff --check` before trusting its
   status.
3. For a requested persistent or cross-session plan, show the `init` or
   `import` dry-run first, then apply it. Do not create lifecycle state for a
   conversational plan unless the user requests a saved plan or continuing
   workflow.
4. Create one task per independently verifiable change, not automatically one
   task per file. Link every task to at least one requirement. Record intended
   paths, protected paths, risk, executable checks, artifacts, and real
   dependencies. Use `wigtn.py task update` and `wigtn.py task depend` with
   dry-run then `--apply`; do not edit WorkGraph JSON directly when these
   commands cover the change.
5. Keep tasks `draft` until their scope and checks are concrete. Mark `ready`
   only when all dependencies are `verified`. Use `blocked` only with a
   specific blocker.
6. Run the WorkGraph validator. Return the next unblocked task IDs, unresolved
   planning gaps, and validation result.

Use [the WorkGraph contract](references/workgraph-contract.md) for state
semantics and commands.

## Rules

- Treat source drift as invalidation, not as a documentation warning.
- Never preserve `verified` after a linked requirement, artifact, dependency,
  or check becomes stale.
- Do not mark a task `verified`; only executed evidence handled by
  `acceptance-verifier` or an explicit delivery workflow may do that.
- Keep release authority outside task status. A ready release gate does not
  authorize commit, push, pull request, or deploy.
- Prefer the smallest dependency graph that preserves real ordering. Do not add
  ceremonial tasks or dependencies.
- Do not execute implementation, install dependencies, commit, push, or mutate
  remote systems.

## Completion

Return the WorkGraph path when saved, its revision, created or changed task
IDs, next task IDs, source-drift status, and validator result. State explicitly
when commands or intended paths remain unspecified.
