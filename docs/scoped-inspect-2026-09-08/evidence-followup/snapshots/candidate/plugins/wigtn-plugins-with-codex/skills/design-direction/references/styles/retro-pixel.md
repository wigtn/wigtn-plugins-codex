# Retro Pixel

Use for playful, game-like, or nostalgic products where the visual metaphor
supports the audience. Keep modern usability under the pixel treatment.

## Direction contract

- Choose one era and resolution logic. Define a small spacing unit, pixel border
  width, corner treatment, and shadow step; use them consistently.
- Use a pixel display face for short headings or labels and a highly legible
  companion for body text. Never render essential copy at simulated low resolution.
- Limit the palette to a coherent 8–16 color set with explicit roles for canvas,
  surface, ink, accent, and semantic states.
- Scale raster art by integer multiples with nearest-neighbor rendering. Provide
  high-density assets and reserve dimensions to prevent layout shift.
- Use panels, inventory-like grids, progress meters, or dialogue structures only
  when they map to real product behavior.
- Preserve ordinary labels, form semantics, and navigation. The interface may
  look game-like without making users guess the controls.
- Pair status colors with text, shape, or icon. Check contrast rather than
  assuming a bright palette is accessible.

## Interaction

- Use short stepped transitions, sprite changes, or 1–2 frame press feedback.
- Disable blinking, screen shake, and looping sprites for reduced motion.
- Keep touch targets modern-sized even when their visible art is compact.
- Provide a clear focus indicator separate from decorative selection frames.

## Avoid

- Mixing 8-bit, 16-bit, CRT, vaporwave, and modern glass effects on one screen.
- Pixel fonts for paragraphs, fake loading delays, excessive sound, or animated
  backgrounds behind text.
- Blurry non-integer asset scaling and inaccessible red/green state pairs.
- Nostalgia that obscures checkout, authentication, settings, or destructive actions.

## Done when

The era and pixel system are internally consistent, all real text is readable,
the UI remains usable with animation and sound off, assets render crisply across
target densities, and task completion does not depend on game literacy.
