---
name: verified-delivery
description: Implement and verify with proportional evidence only when explicitly invoked as $wigtn-plugins-with-codex:verified-delivery; never auto-invoke for ordinary coding, specs, review, or Git requests.
---

# Verified Delivery

This workflow is explicit-only. Invocation authorizes in-scope implementation
and proportionate local verification, not Git, network, deployment, dependency
installation, or unrelated external mutations.

## Workflow

1. Read repository instructions, the requested behavior, adjacent code, and
   existing tests. If saved WIGTN state exists, validate it before trusting it.
2. Define observable completion and the verification boundary. Use a compact coverage census
   only when the request names multiple material requirements, files, symbols,
   or interfaces. Name high-risk invariants only when auth, tenancy, secrets, migration, persistence, concurrency,
   public schemas, or compatibility are actually involved.
3. Implement the smallest coherent change using repository-native patterns.
   Preserve unrelated edits. Do not inspect or copy another checkout, an
   installed distribution of the same project, a package cache, benchmark
   reference patch, hidden test, or gold implementation.
4. Run the smallest repository-native checks justified by the blast radius.
   Prefer a focused pre-existing check, then only broader checks that add
   evidence. Do not duplicate a passing repository oracle with an alternate
   harness. A new focused test is strong evidence only when its pre-change
   failure and post-change pass were both observed.
5. Review the final diff, changed interfaces, unexpected paths, debug
   artifacts, and whether checks exercise the requested failure mode.
6. For a small request, report changed behavior, exact checks, and the
   verification boundary. Read [delivery evidence](references/delivery-evidence.md)
   only for multiple material requirements, authored-test provenance,
   benchmark/evaluator work, or a requested saved evidence artifact.

## Evidence and state

- Passing visible checks do not prove unspecified APIs, schemas, hidden tests,
  external state, or unobserved compatibility.
- If source leakage occurs, mark the affected result `not-verifiable` even when
  an evaluator passes.
- Do not create stable IDs, WorkGraph state, or evidence JSON by default. Read
  [the shared evidence contract](../../references/evidence-contract.md) only
  for a requested saved artifact, an existing handoff, or cross-session work.
- A saved WorkGraph task remains `implemented` until its current linked check
  passes and a valid evidence reference exists.

## Authority boundary

Do not commit, push, open a PR or issue, deploy, install dependencies, or alter
remote state unless the user separately asks for that action. Never use
destructive rollback to discard a mixed dirty worktree.
