# Acceptance Hard pilot errata

## v1

The sequential runner was stopped after one completed sample and replaced by
six isolated workers. No outcome result was reported.

## v2

The run was stopped during early grader audit. Two gold labels were defective:

- `code-only` was labeled `implemented-not-executed`, but the task permits a
  focused direct runtime assertion. Correct gold: `verified`.
- `stale-test` was labeled `not-satisfied`, but the implementation satisfies
  the negative-quantity subset and fails only zero. Correct gold:
  `partially-verified`.

The corrections follow the predeclared canonical status definitions and apply
equally to every arm. No v2 aggregate is reported. v3 hashes the corrected
generator, scorer, protocol, and this erratum before calls.

## v3

The static harness check found that the scorer invoked `validate-evidence.py`
with an unsupported `--json` option. This would have classified every artifact
as invalid regardless of arm or content. The run was stopped before aggregate
scoring, the invocation was corrected, and the corrected scorer was frozen as
v4. No v3 aggregate is reported.

## v4

The common prompt explicitly warned every arm about irrelevant, stale, and
flaky tests. That leaked the treatment's central evidence rule into bare. The
run was stopped and no causal aggregate is reported. v5 removes failure-mode
hints from the common prompt and places the relevance audit only in the
Acceptance Verifier treatment.

## v5

All 48 calls completed, but an evidence-level oracle audit found three
predeclared-label defects. The aggregate is exploratory and is not used as the
confirmatory result.

- `tenant-partial` contains no tenant filtering at all. A passing one-tenant
  input is degenerate coverage, not a material implemented subset. Correct
  gold: `not-satisfied`.
- `external-outcome` directly demonstrates the material enqueue precursor but
  cannot observe mailbox delivery. Correct gold: `partially-verified`.
- `flaky-check` cannot have one unconditional gold. `verified` is supported
  when the artifact records a separate successful direct assertion covering
  the complete small observable behavior; otherwise the correct status is
  `implemented-not-executed`. The v5 scorer incorrectly counted two such
  GPT-5.5 direct assertions as false verification.

The v6 scorer derives the flaky gold only from recorded check evidence, stores
the expected and observed statuses in raw scores, and freezes the clarified
subclaim-collapse rules in the treatment before calls.

## v6

The run was stopped after the first batch failed Codex endpoint DNS resolution.
No model output or evidence artifact was produced, so v6 contains
infrastructure failures only and no outcome sample. v7 uses the identical
frozen treatment, task generator, and scorer outside the restricted network
sandbox.
