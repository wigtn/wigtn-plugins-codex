# Optional Project Context

Read `.wigtn/project.json` only when it exists. Do not create it for ordinary
work. Validate it before use:

```bash
python3 <plugin-root>/scripts/validate-project-context.py .wigtn/project.json
```

The file provides `requirement_sources`, `verification_commands`,
`protected_paths`, `prd_profile`, and `evidence_path`. Optional
`lifecycle_profile` (`lite`, `flow`, or `studio`) and `workgraph_path` select
saved lifecycle behavior. Running `wigtn.py init --apply` creates a `flow`
profile because that command is an explicit lifecycle request.

An explicit user request and repository instructions outrank project context. The file narrows
discovery; it never grants commit, push, PR, deploy, network,
dependency-installation, or destructive authority. Missing or invalid context
must degrade to normal repository discovery rather than block unrelated work.
