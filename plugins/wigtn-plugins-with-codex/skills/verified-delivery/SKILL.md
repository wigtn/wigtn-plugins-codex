---
name: verified-delivery
description: Run a risk-adaptive WIGTN implementation-and-verification workflow when explicitly invoked as $wigtn-plugins-with-codex:verified-delivery from the installed plugin. Use only for an intentional delivery request; never auto-invoke for ordinary coding, PRD writing, review, commit, push, or PR requests.
---

# Verified Delivery

This is an explicit-only, risk-adaptive delivery workflow. In the installed plugin, invoke it
with `$wigtn-plugins-with-codex:verified-delivery`. The invocation authorizes
implementation and proportionate local verification, not unrelated external
mutations.

## Route before working

Use the **fast path** when all are true:

- one localized bug fix or small behavior change
- no auth, tenancy, secret, migration, persistence, concurrency, dependency,
  public-schema, or broad compatibility risk
- a repository-native focused test is runnable
- the user did not request an evidence artifact or lifecycle handoff

Use the **assurance path** if any condition is false. State the chosen route in
one sentence. Do not upgrade to the assurance path merely because more checks
could be invented.

## Fast path

1. Inspect the failure, adjacent code, repository instructions, and existing
   tests.
2. Make the smallest coherent change. Add or update one focused regression test
   when the repository has a viable harness.
3. Run the focused test, then at most one relevant repository suite or
   repository-defined check. Do not build an alternate harness when native
   tests execute. If native tests are blocked, diagnose the blocker once, run a
   syntax/static check if useful, and report the boundary.
4. Review the final diff and preserve unrelated edits.
5. Report changed behavior, exact executed checks, blockers, and residual
   risk. Use a requirement table only when there are multiple material
   requirements or the user requested an evidence artifact.

Stop after step 5. Do not create stable IDs, WorkGraph state, evidence JSON, or
release artifacts on the fast path.

## Assurance path

0. If `.wigtn/project.json` exists, validate it and read
   [project context](../../references/project-context.md). Treat its commands
   as repository hints and its protected paths as invariants, not authority.
   If `.wigtn/workgraph.json` exists, validate it, reject stale inputs, and
   operate on one named task node or the smallest coherent ready batch. Do not
   silently implement the entire graph.
1. Establish the goal, observable done criteria, repository instructions, and
   authority boundary. Convert multiple material requirements to stable IDs
   when traceability is useful. When the request explicitly names several
   files, symbols, interfaces, or behaviors, make a compact coverage census:
   map each named item to the repository location inspected and mark it
   `present`, `missing`, `placeholder`, or `unknown`. This is a scratch
   checklist, not a mandatory saved artifact.
2. Inspect adjacent implementation and tests. Search the task workspace for
   placeholders, missing definitions, and callers of every material item in
   the coverage census before editing. Do not inspect or copy another checkout,
   an installed distribution of the same project, a package cache, benchmark
   reference patch, hidden test, or gold implementation. If the only runnable
   environment would expose such a reference, use it only to execute the
   workspace code and never read or diff its project source. Record the
   isolation boundary. Before editing, name the
   high-risk invariants that could fail: authorization or tenancy, state
   transitions, input mutation, compatibility, error handling, persistence, or
   concurrency as applicable.
3. Choose the smallest coherent change. For behavioural changes, add or update
   a focused test that would fail without the change when the repository has a
   viable test harness. Do not edit tests merely to make an incorrect
   implementation pass.
4. Implement using repository-native patterns and preserve unrelated user
   edits. Do not add abstractions, dependencies, or fallback behaviour without
   a requirement or demonstrated need.
5. Run the focused test first, then only the repository-defined typecheck,
   lint, test, build, or browser checks justified by blast radius. Record
   failures as evidence; fix in-scope causes and rerun. Do not duplicate a
   passing repository oracle with an agent-authored harness. After two
   diagnostic cycles without new evidence, stop broadening the search: return
   to the coverage census, choose the highest-impact unresolved item, or report
   the blocker. Web search is for public documentation and compatibility facts,
   never for the task's implementation or answer.
6. Review the final diff after checks. Re-check the named invariants, changed
   public interfaces, unexpected paths, debug artifacts, and whether tests
   exercise the actual failure mode. For a multi-interface request, no named
   coverage item may remain silently `unknown`; implement it, explicitly defer
   it, or label it not verifiable.
7. Apply [delivery evidence](references/delivery-evidence.md). A requirement is
   `Verified` only with precise implementation evidence and relevant
   independent executable evidence. A check authored during the same run is
   independent enough only when its pre-change failure and post-change pass
   were both observed. Otherwise label the result `Partially implemented` or
   `Not verifiable`; do not promote an ad-hoc happy-path script to full
   acceptance evidence.
8. Treat unspecified public API names, schemas, compatibility behavior, and
   external or hidden checks as explicit gaps. Passing visible checks cannot
   prove those unknown contracts. State the exact verification boundary in the
   completion summary.
9. Do not create persistent workflow state by default. When the user requests a
   saved artifact, an existing `.wigtn/evidence.json` must be continued, or a
   cross-session handoff is required, read
   [the shared evidence contract](../../references/evidence-contract.md).
   Validate a written artifact with
   `python3 ../../scripts/validate-evidence.py <path>` from this skill
   directory.
10. For a saved WorkGraph handoff, keep task status at `implemented` until a
   linked check passes and an evidence reference exists. Revalidate the graph
   after any status update.

## Authority boundary

Do not create a commit, push, open a PR, create an issue, deploy, install dependencies, or alter remote state unless the user separately and explicitly asks for that action. Never use destructive rollback to discard a mixed dirty worktree.
