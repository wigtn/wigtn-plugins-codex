# SWE-Skills-Bench external pilot

This pilot measures the marginal effect of the current WIGTN Codex skill
bundle on an independently authored task and test suite.

## Pinned source

- Benchmark: `GeniusHTX/SWE-Skills-Bench`
- Benchmark commit: `95b3ce519fcb58d0b19e90a5b6e5165211dc6dd1`
- Task: `batch1/tdd-workflow`
- Target repository: `tdd-starters/python`
- Target commit: `a1a2d04ae69bd50aba9dac2783737dfda8f048c9`
- Evaluation image:
  `zhangyiiiiii/swe-skills-bench-python@sha256:51d40310cdf44d00b3e383af1c4467bc460e6a3a25fedb1f9fab6a8d7b77b974`
- External test: `tests/batch1/test_tdd_workflow.py`

The test file is never copied into the Codex worktree. It is mounted read-only
only after each run.

## Arms

| Arm | Candidate skills visible | Prompt |
|---|---:|---|
| `bare` | No | Original external task |
| `plugin` | Yes, repo-local symlink to current candidate | Original external task |
| `explicit` | Yes, repo-local symlink to current candidate | Explicitly invokes `verified-delivery`, then includes the original task |

All arms use `gpt-5.6-sol`, high reasoning, the same Codex CLI, the same target
commit, `workspace-write`, no approvals, no user config, no project execution
rules, no web search, and ephemeral sessions.

This is a one-task engineering pilot, not evidence of general quality lift.
Publication-grade inference requires preregistered repetitions across multiple
task families and independent repositories.

## Observed result

| Arm | External tests | Wall time | Output tokens | Commands |
|---|---:|---:|---:|---:|
| `bare` | 11/14 | 190s | 7,372 | 8 |
| `plugin` | 11/14 | 234s | 10,726 | 11 |
| `explicit` | 11/14 | 218s | 9,656 | 10 |

All three arms failed the same calls because the test requires the keyword
`promo_categories`, while the task text does not specify any public keyword
name. The raw score is retained, but those three checks are flagged as a
task-oracle mismatch. The audited interpretable score is 11/11 for every arm.

This run did not show a quality lift. It did show that explicit delivery
produced a stronger evidence trace but initially overstated verification based
on green-only, agent-authored checks. The candidate evidence policy was updated
after the run to prohibit that promotion.

A post-policy behavior recheck again scored 11/14. Its final answer explicitly
disclosed that the contract did not define an exact public signature and that
no hidden or external checks were available. It still labeled functional
requirements `Verified` after an agent-authored red-green check. The policy
therefore improved claim boundaries but does not yet machine-enforce an
independent-evidence status downgrade.

## Confirmatory limitations

- One task and one trial.
- Arms were run in parallel.
- The candidate skill tree was not content-snapshotted before execution.
- The result is a falsification pilot, not a confirmatory estimate.
