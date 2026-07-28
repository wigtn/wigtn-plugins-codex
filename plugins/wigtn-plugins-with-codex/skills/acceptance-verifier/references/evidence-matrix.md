# Evidence Matrix Rules

- `Satisfied`: all material behavior is present and evidence directly supports it.
- `Partially satisfied`: a material subclaim is demonstrated but another
  material subclaim fails or remains unverified.
- `Not satisfied`: evidence shows required behavior is absent or contradictory.
- `Not verifiable`: available artifacts cannot support a reliable conclusion.

Prefer evidence in this order: executed behavior or test, implementation at a precise file/line, generated artifact, then documented intent. Documentation alone does not prove runtime behavior.

Before referencing a passing check, audit its relevance:

- confirm it exercises the implementation and behavior named by the
  requirement, not a legacy module or unrelated assertion
- treat a check that asserts behavior contradicting the authoritative
  requirement as stale evidence, even when it passes
- for state-, order-, random-, or time-dependent behavior, rerun the check at
  least three times; any inconsistent result blocks `verified`
- a focused direct runtime assertion may verify a small observable requirement
  when no test file exists, but record its exact command and cases
- repository evidence can verify that an external action was queued; it cannot
  prove third-party delivery or state that was not observed

Before choosing a status, split compound language into observable subclaims
(for example, negative and zero boundaries; enqueue and third-party delivery).
Record which subclaims passed, failed, or could not be observed. Then collapse
them to one requirement status:

- use `Partially satisfied` only when at least one material subclaim has direct
  implementation or runtime evidence and another material subclaim fails or
  cannot be observed
- use `Not satisfied` when the central named behavior is absent or
  contradictory; a degenerate input that never exercises that behavior is not
  a material subset
- use `Not verifiable` when no material subclaim can be concluded from
  available artifacts or permitted checks
- if an unreliable test fails intermittently but an independent focused
  runtime assertion covers every material observable subclaim, the assertion
  may still support `Satisfied`; cite the flaky test separately as a test-suite
  gap

An irrelevant pass cannot soften a failure.

When a machine-readable handoff is requested, use the canonical status mapping
in the parent skill and the plugin-level Evidence Contract. The human label
`Satisfied` is intentionally split: it becomes `verified` only with a relevant
passing check and otherwise becomes `implemented-not-executed`.
