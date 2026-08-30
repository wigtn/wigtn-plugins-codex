---
name: knowledge-wiki
description: Configure, inspect, manually run, or diagnose WIGTN’s opt-in Codex knowledge-wiki pipeline that turns reusable session learning into gated articles under per-user/. Use for “위키에 지식 쌓아줘”, “knowledge wiki 설정”, “세션 지식 자동 축적”, wiki capture diagnostics, or reviewing export safety. Do not enable capture, widen scope, push, or publish to shared/ without explicit user authorization.
---

# Knowledge Wiki

Operate the Codex-specific, opt-in knowledge capture pipeline. It turns a
completed turn into a generalized Korean article only when all safety gates
pass. Installing the plugin alone captures nothing.

## Boundaries

- Require an existing `knowledge-wiki-codex.yml` with `enabled: true`, at least
  one narrow `include`, a `wiki.path`, and a personal `wiki.subdir`.
- Treat configuration creation, enabling capture, widening `include`, enabling
  push, cloning a remote, and changing a wiki repository as separate mutations.
  Perform only the mutations the user requested.
- Never auto-publish under `shared/`. Automated targets are limited to
  `per-user/<name>`; promotion to `shared/` requires a human-reviewed pull
  request.
- Do not add the user home, filesystem root, customer repositories, NDA work,
  dependency trees, virtual environments, or the wiki repository itself to
  `include`.
- Never print transcript contents, queued jobs, credentials, or rejected text
  while diagnosing. Report only gate names and local status metadata.

## Setup workflow

1. Find the intended local clone of the team wiki. If it does not exist, ask
   before cloning or creating it.
2. Identify the smallest parent directory covering the authorized repositories.
   List sensitive children under `exclude`.
3. Start from
   `../../scripts/knowledge_wiki/knowledge-wiki.example.yml`. Create the config
   only after explicit authorization. Prefer
   `~/.config/wigtn/knowledge-wiki-codex.yml`.
4. Keep `publish.push: false` for the first verification. Set it to `true` only
   when the user explicitly requests automatic remote sharing and the include
   scope is narrow.
5. Reinstall the local plugin and start a new Codex task so the default
   `hooks/hooks.json` is loaded and trusted.

## Gate model

The `Stop` hook performs G0 scope resolution and G1 deterministic secret
blocking, writes a private job under `PLUGIN_DATA`, then exits quickly. A
detached single-worker queue performs G2 Codex generalization, G3 independent
semantic export audit, G4 deterministic output scanning, and local
write/commit/push. Nested Codex calls are ephemeral, read-only, ignore user
configuration and rules, and disable hooks to prevent recursion.

Every uncertain or malformed result fails closed. `SKIP` is a normal result for
routine sessions. See [the ingest policy](references/ingest-policy.md) for the
full contract.

## Diagnosis

Run the bundled read-only doctor first. Resolve the script relative to this
skill directory and never print queued job files:

```bash
python3 ../../scripts/knowledge_wiki/doctor.py --json
```

The doctor reports config scope counts, destination namespace, push state,
queue age/count, Codex availability, and body-free outcome counts. If the
plugin data directory is not inherited, pass its `knowledge-wiki` child with
`--state`. Inspect only metadata under `${PLUGIN_DATA}/knowledge-wiki/events/`:

- `G1`: the original turn contained a deterministic secret or irreversible
  identifier and was never sent to the compiler.
- `SKIP`: Codex found no reusable knowledge.
- `G2` or `G3`: nested Codex failed, timed out, or returned malformed output.
- `G4`: the generated article still contained an export-blocked pattern.
- `published`: the article was written; the detail says whether it was only a
  file, a local commit, or pushed.
- `failed`: processing failed; only the metadata event is retained for diagnosis.

Do not retry a rejected or failed job with weaker gates. Fix configuration or
runtime availability, then capture a later turn.

## Completion

Report the config path, authorized include/exclude scope, wiki target subdir,
whether push is enabled, plugin validation result, and whether a new Codex task
is required. Never claim publication without checking the local wiki Git state.
