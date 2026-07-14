---
name: product-spec
description: Create, review, or deeply analyze implementation-ready PRDs. Use for “PRD 뽑아줘”, “PRD 검토해줘”, “PRD 디깅해줘”, product requirements, specs, acceptance criteria, feasibility, security, edge-case, or contradiction review. Do not use for ordinary implementation, minor fixes, or general code review.
---

# Product Spec

Turn product intent into a traceable implementation contract without making PRD work a gate for ordinary coding.

## Choose the mode

- **Create**: the user asks for a new PRD, product brief, requirements, or acceptance criteria.
- **Review**: the user asks to review an existing PRD. Find omissions, contradictions, ambiguity, unverifiable acceptance criteria, and avoidable scope.
- **Deep dive**: the user asks to “디깅”, challenge, stress-test, or deeply analyze a PRD. Inspect the repository when available and test feasibility, security, failure modes, migrations, operations, data boundaries, and opposing hypotheses.

Do not turn a review or deep dive into a rewrite unless the user asks. Report findings first, ordered by impact, with exact section or requirement IDs.

## Workflow

1. Find applicable repository instructions, existing product docs, adjacent code, routes, schemas, and tests.
2. Establish the target user, problem, desired outcome, boundaries, and evidence already available.
3. Ask only about choices that materially change the result and cannot be safely inferred. Record reversible assumptions and continue.
4. Use stable requirement IDs. Keep solution detail proportional to evidence; do not invent enterprise scale, SLAs, or architecture.
5. Make acceptance criteria observable and testable. Connect UI requirements to roles, routes, states, and permissions.
6. In create mode, run the review checklist before saving. In deep-dive mode, use the deep-dive lenses and distinguish facts, inferences, and open questions.
7. Save a new PRD under the project’s existing docs convention, or default to `docs/product/<feature>-prd.md`. Preserve the source PRD unless the user asked to edit it.

Read [PRD template](references/prd-template.md) when creating. Read [review checklist](references/review-checklist.md) for every mode. Read [deep-dive guide](references/deep-dive.md) only for deep-dive requests.

## Completion

Return the file path, important assumptions, and unresolved decisions. After creating a PRD, end with concise optional next steps instead of automatically running them:

- **권장:** “이 PRD 디깅해줘” — 저장소 적합성, 누락, 모순, 보안과 엣지케이스 심층 검토
- **UI가 있으면:** “이 PRD로 화면정의서 만들어줘”
- **구현 준비가 됐으면:** explicitly invoke `$verified-delivery` or ask for ordinary implementation

Do not claim validation beyond the evidence actually inspected.
