---
name: screen-spec
description: Create only the requested IA, user flow, screen spec, lo-fi HTML wireframe, or developer handoff from requirements. Use for “화면정의서”, IA, user flow, wireframe, or UI handoff requests. Build all five only for an explicit complete bundle. Do not use for styling alone or backend work.
---

# Screen Spec

Select the requested artifact and its dependency closure:

- `ia` → `01-IA.md`
- `flow` → `02-USER-FLOW.md`
- `screen` → `03-SCREEN-SPEC.md` plus IA
- `wireframe` → `04-WIREFRAME.html` plus IA and screen
- `handoff` → `05-DEV-HANDOFF.md` plus all dependencies
- explicit complete bundle → all five

Do not produce or propose the other artifacts merely because the skill loaded.

## IA-only or flow-only

- Use a sufficient user brief directly. Inspect repository routes only when
  project-native behavior is requested or source files are named.
- For chat-only output, do not read templates, create files, run validators,
  or perform browser checks.
- For a file, read only its matching template and validate only that artifact.
- IA needs assumptions, a page/route map, navigation, roles, and boundaries.
  Stop after the requested artifact.

## Multi-artifact workflow

1. Read the requirements and only the existing routes, components,
   permissions, and tokens needed for the selected artifacts.
2. Preserve requirement IDs. Mark unsupported routes, policies, breakpoints,
   APIs, and copy as assumptions or open decisions rather than defaults.
3. Read only the selected templates in `assets/templates/` and their dependency
   templates. Treat placeholders as shape, never as product facts.
4. Keep page IDs, roles, routes, states, requirements, and wireframe anchors
   consistent across the artifacts that exist.
5. For screen, wireframe, or handoff, read the compact
   [state contract](references/state-contract.md). For handoff, also read the
   [handoff contract](references/handoff-contract.md).
6. Keep wireframes grayscale with semantic status colors and one self-contained
   responsive HTML file. If browser control is available, inspect wide and
   narrow layouts, overflow, labels, and links.
7. Run from this skill directory:

   `python3 ../../scripts/validate-screen-spec.py <directory> --artifacts <selection|all>`

8. Return file links and deterministic plus visual results without pasting the
   full bundle into chat.

Use project-native language for microcopy. Prefer explicit action labels and a
useful recovery action; do not invent timing, policy, ownership, or operational
promises. Screen artifacts describe intended behavior and never verify its
implementation. Suggest `design-direction` only for an actual visual-direction
request.
