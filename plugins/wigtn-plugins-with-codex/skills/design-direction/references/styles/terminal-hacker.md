# Terminal / Hacker

Use for developer, infrastructure, security, or diagnostic tools where commands,
logs, and system state are real product content. Avoid costume-terminal styling.

## Direction contract

- Use monospace for commands, code, identifiers, logs, and compact data. Use a
  readable sans-serif for long explanations unless the product is truly terminal-only.
- Define dark canvas, raised panel, quiet border, primary text, muted text, one
  phosphor-like accent, and semantic status tokens.
- Build layouts around panes, command/search entry, results, status bar, and
  inspectable detail. Preserve a clear conventional navigation path.
- Align tabular data and timestamps. Support wrapping or horizontal inspection
  without clipping critical values.
- Distinguish prompt, user input, stdout, stderr, metadata, and selection with
  more than color alone.
- Make copy buttons, filters, pause/follow controls, and line references explicit.
  Operational output should remain selectable.
- Keep decorative scan lines, grids, and noise extremely faint or absent.

## Interaction

- Keyboard shortcuts must be discoverable and must not override browser or OS
  conventions without strong reason.
- Cursor blink is acceptable for a real input, not as ambient decoration.
- Streamed output must respect reduced motion, preserve scroll position, and
  offer pause/follow behavior when volume is high.
- Use a strong focus/selection treatment distinct from success green.

## Avoid

- “ACCESS GRANTED,” fake hex dumps, Matrix rain, glitch effects, and typing
  animations that delay real content.
- Green for every semantic state or monospace for long dense prose.
- Tiny text justified as terminal authenticity.
- Making a GUI workflow harder to use to resemble a command line.

## Done when

The visual language follows actual developer tasks, logs remain readable and
copyable, status is understandable without hue, all primary actions work by
keyboard and pointer, and decorative effects can be removed without losing the
direction.
