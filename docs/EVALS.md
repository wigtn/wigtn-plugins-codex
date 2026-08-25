# Evaluation Guide

The repository separates deterministic contracts from stochastic model
behavior. Mixing them under one “eval” pass made a green trigger parser look
like proof of model quality.

## Static contracts

`scripts/run-static-contracts.sh` checks:

- all trigger fixtures map to exactly one expected skill or `none`
- runtime plugin references resolve, bundled skill resources are reachable,
  and output templates contain no remote dependencies
- handDrawn source/SVG/PNG structure and self-contained WIGTN HTML presentation
  routing pass positive and negative fixtures
- a valid Evidence Contract passes
- nine invalid Evidence Contract cases fail with the expected diagnostic,
  including false `verified`, unauthorized action, absolute path, duplicate
  check, inconsistent exit, unknown key, missing gap, status/check mismatch,
  and wrong schema version
- Compact and Full PRD profiles accept four versioned fixtures, including
  stable non-`FR-` IDs and Markdown code-span IDs
- Spec Kit, OpenSpec, and BMAD Markdown fixtures import into conservative
  `not-verifiable` Evidence Contract stubs, preserve unchanged evidence on
  resume, and invalidate changed requirements
- Core 4 and equal-description-length Placebo 4 ablation packages build with
  isolated skill catalogs
- Evidence status detects source drift and invalid code references
- optional project context rejects unsafe paths and unknown configuration
- screen bundles reject missing artifacts, unresolved template values, broken
  wireframe anchors, remote resources, missing viewport metadata, and
  cross-artifact requirement drift
- release-state inspection distinguishes staged, unstaged, untracked,
  conflicted, detached, and in-progress Git states without mutation
- sanitized eval packets redact run roots and secrets, hash membership, exclude
  auth/work homes, and detect tampering
- WorkGraph schema, ID/reference integrity, dependency cycles, false
  `verified`, source drift propagation, migration, dry-run, idempotency, and
  CLI behavior pass 67 deterministic cases
- paired evaluation schedules are deterministic, seed-frozen,
  block-position balanced, and contain every arm exactly once per pair

`scripts/run-evals.sh` remains a compatibility alias for this deterministic
suite. Static checks catch description and evidence-policy regressions; they do
not prove Codex's model-based implicit invocation or implementation quality.

## Behavior smoke

`scripts/run-behavior-evals.sh` has a no-cost planning mode:

```bash
./scripts/run-behavior-evals.sh
```

Execute the paired GPT-5.6 Sol smoke run explicitly:

```bash
./scripts/run-behavior-evals.sh --execute
```

“Paired” only means the two arms share a task/repetition identity. It does not
make the result trustworthy by itself. The runner now requires a fresh output
root, freezes and hashes `SCHEDULE.tsv`, uses seed-frozen block-wise cyclic
rotation to balance arm position, records pair ID and global order in every
run, and fails the scorer when a scheduled arm is missing, duplicated, or
mismatched.

For a confirmatory quality claim, paired execution additionally requires:

- identical model, effort, timeout, tools, permissions, and repository commit;
- independently reset workspaces and Codex homes;
- at least three trials per task;
- locked prompts, graders, and holdout tasks hashed before execution;
- task-level paired statistics rather than treating repeats as independent
  samples;
- blind human review for subjective endpoints;
- complete reporting of timeout, infrastructure failure, exclusion, and
  protocol deviation.

Fixed-order `bare → plugin`, a reused run directory, unblinded model judging,
or a single trial downgrades a run to development smoke. It cannot support a
causal quality-lift claim.

Implementation provenance is also part of validity. Reading or diffing an
installed copy, another checkout, a package cache, benchmark gold patch, or
hidden test for the same project invalidates the affected arm even if the
official evaluator passes. Prompt-only instructions are not sufficient
isolation when the agent filesystem can still read those references.

It creates isolated `CODEX_HOME` directories, disables remote plugins and apps,
installs WIGTN only in the treatment arm, verifies prompt-input isolation,
hashes the evaluated plugin and prompts, and stores raw outputs, logs, metadata,
and a results file outside the repository by default. Its three prompts cover
PRD creation, uncertain acceptance evidence, and an ordinary coding request.

The smoke scorer checks execution health only. It deliberately does not turn
output keywords into a quality score. Publication claims require frozen
task-specific scorers, repeated runs, and human review.

## FeatureBench quality-lift pilot

The 2026-07-28 pilot froze four unique-repository tasks from FeatureBench's
fast split after clean-base and gold prechecks. It observed one raw
bare-fail/plugin-pass pair, but the plugin event log showed direct inspection
of an installed copy of the same project and a reverse-order clean repeat
failed in both arms. The adjudicated result is therefore zero eligible and zero
replicated positive tasks, not 1/4 positive lift.

- protocol: `docs/FEATUREBENCH-LIFT-PROTOCOL-2026-07-28-KO.md`
- result narrative: `docs/FEATUREBENCH-LIFT-PILOT-2026-07-28-KO.md`
- frozen result: `tests/external/featurebench/results-2026-07-28.json`
- contract check: `scripts/check-featurebench-results.py`

These four tasks are a development set after the assurance-path reform. A
future quality claim requires a new isolated holdout; rerunning the same tasks
cannot provide confirmatory evidence.

## Package ablation

`scripts/run-package-ablation.sh` compares `bare`, equal-description-length
`placebo4`, `core4`, and `full9` arms in isolated Codex homes. Its deterministic
summarizer scores the Compact PRD contract and an ordinary non-mutating
JavaScript fix while reporting token, response-size, and latency separately.

```bash
./scripts/run-package-ablation.sh
./scripts/run-package-ablation.sh --execute
```

The first command is a no-cost plan. The second makes model calls and requires
a fresh `WIGTN_ABLATION_ROOT`. A two-task pilot can falsify broken isolation or
obvious catalog regressions; it cannot authorize a general quality claim or a
marketplace split.

## Ordinary-coding non-interference gate

`scripts/run-ordinary-gate.sh` compares `bare`, `core4`, `full8`, and `full9`
on a frozen 12-task Python/JavaScript/Ruby hidden-test corpus:

```bash
bash scripts/run-ordinary-gate.sh
WIGTN_ORDINARY_GATE_ROOT=/tmp/fresh-ordinary-gate \
  bash scripts/run-ordinary-gate.sh --execute
```

The corpus validator proves that each starting fixture passes visible tests,
fails its hidden fault test, and passes after the reference fix. The scorer
checks hidden correctness, allowed-file scope, protected sentinel integrity,
unsolicited lifecycle state, tokens, and duration. A passing run is a
development non-interference screen, not evidence that the plugin improves
ordinary coding. The 2026-07-28 GPT-5.6 Sol pilot passed all gates but all arms
scored 12/12, so the result has a material ceiling effect and requires harder
held-out confirmation.

## Hard outcome suites

- `scripts/run-acceptance-hard.sh`: eight adversarial evidence tasks, three
  arms, two trials; exact canonical status and false `verified` are primary.
- `scripts/run-delivery-recheck.sh`: four hidden-test implementation tasks and
  ten disposable Git-state tasks against the current candidate.
- `scripts/run-delivery-blind.sh`: anonymous patches for two model judges plus
  a human-review packet. Candidate mapping is not materialized during judging.
- `scripts/run-prd-blind.sh`: four anonymous PRD panels across source models
  and repeats, scored for implementability, decision hygiene, traceability, and
  concision by two model judges, plus a separate human packet.
- `scripts/run-actual-repo-pilot.sh`: four tasks copied from two non-toy
  repositories; source repositories are never modified.
- `scripts/run-workgraph-pilot.sh`: twelve explicit `work-planner` capability
  tasks scored for contract validity, source fidelity, requirement coverage,
  checks, intended paths, dependencies, risk, no overclaim, protected paths,
  and sentinel preservation. This treatment-only pilot tests lifecycle
  behavior; it does not estimate lift over bare Codex.

Every expensive suite requires an explicit `--execute`, a fresh output root,
and a pre-call manifest. Aborted pilots and scorer corrections remain in
errata and are excluded from aggregate claims.
An anonymous label is not enough for a blind claim: mapping files must be
absent from the judge-visible run tree until scoring, and model judges remain a
screening layer rather than independent human replication.

Export selected run roots only after all scorers finish:

```bash
python3 scripts/export-eval-packet.py \
  --exclude-prefix blind --exclude-prefix blind-v2 \
  /tmp/wigtn-eval-packet <run-root>...
python3 scripts/verify-eval-packet.py /tmp/wigtn-eval-packet
```

The exporter omits Codex homes, work copies, staging, and prompt-input state,
redacts local roots and token-like secrets, and hashes every included file.
Store the resulting packet outside ephemeral `/tmp` before publication.

## Release behavior gate

Before release, install from the repository marketplace and run each relevant
prompt with at least three wording variants in fresh tasks. Record:

- selected skill
- unintended skills
- output acceptance criteria
- external mutation attempts
- commands and evidence produced

Release requires no unauthorized external mutation and no heavy-skill selection for ordinary “구현해줘” or small-fix prompts.

For a causal plugin claim, compare bare and plugin arms using the same model,
reasoning effort, task fixture, permissions, and runtime. GPT-5.5+plugin versus
GPT-5.6 bare is a compatibility comparison, not a causal estimate.

For implementation and release workflows, use disposable real Git
repositories, visible and hidden tests, preserved user-draft sentinels, exact
Git-state collection, and blinded patch review. Report deterministic pass rates
and unauthorized mutation counts before model-judge preferences. Freeze prompts
and scorers by hash before confirmatory runs; scorer changes create a new study
version.

## 2026 model/harness study

The existing repository-level research evidence is under
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
- use the optional Evidence Contract for explicit cross-workflow handoffs,
- block release on any unauthorized Git mutation.
