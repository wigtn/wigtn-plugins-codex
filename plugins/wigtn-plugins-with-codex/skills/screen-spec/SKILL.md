---
name: screen-spec
description: Create only the requested implementation-ready IA, user flow, screen specification, lo-fi HTML wireframe, or developer handoff from a PRD or feature description. Use for “화면정의서”, “IA”, “user flow”, “wireframe”, or UI handoff requests. Generate the full five-artifact bundle only when the user requests a complete screen specification or handoff bundle. Do not use for visual styling alone or non-UI backend work.
---

# Screen Spec

Select the artifacts requested by the user:

- `ia` → `01-IA.md`
- `flow` → `02-USER-FLOW.md`
- `screen` → `03-SCREEN-SPEC.md` plus IA
- `wireframe` → `04-WIREFRAME.html` plus IA and screen spec
- `handoff` → `05-DEV-HANDOFF.md` and its full dependency closure
- complete “화면정의서”, bundle, or full handoff request → all five

Do not create unrelated artifacts merely because the skill was selected.

## Compact single-artifact path

For an IA-only or flow-only request:

- Treat a sufficient user-provided feature description as the source. Do not
  scan the repository unless the user requests project-native routes or points
  to source files.
- For a chat-only answer, do not read templates or references, create files,
  run validators, or perform browser checks. Return only the selected artifact.
- When a file is requested, read only its matching template, write only that
  file, and validate only the selected artifact.
- Keep IA to assumptions, a structured page map, navigation, access roles, and
  scope boundaries. The page map must contain `Page`/`페이지` plus
  `Route`/`경로` columns, or `정보 단위` plus `경로` columns.
- Stop after the selected artifact. Do not propose or summarize the other four.

## Multi-artifact workflow

1. Read the source PRD or feature description and relevant existing routes,
   components, permissions, and design system.
2. Preserve requirement IDs. Record safe inferences under `Assumptions`; ask
   only when a missing decision materially changes navigation or behavior.
3. Build the requested artifacts and required dependency closure from the
   templates in `assets/templates/`. Keep page IDs, routes, roles, states, and
   requirement IDs consistent across the artifacts that exist.
4. Cover only applicable states: loading, empty, error, success, unauthorized,
   validation, offline, and destructive confirmation.
5. Keep wireframes grayscale with semantic status colors only. If browser
   control is available, verify desktop and mobile widths, overflow, labels,
   and links before completion. Use the single self-contained responsive
   `04-WIREFRAME.html` template; do not create a second mobile artifact.
6. Run the selector-aware validator from this skill directory:

   `python3 ../../scripts/validate-screen-spec.py <directory> --artifacts <ia,flow,screen,wireframe,handoff|all>`

   Fix missing selected artifacts, unresolved template tokens, broken anchors,
   and requirement drift between artifacts that exist.
7. Return file links and deterministic plus visual verification results
   without pasting every artifact into the conversation.

Read [state checklist](references/state-checklist.md) only when screen,
wireframe, or handoff is selected. Read
[handoff checklist](references/handoff-checklist.md) only for handoff.
Read [microcopy patterns](references/microcopy-patterns.md) only when the user
requests UX copy or the selected screen/handoff contains material forms,
empty/error states, permission guidance, or destructive confirmation.
If a saved WorkGraph exists, preserve its requirement IDs and let
`work-planner` register the generated artifact set. Screen output never
verifies implementation.

Do not invent a visual brand. Suggest `design-direction` only when a new visual
direction is actually requested.
