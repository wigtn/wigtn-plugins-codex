# Evidence Matrix Rules

- `verified`: all material behavior is present and a relevant executed check passes.
- `implemented-not-executed`: implementation evidence exists, but no relevant
  executable check ran successfully.
- `partially-verified`: a material subclaim is demonstrated and another remains
  unverified, with no demonstrated violation of the requirement.
- `not-satisfied`: evidence shows required behavior is absent or contradictory.
- `not-verifiable`: available artifacts cannot support a reliable conclusion.
- `not-applicable`: the requirement is outside the evaluated scope.

Prefer evidence in this order: executed behavior or test, implementation at a precise file/line, generated artifact, then documented intent. Documentation alone does not prove runtime behavior.

Before referencing a passing check, audit its relevance:

- confirm it exercises the implementation and behavior named by the
  requirement, not a legacy module or unrelated assertion
- treat a check that asserts behavior contradicting the authoritative
  requirement as stale evidence, even when it passes
- exercise relevant state transitions, ordering and boundaries. Repeat checks
  when intermittency or timing uncertainty warrants it; three identical passes
  do not establish coverage. Investigate any inconsistent result before
  claiming `verified`
- a focused direct runtime assertion may verify a small observable requirement
  when no test file exists, but record its exact command and cases
- repository evidence can verify that an external action was queued; it cannot
  prove third-party delivery or state that was not observed

Before choosing a status, split compound language into observable subclaims
(for example, negative and zero boundaries; enqueue and third-party delivery).
Record which subclaims passed, failed, or could not be observed. Then collapse
them to one requirement status:

- first use `not-satisfied` if evidence demonstrates a required behavior is
  absent or violated; passing other cases cannot soften that conclusion
- use `partially-verified` when a material subclaim has direct implementation
  or runtime evidence, another cannot be observed, and no required behavior
  has been demonstrated false
- accepting allowed inputs does not partially establish a missing rejection
  constraint; the required denial or rejection is still violated
- use `not-verifiable` when no material subclaim can be concluded from
  available artifacts or permitted checks
- if an unreliable test fails intermittently but an independent focused
  runtime assertion covers every material observable subclaim, the assertion
  may still support `verified`; cite the flaky test separately as a test-suite
  gap

An irrelevant pass cannot soften a failure.

Use these same values in the human matrix and in any machine-readable handoff.
Localized labels may accompany them but must not replace the canonical value.
