# Evidence Contract 1.0

The Evidence Contract is an optional, machine-readable handoff between WIGTN's
product, implementation, acceptance, and release skills. Its purpose is narrow:
prevent a later workflow from silently turning “code exists” into “verified” or
turning a recorded release intention into authority.

It is not a required project database. Skills should create or update
`.wigtn/evidence.json` only when the user requests a saved artifact, when that
file already participates in the task, or when a cross-session handoff is
explicitly required.

## What the contract preserves

- source artifact paths and optional hashes
- stable requirement IDs
- precise repository-relative code evidence
- executed commands, exit codes, and named tests
- requirement-to-check references
- unresolved gaps and limitations
- separate commit, push, pull-request, and deploy authority
- evidence for external actions actually performed

The canonical JSON Schema is
`plugins/wigtn-plugins-with-codex/schemas/evidence-contract.schema.json`.
The dependency-free validator also enforces relationships that JSON Schema
alone cannot express compactly.

```bash
python3 plugins/wigtn-plugins-with-codex/scripts/validate-evidence.py \
  .wigtn/evidence.json
```

Inspect whether a valid handoff has drifted since it was written:

```bash
python3 plugins/wigtn-plugins-with-codex/scripts/inspect-evidence.py \
  .wigtn/evidence.json --root .
```

The status command verifies recorded source hashes, referenced code paths and
line ranges, canonical status counts, and the current release-authority flags.

## Optional project context

Teams may commit `.wigtn/project.json` to share requirement sources,
repository-owned verification commands, protected paths, the desired PRD
profile, and the Evidence Contract location across the core skills:

```bash
python3 plugins/wigtn-plugins-with-codex/scripts/validate-project-context.py \
  .wigtn/project.json
```

The file is optional and never grants external-action authority. Missing or
invalid context degrades to normal repository discovery.

## Status semantics

| Status | Minimum evidence |
|---|---|
| `verified` | code reference plus a referenced passing check; no open gap |
| `implemented-not-executed` | code reference, but no relevant passing check |
| `partially-verified` | partial support and at least one explicit gap |
| `not-satisfied` | evidence of missing or contradictory behavior and a gap |
| `not-verifiable` | insufficient accessible evidence and a stated gap |
| `not-applicable` | requirement is outside the evaluated scope |

The human report may use natural labels. The persisted artifact uses only these
canonical values. Documentation or model narration cannot by itself establish
`verified`.

## Authority invariant

The artifact records what the user authorized; it does not authorize an action.
If an action is marked `performed`, the corresponding authority flag must be
true and the action must retain evidence such as a commit hash, pushed branch,
or pull-request URL. Commit authority does not imply push authority, and push
authority does not imply pull-request or deploy authority.

## Compatibility

Version `1.0` rejects unknown keys so that producer mistakes fail loudly.
Future incompatible formats require a new `schema_version` and schema ID.
Repository-relative paths make artifacts portable across clones and evaluator
machines.

## Read-only interoperability

The plugin can normalize supported Markdown requirements without installing or
re-running another framework's lifecycle:

```bash
python3 plugins/wigtn-plugins-with-codex/scripts/import-requirements.py \
  path/to/spec.md --output .wigtn/evidence.json
```

The importer recognizes stable WIGTN/Spec Kit IDs, OpenSpec requirement blocks,
BMAD acceptance lists, and a conservative generic subset. Imported
requirements always start as `not-verifiable`; importing a document never
proves implementation.

To resume after a source specification changes:

```bash
python3 plugins/wigtn-plugins-with-codex/scripts/import-requirements.py \
  path/to/spec.md --existing .wigtn/evidence.json \
  --output .wigtn/evidence.json
```

Evidence and referenced checks survive only when both the stable ID and
normalized requirement text are unchanged. Changed requirements reset to
`not-verifiable`, removed IDs are recorded in metadata, and release authority
is never inherited from the old artifact.
