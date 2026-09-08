# Delivery Evidence

Cite the relevant implementation and executed checks. Distinguish pre-existing
repository checks, external/user-provided checks, and agent-authored checks.
For new checks, report whether a pre-change failure was actually observed;
a green-only check must not be described as red/green evidence. Judge coverage
by what was exercised, not by who wrote the check. Passing an unrelated suite
cannot establish an untested behavior.

Use the [shared canonical status definitions](../../../references/evidence-contract.md)
when statuses are needed. A demonstrated required-behavior violation is
`not-satisfied`; passing other subclaims cannot dilute it. External delivery
needs external observation. Code or queue creation alone does not prove it.

For benchmark and independent evaluation work, do not read the tested project's
reference implementation, gold patch, hidden tests, installed copy, or another
checkout. Such leakage makes the affected result `not-verifiable`.
A clean evaluator pass does not repair contaminated provenance. Ordinary work
may inspect authorized dependencies and user-designated checkouts.

Do not manufacture a matrix for a one-line fix. For larger work, cover every
material requirement in the requested format and identify unimplemented,
deferred, or uninspected interfaces. Report relevant failed/skipped checks and
uncertainty without inventing missing API or product requirements.
