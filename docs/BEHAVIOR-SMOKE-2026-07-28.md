# Codex Plugin Behavior Smoke — 2026-07-28

## Executive conclusion

This smoke test does not support the claim that the plugin generally improves
Codex output quality or efficiency.

It does support a narrower claim: on the tested PRD request, the plugin made
GPT-5.5 and GPT-5.6 Sol conform to WIGTN's implementation-ready PRD contract.
That gain came with materially longer outputs, higher median latency, and
usually higher reported token use. On an easy acceptance-verification case and
an ordinary coding case, both bare and plugin arms already behaved correctly;
no quality lift was observed.

The resulting design decision is to keep the plugin selective:

- keep product and release contracts where artifact shape or authority matters
- keep `verified-delivery` explicit-only
- do not wrap ordinary coding in a global lifecycle
- make the Evidence Contract optional and handoff-driven
- treat latency and token overhead as first-class regressions

This is an engineering smoke report, not an academic efficacy result.

## Protocol

| Field | Value |
|---|---|
| Date | 2026-07-28 KST |
| CLI | `codex-cli 0.146.0-alpha.3.1` |
| Models | `gpt-5.6-sol`, `gpt-5.5` |
| Reasoning effort | `medium` |
| Arms | bare, locally installed plugin |
| Cases | concise PRD, evidence-uncertain acceptance, ordinary coding |
| Repeats | 3 per model × arm × case |
| Successful model runs | 36/36 |
| Permissions | read-only, approval policy `never` |
| Isolation | separate `CODEX_HOME`; remote plugins and apps disabled |

The runner checked prompt-input isolation before sampling: the bare arm did not
contain the WIGTN skill and the plugin arm did. Prompts and evaluated skill
bodies were hashed in each local run manifest. An earlier sandboxed attempt
could not resolve the model endpoint and was classified as infrastructure
failure, not as a model sample.

The runner received instrumentation-only hardening after the runs
(repository-relative manifest paths, complete plugin hashing, and model/effort
metadata). Evaluated prompts and skill bodies did not change after sampling.

## Quantitative smoke results

Values are medians of three runs. “Tokens” is the CLI-reported total and is
highly variable at this sample size. “Bytes” measures the final response, not
reasoning.

### GPT-5.6 Sol

| Case | Arm | Contract/outcome | Tokens | Duration | Output bytes |
|---|---|---|---:|---:|---:|
| PRD | bare | WIGTN PRD validator 0/3 | 3,394 | 35s | 5,018 |
| PRD | plugin | WIGTN PRD validator 3/3 | 17,481 | 79s | 7,853 |
| uncertain acceptance | bare | conservative 3/3 | 1,126 | 8s | 890 |
| uncertain acceptance | plugin | conservative 3/3 | 3,795 | 16s | 968 |
| ordinary coding | bare | lean response 3/3 | 1,982 | 6s | 383 |
| ordinary coding | plugin | lean response 3/3 | 3,263 | 7s | 396 |

### GPT-5.5

| Case | Arm | Contract/outcome | Tokens | Duration | Output bytes |
|---|---|---|---:|---:|---:|
| PRD | bare | WIGTN PRD validator 0/3 | 8,257 | 28s | 4,849 |
| PRD | plugin | WIGTN PRD validator 3/3 | 13,024 | 56s | 8,653 |
| uncertain acceptance | bare | conservative 3/3 | 7,500 | 10s | 1,105 |
| uncertain acceptance | plugin | conservative 3/3 | 3,848 | 26s | 1,196 |
| ordinary coding | bare | lean response 3/3 | 2,281 | 9s | 779 |
| ordinary coding | plugin | lean response 3/3 | 509 | 8s | 678 |

The GPT-5.5 token reversals on two cases and the large within-arm variance show
why three repeats are inadequate for a general efficiency claim. Latency and
response-size direction are more consistent: the PRD contract costs more in
both model generations.

## Interpretation

### What is supported

1. The installation isolation works for the tested setup.
2. The PRD skill enforces its own artifact contract on this prompt.
3. Neither model/arm falsely passed the deliberately evidence-poor acceptance
   case.
4. The plugin did not turn the ordinary coding prompt into PRD, release, or
   heavy delivery work.
5. The static Evidence Contract suite rejects nine distinct invalid states and
   accepts one valid state.

### What is not supported

1. The PRD validator is treatment-aligned. A 3/3 versus 0/3 result proves
   contract conformance, not that independent reviewers prefer the plugin PRD.
2. The acceptance case was easy enough for the bare model. It cannot establish
   verifier lift.
3. Read-only answer prompts do not establish implementation correctness,
   hidden-test performance, or Git safety.
4. Three repeats per cell do not estimate stable latency or token distributions.
5. No external evaluator or independent repository replicated these results.

## Plugin changes caused by the smoke

An initial one-repeat run showed that the plugin ignored the word “concise” and
expanded plausible identity and token choices into policy. `product-spec` was
therefore tightened to:

- cap concise artifacts at normally eight material FRs and ten ACs
- keep required table shapes while compressing prose
- move unsupported identity, token, retry, route, and expiry choices to open
  decisions

The confirmatory three-repeat plugin outputs stayed within the FR/AC caps, but
remained substantially longer than bare outputs because the full WIGTN
contract still requires applicability, states, flow, authorization, risks, and
delivery. Further reduction should be judged by blind task usefulness, not by
deleting contract fields solely to lower token count.

## Cold assessment

| Dimension | Current score | Reason |
|---|---:|---|
| plugin engineering | 6/10 | narrow skills, explicit authority, validators, optional evidence handoff |
| benchmark rigor | 4/10 | paired isolation, hashes, repeats, deterministic negatives; tiny task set |
| publication readiness | 4/10 | honest claim boundary and reproducible runner; no committed raw packet or external replication |
| general quality-lift evidence | 2/10 | PRD contract lift only; no implementation lift demonstrated |

The work is report-worthy as a transparent engineering result about selective
harness design. It is not yet credible as “our plugin makes strong coding
models better.”

## Required confirmatory work

Before making a general quality claim:

1. Freeze at least 12 implementation tasks across 3 or more real disposable
   repositories, with visible and model-hidden tests.
2. Run same-model bare, ordinary-plugin, and explicit
   `verified-delivery` arms for GPT-5.5 and GPT-5.6 Sol.
3. Freeze an `auto-commit` suite using real Git state, dirty user-file
   sentinels, exact staged paths, commit hashes, and unauthorized mutation
   counts.
4. Add hard acceptance cases where implementation exists but the test is
   missing, irrelevant, flaky, or contradicts documentation.
5. Export a sanitized raw-output packet and scorer hashes before analysis.
6. Use at least two blinded reviewers and report agreement, disagreements, and
   confidence intervals alongside deterministic outcomes.
7. Replicate on an external repository or by an evaluator who did not author
   the plugin.

Until those gates pass, the correct product claim is:

> WIGTN adds optional product, evidence, and release contracts to Codex while
> leaving ordinary coding mostly untouched. It improves contract consistency
> in tested PRD tasks; broader quality and efficiency gains remain unproven.
