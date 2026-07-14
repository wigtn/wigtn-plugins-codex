# Evaluation Guide

`tests/trigger-cases.tsv` is the deterministic invocation contract. `scripts/run-evals.sh` checks that every fixture maps to exactly the expected skill or to `none` using intentionally narrow trigger vocabularies.

This static check catches description regressions but does not prove Codex’s model-based implicit invocation. Before release, install from the repository marketplace and run the PRD E-01–E-15 prompts with at least three wording variants in fresh tasks. Record:

- selected skill
- unintended skills
- output acceptance criteria
- external mutation attempts
- commands and evidence produced

Release requires no unauthorized external mutation and no heavy-skill selection for ordinary “구현해줘” or small-fix prompts.
