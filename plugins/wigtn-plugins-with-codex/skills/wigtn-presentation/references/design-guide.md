# WIGTN Presentation Design

Use the host presentation workflow for narrative, citations, file generation,
and rendering. This guide supplies only WIGTN-specific composition decisions.

## Composition

- One slide communicates one audience-facing message.
- Use asymmetric alignment, deliberate whitespace, and a strong type hierarchy.
- Prefer one composition over repeated UI panels, badges, or card grids.
- Keep the purple signature consistent and subordinate to the message.
- Use `section-inverse` only for a real section boundary, never as random variety.

## Slide roles

| Role | WIGTN treatment |
|---|---|
| Cover | minimal title, canonical wordmark, one ink/purple structural element |
| Agenda | numbered list; only the number's period is purple |
| Section | large number and title; optional `section-inverse` |
| Body | title plus one clear composition: comparison, image/text, timeline, quote, or KPI |
| Closing | concise CTA or conclusion with the canonical wordmark |

Vary adjacent silhouettes. A deck should not repeat the same card grid or
two-column ratio on every slide.

## Visuals and diagrams

Follow the host presentation workflow's visual and diagram rules for the
selected output format. Use native presentation shapes or its supported diagram
route for PPTX/Slides. Use CSS or inline SVG only for an explicitly requested
HTML deck.

Do not invoke `handdrawn-diagram` merely because a slide needs a diagram. Use
that skill only when the user explicitly requests a sketch or hand-drawn
aesthetic, then treat the verified SVG/PNG as a presentation asset.

## Motion

Use restrained 0.2–0.4 second fades or short vertical movement. Limit each
slide to one or two entrance patterns. Respect reduced-motion settings in HTML.
Do not use decorative parallax, perpetual motion, or heavy glow.

## Final review

Inspect every rendered slide at full size. Fix overflow, clipping, unintended
overlap, title wrapping, weak contrast, inconsistent signature placement, logo
distortion, and font substitution. Use a contact sheet only for deck-level
rhythm; it does not replace per-slide inspection.
