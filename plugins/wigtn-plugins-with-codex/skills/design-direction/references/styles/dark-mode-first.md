# Dark Mode First

Use for technical, media, monitoring, or low-light products designed around dark
surfaces from the start. Dark mode is a contrast system, not a black background.

## Direction contract

- Define at least canvas, raised surface, overlay, subtle border, primary text,
  muted text, and semantic status tokens. Avoid pure black and pure white for
  large areas unless the existing brand requires them.
- Separate elevation with small lightness changes and borders before adding
  shadows. Test adjacent surfaces on ordinary displays.
- Use a neutral sans-serif for UI and monospace only for code, identifiers, or
  tabular technical data.
- Keep body text comfortably bright and muted text above WCAG contrast targets.
  Thin font weights usually underperform on dark backgrounds.
- Limit luminous accents to interactive focus and meaningful status. One primary
  accent plus semantic colors is usually enough.
- Charts need labeled series, distinguishable strokes or patterns, and tooltips
  that remain readable without relying only on hue.
- Inputs and code blocks need explicit boundaries; a darker rectangle alone is
  often insufficient.

## Interaction

- Focus rings should be brighter and thicker than quiet borders.
- Use glow only as a restrained secondary cue. Never blur text or status edges.
- Keep transitions under 200ms and stop pulses, scans, and floating effects for
  reduced motion.
- If a light theme exists, map semantic tokens instead of inverting colors.

## Avoid

- Neon on every control, large blurred gradients, star-field backgrounds, and
  “cyber” decoration unrelated to the product.
- Pure-gray hierarchy with no surface distinction.
- Color-only error/success states or low-opacity disabled text that becomes
  unreadable.

## Done when

All text and controls meet contrast targets, elevation remains clear without
glow, charts work for color-vision differences, and the interface is comfortable
at both low and normal ambient light.
