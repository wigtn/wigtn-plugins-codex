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
- `partially-verified`: part is supported, the rest is unresolved, and no required
  behavior is demonstrated false
- `not-satisfied`: evidence shows required behavior is absent or contradicted;
  this takes precedence over passing other examples
- `not-verifiable`: available evidence cannot support a conclusion
- `not-applicable`: the requirement does not apply to this scope

Never mark a requirement `verified` from documentation, narration, an
unexecuted or unrelated test, or a check that is not referenced by ID.
Judge executed checks by their coverage of the current requirement. Record
whether they were pre-existing, supplied externally, or authored for this work;
after-change-only checks are not red/green evidence. Their authorship alone
neither proves coverage nor requires a downgrade. Use `partially-verified` for
an actual unresolved subclaim, and `not-satisfied` for a demonstrated violation.

## Portability and authority

- Store repository-relative paths, never machine-specific absolute paths.
- Keep requirement and check IDs unique and stable.
- Record exact commands, exit codes, and relevant test names.
- Record commit, push, pull-request, and deploy authority separately.
- A performed external action must include evidence and recorded user
  authority. The artifact records authority; it does not grant it.
- Keep unknowns as gaps or limitations instead of fabricating evidence.
