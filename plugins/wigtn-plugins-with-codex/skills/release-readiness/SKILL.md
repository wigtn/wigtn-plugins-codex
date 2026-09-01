---
name: release-readiness
description: Safely review, prepare, commit, push, or open a PR for explicit Git requests such as “커밋해줘”, “푸시해줘”, or “PR 올려줘”. Preserve unrelated changes and perform only the requested scope. Do not use for implementation or vague completion requests.
---

# Release Readiness

Interpret the user’s sentence as the authority boundary.

## Request mapping

- **“리뷰해줘”**: review and report only. Do not stage or commit.
- **“커밋 준비해줘”**: inspect, verify, and propose the exact scope and message. Do not commit.
- **“커밋해줘”**: inspect, verify, stage only in-scope files, and commit.
- **“푸시해줘”**: inspect status, run needed checks, and push the current intended branch; commit only if the request or context clearly includes committing the current changes.
- **“PR 올려줘”**: verify and perform the necessary in-scope commit and push, then create the PR.
- **“구현해줘”**: not a release request. Do not capture it and do not perform Git mutations.

When wording is ambiguous about a consequential mutation, stop before that mutation and ask.

## Workflow

0. If `.wigtn/project.json` exists, validate it and read
   [project context](../../references/project-context.md). Never stage its
   protected paths unless the current request explicitly includes them.
   If `.wigtn/workgraph.json` exists, validate it and inspect release-gate
   status. A ready gate is prerequisite evidence, not permission for Git or
   remote actions.
1. Read repository instructions. Run
   `python3 ../../scripts/inspect-release-state.py <repository>` from this skill
   directory to capture branch, upstream, operations, conflicts, staged,
   unstaged, and untracked paths without mutation. Then inspect the relevant
   staged and unstaged diffs.
2. Separate task changes from pre-existing or unrelated user work. Never silently include unrelated files.
3. Review for correctness, regression, security, and missing tests. Findings need severity, confidence, file/line, and impact.
4. Run relevant repository-defined verification. Record exact commands and results.
5. Execute only the mapped action. Use non-interactive Git commands and preserve hooks unless the user explicitly asks otherwise.
6. Report commit hash, pushed branch, or PR URL only after success.

Read [Git safety](references/git-safety.md) before any staging, commit, push, or PR operation. Never force-push, hard-reset, delete branches, amend, or rewrite history without explicit authorization.

## Machine-readable handoff

Do not create state for an ordinary release request. When the user requests a
saved release artifact, an existing `.wigtn/evidence.json` must be continued,
or a cross-session handoff is required, read
[the shared evidence contract](../../references/evidence-contract.md). The
artifact records authority; it never grants authority. Mark an external action
`performed` only after success and retain its commit, branch, or URL evidence.
Validate a written artifact with
`python3 ../../scripts/validate-evidence.py <path>` from this skill directory.
