---
name: product-spec
description: Create, review, or deep-dive an implementation-ready PRD or product spec. Use for “PRD 뽑아줘”, “PRD 검토해줘”, “PRD 디깅해줘”, requirements, acceptance criteria, and spec feasibility or contradiction review. Do not use for brainstorming without an artifact, implementation, minor fixes, or general code review.
---

# Product Spec

Turn product intent into a traceable implementation contract. Do not make PRD
work a gate for ordinary coding.

## Mode

- If `.wigtn/project.json` exists, validate it and read
  [project context](../../references/project-context.md). An explicit user
  profile overrides `prd_profile`; missing context changes nothing.
- **Create:** read [create contract](references/create-contract.md). Use Compact
  by default. Use Full only when the user requests it or the product actually
  needs multiple route/state contracts, a multi-step lifecycle, evidenced
  NFRs, phased delivery, or migration planning. Mark Full conditional
  contracts `Required` or `N/A` with evidence.
- **Review:** read [review contract](references/review-contract.md). Emit its
  contract-audit table, then at most five material findings. Do not rewrite
  unless asked.
- **Deep dive:** read the review contract and
  [deep-dive guide](references/deep-dive.md). Inspect repository evidence when
  available and label facts, inferences, and open questions.

## Rules

- Use stable requirement IDs and observable acceptance criteria.
- Treat server authorization, ownership, and tenancy as product behavior where
  applicable. UI hiding is not authorization.
- Do not invent scale, SLA numbers, architecture, analytics, or compliance
  requirements without evidence.
- Keep the contract proportional to the brief. Avoid repeated requirements,
  speculative policy, and exhaustive low-impact edge-case catalogs.
- Respect an explicit request for a concise artifact. Use Compact rather than
  shrinking a Full artifact cosmetically. Compact allows no more than eight
  material FRs and ten acceptance criteria.
- Do not promote plausible product choices—identity matching, token rotation,
  retry policy, route shape, or similar—into requirements. Keep unsupported
  choices as compact open decisions.
- Ask only about decisions that materially change implementation or release.
  Record reversible assumptions and continue.
- Preserve source documents unless the user asks to edit them.
- In reviews, `Present` means the required artifact exists, not that it is
  flawless. Report defects in that artifact as findings; do not relabel it
  `Missing`.
- Omit low/nit findings. Group related medium findings and return no more than
  five material findings, ordered by impact with exact section or requirement
  IDs.
- After saving a PRD, run `python3 scripts/validate-prd.py <path>` from this
  skill directory. The validator reads the profile marker. Report failures;
  never weaken the contract to make it pass.
- Do not create a machine-readable evidence sidecar for an ordinary PRD answer.
  When the user requests a saved evidence artifact, an existing
  `.wigtn/evidence.json` must be continued, or a cross-session handoff is
  required, read [the shared evidence contract](../../references/evidence-contract.md).
  A product spec does not prove implementation: record its requirements as
  `not-verifiable` until code and executed-check evidence exists.
- When the user explicitly asks to continue from the PRD into a saved
  implementation plan, hand off stable requirement IDs to `work-planner`.
  Do not create implementation tasks inside the PRD itself.

## Completion

Return the artifact or findings, important assumptions, unresolved decisions,
and validator result when run. Do not claim validation beyond inspected
evidence. When a shared evidence artifact was written, validate it with
`python3 ../../scripts/validate-evidence.py <path>` from this skill directory.
