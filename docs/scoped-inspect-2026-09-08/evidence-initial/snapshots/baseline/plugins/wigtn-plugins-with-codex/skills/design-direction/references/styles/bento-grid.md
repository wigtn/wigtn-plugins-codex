# Bento Grid

Use for modular overviews where multiple independent features or metrics deserve
different visual weights. Do not use it as a default wrapper for unrelated copy.

## Direction contract

- Start with content priority, then assign spans. Limit the composition to 2–3
  card sizes so the grid reads as a system.
- Use a 12-column desktop grid, 6-column tablet grid, and a deliberate one- or
  two-column mobile order. DOM order must match the mobile reading order.
- Give each tile one job: metric, action, feature explanation, media, or status.
  Keep the title, value/content, and next action easy to scan.
- Share surface, border, radius, and spacing tokens. Vary emphasis through span,
  contrast, or media, not unrelated card styles.
- Reserve the darkest or accent surface for one or two high-priority tiles.
  Ensure text and focus contrast on every surface.
- Use consistent internal padding and align repeated data across cards.
- Let media fill a defined region with fixed aspect ratio. Avoid layout shifts.

## Interaction

- Whole-card clicks are appropriate only when the card has one destination.
  Multiple actions need explicit controls.
- Hover may lift or clarify a clickable tile by 1–2px; it must not be the only
  interaction cue.
- Keep entrance animation subtle and disable it for reduced motion. Do not
  stagger a long dashboard.
- Preserve keyboard order independent of visual CSS placement.

## Avoid

- A mosaic of identical cards, random spans, or every tile using a different
  gradient, icon container, and radius.
- Important data hidden in decorative imagery.
- Reordering with CSS in a way that breaks screen-reader or keyboard sequence.
- Bento layouts for long forms, articles, or linear tasks.

## Done when

Priority remains obvious at desktop and mobile widths, each tile has a single
purpose, the grid uses a small repeatable span vocabulary, and content growth or
localization does not overlap controls.
