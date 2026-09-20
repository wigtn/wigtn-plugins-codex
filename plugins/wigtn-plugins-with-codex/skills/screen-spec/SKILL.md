---
name: screen-spec
description: Create only the requested IA, user flow, screen spec, lo-fi HTML wireframe, or developer handoff from requirements. Use for “화면정의서”, IA, user flow, wireframe, or UI handoff requests. Build all five only for an explicit complete bundle. Do not use for styling alone or backend work.
---

# Screen Spec

Create the requested artifact at the user's chosen path and in their chosen
format. Existing IA, screen documents and routes are inputs; do not recreate
them as additional deliverables. Create the five-file WIGTN bundle only when
that bundle is requested.

## Scope and evidence

- Use a sufficient brief directly. Inspect repository routes, components,
  permissions and tokens when project-native behavior is requested or sources
  are named. Preserve source requirement IDs and confirmed routes.
- For screen behavior or handoff, read the compact
  [state contract](references/state-contract.md). For implementation handoff,
  also read [handoff contract](references/handoff-contract.md).
- Separate confirmed behavior from proposals and unresolved decisions. Do not
  invent API routes, roles, timing, retry limits or operational promises.
- Read a matching template in `assets/templates/` only when its format is useful
  for the requested output. Template dependencies do not authorize more files.
  Optional templates: [IA](assets/templates/01-IA.md),
  [flow](assets/templates/02-USER-FLOW.md),
  [screen](assets/templates/03-SCREEN-SPEC.md),
  [wireframe](assets/templates/04-WIREFRAME.html),
  [handoff](assets/templates/05-DEV-HANDOFF.md).

## Validation

For ordinary chat or custom Markdown, review the requested roles, states,
transitions, source links and open decisions directly. Do not run the WIGTN
bundle validator or change the output format merely to satisfy it.

For an explicitly requested WIGTN artifact set using its numbered filenames,
run `python3 ../../scripts/validate-screen-spec.py <directory> --artifacts <set> --json`
from this skill directory. This validator checks the legacy bundle's dependency
closure and headings; use it only when those companion artifacts are in scope.
Replace template placeholders and cross-check IDs and links between the
artifacts that actually exist.

For a requested lo-fi wireframe, produce one self-contained responsive grayscale
HTML file, using color for semantic status when useful.
Inspect wide and narrow layouts when browser tools are available; report which
render checks were performed. Do not claim implementation from a screen spec.

Return the requested artifact or file links, material open decisions and the
checks actually performed. Do not paste a full saved bundle into chat.
