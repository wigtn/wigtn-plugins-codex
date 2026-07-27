---
name: product-spec
description: Create, review, or deeply analyze an actual implementation-ready PRD or product-spec artifact. Use for “PRD 뽑아줘”, “PRD 검토해줘”, “PRD 디깅해줘”, drafting requirements or acceptance criteria, and feasibility, security, edge-case, or contradiction review of a provided spec. Do not use for conceptual explanations of product terms, brainstorming without a requested requirements artifact, ordinary implementation, minor fixes, or general code review.
---

# Product Spec

Turn product intent into a traceable implementation contract. Do not make PRD
work a gate for ordinary coding.

## Mode

- **Create:** read [create contract](references/create-contract.md). Include only
  applicable sections. Mark each conditional contract `Required` or `N/A` with
  evidence.
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
  skill directory. Report failures; never weaken the contract to make it pass.

## Completion

Return the artifact or findings, important assumptions, unresolved decisions,
and validator result when run. Do not claim validation beyond inspected
evidence.
