# Minimal Corporate

Use for B2B, administration, finance, operations, and workflow products where
trust, density, and predictable states outrank visual experimentation.

## Direction contract

- Reuse the product’s neutral palette. Define semantic roles for canvas,
  surface, border, text, muted text, primary, success, warning, and danger.
- Use one practical sans-serif. Default to 14–16px body text, tabular numerals
  for metrics, and a restrained 4–5 step type hierarchy.
- Organize pages as title/context, primary action, filters, content, then
  secondary help. Keep the primary action stable across related screens.
- Use an 8px spacing system with compact and comfortable density modes only if
  users genuinely need both.
- Tables need persistent headers when useful, clear column alignment, sorting
  state, empty/loading/error states, and a narrow-screen alternative.
- Cards should represent separate objects or summaries. Prefer sections and
  dividers when content belongs to one workflow.
- Forms use visible labels, inline help before failure, errors beside the field,
  and a clear submit result. Never rely on placeholder text as the label.
- Reserve color for action, status, and exceptions. Pair every status color with
  text or an icon.

## Interaction

- Keep transitions under 180ms and avoid moving controls after user input.
- Confirm destructive actions in proportion to reversibility. Explain the exact
  object affected.
- Make focus, hover, selected, disabled, busy, success, and error states explicit.
- Support keyboard use for navigation, dialogs, menus, and data controls.

## Avoid

- Dashboard decoration without an operational question.
- Low-contrast borders, excessive rounded cards, generic blue gradients, and
  hiding advanced actions behind unexplained icon-only buttons.
- Dense desktop tables squeezed into mobile width.

## Done when

A new user can identify current context, primary action, and system state; an
expert can scan dense data quickly; every mutation has feedback; and the screen
remains understandable without color.
