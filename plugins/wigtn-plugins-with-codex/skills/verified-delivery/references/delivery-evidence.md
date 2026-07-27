# Delivery Evidence

For each material requirement, retain at least one precise code reference and
one verification result when executable verification exists. Record commands
exactly, including failures, reruns, and skipped checks. Never replace evidence
with a quality score.

Use exactly one status:

- `Verified`: implementation evidence plus a passing relevant check
- `Implemented, not executed`: code evidence exists but no relevant check ran
- `Partially implemented`: only part of the observable criterion is supported
- `Not implemented`
- `Not verifiable`: required evidence is inaccessible or inherently external

Completion summary:

| Requirement | Status | Implementation evidence | Executed evidence |
|---|---|---|---|

Then list changed behaviour, exact commands and exits, residual risks, unrelated
dirty state preserved, and external actions not performed. If all deterministic
checks already passed before the treatment, do not claim that this workflow
improved code quality; report only the evidence and safety it actually added.
