---
name: verified-delivery
description: Run the complete WIGTN implementation-and-verification workflow when explicitly invoked as $wigtn-plugins-with-codex:verified-delivery from the installed plugin. Use only for an intentional end-to-end delivery request; never auto-invoke for ordinary coding, PRD writing, review, commit, push, or PR requests.
---

# Verified Delivery

This is an explicit-only delivery workflow. In the installed plugin, invoke it
with `$wigtn-plugins-with-codex:verified-delivery`. The invocation authorizes
implementation and proportionate local verification, not unrelated external
mutations.

## Workflow

1. Establish the goal, observable done criteria, repository instructions, and
   authority boundary. Convert material requirements to stable IDs when none
   exist.
2. Inspect adjacent implementation and tests. Before editing, name the
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
5. Run the focused test first, then the relevant repository-defined typecheck,
   lint, test, build, or browser check in proportion to blast radius. Record
   failures as evidence; fix in-scope causes and rerun.
6. Review the final diff after checks. Re-check the named invariants, changed
   public interfaces, unexpected paths, debug artifacts, and whether tests
   exercise the actual failure mode.
7. Apply [delivery evidence](references/delivery-evidence.md). A requirement is
   `Verified` only with precise implementation evidence and a passing
   executable check when one is feasible.

## Authority boundary

Do not create a commit, push, open a PR, create an issue, deploy, install dependencies, or alter remote state unless the user separately and explicitly asks for that action. Never use destructive rollback to discard a mixed dirty worktree.
