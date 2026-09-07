# PRD Review Contract

First identify the declared Compact/Full profile and the user’s requested
review scope. Review Compact against its own sections, requirement IDs and
acceptance criteria; do not require Full-only artifacts. For an external PRD,
review the supplied contract unless the user asks for WIGTN conformance.
For a Full WIGTN contract audit, emit the following table before semantic findings. Use only `Present`, `N/A`, or
`Missing`; `N/A` requires evidence from the PRD.

| Contract | Status | Evidence |
|---|---|---|
| Applicability ledger |  |  |
| Pages and routes |  |  |
| Empty/loading/error/success/recovery state matrix |  |  |
| Mermaid user or system flow |  |  |
| Acceptance precondition/action/result mapped to requirement IDs |  |  |
| Delivery phases mapped to requirement IDs and exit conditions |  |  |

Status semantics:

- `Present`: the artifact exists in recognizable form. Imperfect, incomplete,
  or internally defective content is still `Present`; describe the defect in a
  finding.
- `Missing`: an applicable artifact does not exist. Do not use it as a quality
  rating.
- `N/A`: the contract is not applicable and the PRD provides supporting
  evidence.

Applicability:

- A user-visible feature makes pages/routes and the state matrix applicable.
- A multi-step user or system lifecycle makes Mermaid flow applicable.
- Backend-only work must not invent screens.
- `Missing` on an applicable WIGTN contract is a finding even when the rest of
  the PRD is sound.

Then review universal quality: contradictions, authorization/data boundaries,
state transitions, failure/recovery, unverifiable acceptance, unsupported
scope, migration, operations, privacy, and security only where relevant.

Report all material `blocker` and `high` findings; group related `medium`
findings. Omit low/nit findings unless requested, cite exact sections or IDs,
and do not use numeric quality scores.
