# PRD Review Contract

Emit this table before semantic findings. Use only `Present`, `N/A`, or
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

Return at most five `blocker`, `high`, or grouped `medium` findings. Omit
low/nit findings, cite exact sections or IDs, and do not use numeric quality
scores.
