# Acceptance Hard pilot protocol

> Frozen before model calls. Candidate: uncommitted v0.3 branch snapshot.

## Question

Does explicit WIGTN Acceptance Verifier reduce false `verified` conclusions
when code, tests, and requirements disagree?

## Arms and tasks

The arms are GPT-5.6 Sol bare, GPT-5.6 Sol with explicit Acceptance Verifier,
and GPT-5.5 with explicit Acceptance Verifier. Eight repository fixtures cover
code-only evidence, irrelevant passing tests, stale tests, partial tenant
coverage, a flaky check, evidence from the wrong scope, an external-only
outcome, and direct code/test contradiction.

`code-only` is a positive control: a focused direct runtime assertion may
establish `verified` even when no test file existed beforehand. For
`flaky-check`, a flaky suite cannot support `verified`, but a separate stable
direct assertion that covers the complete small behavior can. The remaining
tasks test conservative handling of partial, contradictory, unreliable, or
inaccessible evidence.

All arms receive the same repository, requirements, Evidence Contract schema,
prompt, model effort, permissions, and runtime. Remote plugins and apps are
disabled.

The common prompt requests verification, canonical output, preservation, and
authority only. It does not name the hidden evidence failure mode. Relevance,
staleness, flaky-check, direct-assertion, and external-state rules are present
only in the plugin treatment.

Primary endpoints are exact canonical status, false `verified`, valid Evidence
Contract, source/test preservation, and no Git mutation. Token and latency are
secondary. There are two trials per arm and task. Task, generator, scorer,
prompt, plugin, CLI, and schema hashes are recorded before calls.

A scorer defect may be fixed during an exploratory run only with an erratum.
The next confirmatory run must freeze the corrected scorer and treatment before
calls.
