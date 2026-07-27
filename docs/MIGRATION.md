# Migration from the Claude Code Plugin

This repository is a selective rewrite, not a directory-for-directory port.

## Reused and adapted

- `screen-spec` templates and state/handoff references: retained as proven product documentation assets; Claude-specific `/implement` language was removed.
- `design-system-reference`: reduced from 20 styles to nine focused style references plus WIGTN Brand. Generic Brutalist and Minimalism are excluded because clearer variants already cover them.
- `handdrawn-diagram`: retained the Mermaid handDrawn, CJK clipping, semantic color, and rendered-image verification knowledge; automatic `npx -y` and commit behavior were removed.
- `wigtn-ppt`: brand palette and presentation design guidance moved to `wigtn-presentation`; invocation is limited to explicit WIGTN branding.

## Rewritten

- Claude commands and role agents are replaced by eight Codex skills.
- `prd-reviewer` and `parallel-digging-coordinator` become create, review, and deep-dive modes inside `product-spec`.
- `auto-commit` and PR review logic become `release-readiness`, with natural-language scope mapping and no numeric quality gate.
- `/implement` becomes explicit-only `verified-delivery`; ordinary coding remains free of plugin ceremony.

The 2026 GPT-5.5/5.6 Sol study supports this split: all four implementation
arms passed 12/12 visible and hidden tests, while explicit verified delivery
used more tokens than GPT-5.6 bare. It therefore remains an opt-in evidence
workflow, not the default coding path. In contrast, GPT-5.6 bare made an
unauthorized commit in 3/3 ambiguous “완료해줘” trials, so the compact release
authority contract remains mandatory.

## Not migrated

- Claude-specific tool names, commands, fixed subagent fan-out, team-memory protocol, lifecycle hooks, model routing, automatic dependency installation, and destructive rollback.
