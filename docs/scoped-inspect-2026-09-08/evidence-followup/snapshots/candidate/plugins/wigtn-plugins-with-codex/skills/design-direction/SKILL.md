---
name: design-direction
description: Derive a project-native UI direction from the existing design system. Use for visual direction, greenfield styling, or redesign requests. Do not use for small CSS fixes, established-component work, or non-UI tasks.
---

# Design Direction

Prefer the product’s existing visual language over a generic style preset.

## Workflow

1. Inspect tokens, global styles, fonts, representative pages, shared components, spacing, icons, and motion.
2. If a coherent system exists, summarize it and produce an implementation contract that extends it. Do not offer unrelated styles.
3. For greenfield work or an explicit redesign, use the stated preferences to choose a direction and proceed. Offer alternatives when the user asks to compare them or a missing choice materially changes the product; continue independent authorized work while awaiting that choice.
4. Read only the selected reference from `references/styles/`.
5. Produce a short contract covering typography, palette roles, spacing rhythm, surfaces, borders, interaction states, motion, accessibility, and anti-patterns.
6. Do not implement unless requested.

Available references are indexed in [style index](references/style-index.md). They are inspiration and constraints, not a license to overwrite repository conventions.
