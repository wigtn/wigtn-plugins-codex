# WorkGraph contract

WorkGraph is the planning state between product artifacts and Evidence
Contract results.

## Lifecycle boundary

```text
requirement → artifact → task → check → release gate
```

- Requirement status describes whether its source is current.
- Artifact status describes whether a derived product artifact is current.
- Task status describes implementation progress.
- Check status describes an executable observation.
- Release gate status summarizes prerequisites; it never grants authority.

Allowed task progression:

```text
draft → ready → in-progress → implemented → verified
                  └──────→ blocked
any active state → stale
```

`verified` requires a linked passing check and an evidence reference. Source
drift propagates through linked artifacts, tasks, checks, dependent tasks, and
release gates.

## CLI

Run from the target repository root and replace `<plugin-root>` with the
installed plugin path:

```bash
python3 <plugin-root>/scripts/wigtn.py --json init
python3 <plugin-root>/scripts/wigtn.py --json init --apply
python3 <plugin-root>/scripts/wigtn.py --json import docs/prd.md
python3 <plugin-root>/scripts/wigtn.py --json import docs/prd.md --apply
python3 <plugin-root>/scripts/wigtn.py --json plan
python3 <plugin-root>/scripts/wigtn.py --json plan --apply
python3 <plugin-root>/scripts/wigtn.py --json status
python3 <plugin-root>/scripts/wigtn.py --json next
python3 <plugin-root>/scripts/wigtn.py --json diff --check
python3 <plugin-root>/scripts/wigtn.py --json diff --apply
python3 <plugin-root>/scripts/wigtn.py --json doctor
python3 <plugin-root>/scripts/wigtn.py --json task update TASK-ID \
  --title "..." --risk high --path src/file.py
python3 <plugin-root>/scripts/wigtn.py --json task update TASK-ID \
  --title "..." --risk high --path src/file.py --apply
python3 <plugin-root>/scripts/wigtn.py --json task depend TASK-ID --on TASK-OTHER
python3 <plugin-root>/scripts/wigtn.py --json task depend TASK-ID \
  --on TASK-OTHER --apply
python3 <plugin-root>/scripts/validate-workgraph.py .wigtn/workgraph.json
```

Mutation commands are dry-run unless `--apply` is present. Repeating an
unchanged import, plan, or drift application must not advance the revision.
Use `--expected-revision <n>` on task mutations when another process could
change the graph. A mismatch fails instead of overwriting newer work. Adding an
unverified dependency automatically returns a `ready` task to `draft`.

## Planning quality

A task is implementation-ready only when it has:

- at least one stable requirement ID;
- a coherent observable outcome;
- real dependency IDs;
- intended and protected paths when known;
- a proportionate risk class;
- at least one check ID;
- a concrete command when the repository exposes one.

Leave unknown commands as `null`; do not invent test commands. A generated
one-task-per-requirement plan is only a deterministic seed. Merge or split
tasks when repository boundaries and verification endpoints justify it.
