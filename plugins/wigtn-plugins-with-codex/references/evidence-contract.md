# Evidence Contract

Use the evidence contract only when the user requests a saved machine-readable
artifact, an existing `.wigtn/evidence.json` is part of the task, or a workflow
explicitly requires handoff across sessions. Do not create project state for an
ordinary answer.

The canonical schema is `schemas/evidence-contract.schema.json` at the plugin
root. Validate a saved artifact with:

```bash
python3 <plugin-root>/scripts/validate-evidence.py <artifact.json>
```

## Canonical statuses

- `verified`: precise implementation evidence and a referenced passing check
- `implemented-not-executed`: implementation evidence exists; no relevant
  passing check was executed
- `partially-verified`: only part of the observable requirement is supported
- `not-satisfied`: evidence shows the requirement is absent or contradicted
- `not-verifiable`: available evidence cannot support a conclusion
- `not-applicable`: the requirement does not apply to this scope

Never mark a requirement `verified` from documentation, model narration, an
unexecuted test, a check that is not referenced by ID, or a green-only check
written by the same agent during the implementation. An agent-authored check
can support `verified` only when the artifact or accompanying trace records its
pre-change failure and post-change pass. Until check provenance is represented
in the machine-readable schema, record that distinction in `limitations` and
use `partially-verified` when independent evidence is absent.

## Portability and authority

- Store repository-relative paths, never machine-specific absolute paths.
- Keep requirement and check IDs unique and stable.
- Record exact commands, exit codes, and relevant test names.
- Record commit, push, pull-request, and deploy authority separately.
- A performed external action must include evidence and recorded user
  authority. The artifact records authority; it does not grant it.
- Keep unknowns as gaps or limitations instead of fabricating evidence.
