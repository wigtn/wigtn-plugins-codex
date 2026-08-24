# Delivery Evidence

For each material requirement, retain at least one precise code reference and
one verification result when executable verification exists. Record commands
exactly, including failures, reruns, and skipped checks. Never replace evidence
with a quality score.

Classify each check by provenance:

- `external`: benchmark, CI, or evaluator kept outside the agent worktree
- `repository`: pre-existing repository test or executable contract
- `user-provided`: fixture or oracle supplied by the user
- `agent-authored-red-green`: a focused test observed failing before the
  implementation and passing afterward
- `agent-authored-green-only`: an inline script or test observed only after the
  implementation

`verified` requires at least one relevant check from the first four classes.
`agent-authored-green-only` can support implementation confidence but cannot,
by itself, close an acceptance criterion. A passing unrelated repository test
does not upgrade an uncovered requirement.

Reference implementation isolation is part of evidence validity. If the run
reads or diffs an installed copy, another checkout, a package cache, benchmark
gold patch, or hidden test for the same project, label the affected result
`not-verifiable` and disclose the leakage. A clean evaluator pass does not
repair contaminated implementation provenance.

Use exactly one status:

- `verified`: implementation evidence plus a passing relevant check
- `implemented-not-executed`: code evidence exists but no relevant check ran
- `partially-verified`: only part of the observable criterion is supported
- `not-satisfied`: required behavior is absent or contradicted
- `not-verifiable`: required evidence is inaccessible or inherently external
- `not-applicable`: the requirement is outside the evaluated scope

Use the same canonical values for conversational output and a requested saved
handoff. A saved artifact is optional workflow output, not hidden state and not
a prerequisite for ordinary implementation.

For a small task with one material requirement, use a short completion
summary: changed behavior, exact checks and exits, blockers, and residual risk.
Do not manufacture a matrix for a one-line fix.

For multiple material requirements, use:

| Requirement | Status | Implementation evidence | Executed evidence |
|---|---|---|---|

When several public symbols or interfaces are named, include every
unimplemented, deferred, or uninspected item in the requirement rows or
verification boundary. Do not infer whole-feature coverage from one passing
submodule.

Then list changed behaviour, exact commands and exits, residual risks, unrelated
dirty state preserved, and external actions not performed. If all deterministic
checks already passed before the treatment, do not claim that this workflow
improved code quality; report only the evidence and safety it actually added.
Always state the verification boundary: which interfaces and behaviors were
exercised, which were inferred, and whether hidden or external checks were
available. Unspecified public API names or schemas remain gaps even when the
implemented behavior appears correct.
