# Saved acceptance evidence

Use for WIGTN-format evidence or WorkGraph verification. A user-defined
report schema is sufficient when no WIGTN state is requested or present.
For WIGTN evidence, read the shared
[Evidence Contract](../../../references/evidence-contract.md).

For a new imported handoff, run from the target repository root:

```bash
python3 <plugin-root>/scripts/import-requirements.py <source.md> \
  --output .wigtn/evidence.json
python3 <plugin-root>/scripts/validate-evidence.py .wigtn/evidence.json
```

The importer starts every requirement as `not-verifiable`. Only inspected code
and executed checks may raise status. To resume after source changes, add
`--existing .wigtn/evidence.json`; changed requirements lose prior evidence,
removed IDs stay in metadata, and release authority resets.

Before trusting an existing artifact, run:

```bash
python3 <plugin-root>/scripts/inspect-evidence.py .wigtn/evidence.json --root .
```

Treat source drift, missing code references, or invalid checks as gaps. Use the
same canonical status in the saved artifact and human report. A saved artifact
records evidence and authority; it grants neither release nor remote action.
