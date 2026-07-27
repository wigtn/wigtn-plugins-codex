# Evaluation Guide

`tests/trigger-cases.tsv` is the deterministic invocation contract. `scripts/run-evals.sh` checks that every fixture maps to exactly the expected skill or to `none` using intentionally narrow trigger vocabularies.

This static check catches description regressions but does not prove Codex’s model-based implicit invocation. Before release, install from the repository marketplace and run the PRD E-01–E-15 prompts with at least three wording variants in fresh tasks. Record:

- selected skill
- unintended skills
- output acceptance criteria
- external mutation attempts
- commands and evidence produced

Release requires no unauthorized external mutation and no heavy-skill selection for ordinary “구현해줘” or small-fix prompts.

## 2026 model/harness study

The repository-level evidence is under
`.github/evals/delivery-workflows-2026/` in the parent source repository.
It separates:

- GPT-5.6 Sol bare vs installed-plugin ordinary vs explicit verified delivery,
- GPT-5.5 plugin cross-checks,
- real disposable Git state for release actions,
- visible and model-hidden implementation tests,
- test/draft/hash/scope preservation,
- anonymous dual-model patch review and a human blind-review packet,
- confirmatory PRD create/review gates.

Do not infer plugin value by comparing GPT-5.5+plugin directly with GPT-5.6
bare. For causal plugin claims, hold the model, effort, fixtures, and runtime
constant. Deterministic state and executed tests outrank model-judge scores.

The current release policy is:

- keep `release-readiness` as an authority boundary,
- leave ordinary coding unconstrained,
- invoke `verified-delivery` only by its qualified name,
- keep product/screen contracts and validators,
- block release on any unauthorized Git mutation.
