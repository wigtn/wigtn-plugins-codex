---
name: handdrawn-diagram
description: Create committable sketch-style architecture or flow diagrams as Mermaid handDrawn source plus verified SVG and PNG. Use when the user explicitly requests a 손그림, sketch, hand-drawn, or handDrawn aesthetic, including Devpost assets with that stated style. Do not use for an ordinary diagram, chart, presentation diagram, or bitmap illustration without a sketch-style request.
---

# Hand-drawn Diagram

Create a legible diagram whose text survives rendering, including Korean and mixed CJK/Latin labels.

## Workflow

1. Confirm the system boundary, groups, flow direction, and output location from context. Keep the smallest useful node set.
2. Author Mermaid with `look: handDrawn`, quoted labels, concise accessible title and description, and semantic colors.
3. Prefer a repository-installed or already available Mermaid CLI and record `mmdc --version`. Never run a floating `npx -y` download. If no renderer exists, request approval before any exact-version network installation.
4. Render both SVG and PNG using the [render guide](references/rendering.md).
5. Run `python3 scripts/verify-artifacts.py <source.mmd> <diagram.svg> <diagram.png>` from this skill directory.
6. Inspect the PNG visually. Check clipped Korean/English labels, overlaps, contrast, arrow direction, and group meaning. Revise and rerender until legible.
7. Return links to source, SVG, and PNG, the renderer version, and the render command. Do not commit unless separately requested.

Avoid hand-editing generated SVG when the Mermaid source can be corrected instead.
