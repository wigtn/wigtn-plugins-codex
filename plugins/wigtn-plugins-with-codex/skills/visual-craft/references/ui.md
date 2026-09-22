# UI craft

Use for building or refining an interface. Existing tokens, components and brand
references are the starting point. A request to improve a screen does not require
new fonts, dependencies, motion libraries or a replacement design system.

## Composition

- Establish the primary task and reading order. Keep supporting detail close to
  what it explains; defer optional detail only when it remains easy to find.
- A landing page needs a convincing message and relevant proof. A dashboard needs
  comparison, state and efficient action. Do not impose marketing-page whitespace
  or a hero section on an operational tool.
- Review overloaded sections for competing headings, badges, statistics and CTAs.
  Group by purpose instead of reducing every font or moving essential detail into
  hidden tabs. Use a table for comparison, a list for scanning and a card when the
  content is a distinct object or action.
- Avoid repeating a giant left headline with a tiny detached paragraph on the
  right. Put the explanation in the same reading path or align a real second
  column. Symmetric and centered layouts remain valid when they fit the content.
- Decoration must not simulate evidence: a real component preview or supplied
  screenshot is useful; a made-up dashboard with success figures is not proof.

## Type, copy and effects

- Use real strings early, including Korean and long labels. Adjust content width,
  wrapping and hierarchy before shrinking type. Do not encode desktop composition
  with repeated hard breaks or non-breaking spaces.
- For Korean prose, judge phrase breaks with the actual font. Apply keep-all only
  where it improves reading, with a suitable fallback for long URLs or tokens.
  Do not apply a blanket wrapping rule to code, tables and every component.
- Prefer labels that name the action or content. Skip repeated eyebrow labels,
  decorative counters, dot-separated slogans and automatic arrows on every CTA.
  Keep arrows that explain navigation and dots that communicate real state.
- Use motion to explain change or satisfy the brief. Avoid attaching the same
  entrance effect to every section; retain reduced-motion behavior.

## Verify the implemented surface

- View the actual page at wide and narrow sizes appropriate to the product and
  at any intermediate width where the composition changes. Check reading order,
  awkward heading wraps, tiny final lines, clipping and accidental horizontal scroll.
- Exercise the interactions touched by the change, including keyboard focus and
  relevant loading, empty, error or expanded states. Keep contrast and semantics
  intact; a screenshot alone cannot verify these behaviors.
- Fix observable defects and confirm the affected views. If rendering is unavailable,
  identify the unverified visual aspects; do not equate a source scan with visual QA.
