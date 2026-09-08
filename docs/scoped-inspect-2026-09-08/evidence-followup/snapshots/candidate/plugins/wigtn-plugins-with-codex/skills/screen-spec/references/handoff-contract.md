# Developer handoff contract

Use only when `handoff` is selected.

- Map every in-scope requirement to a screen or flow, an implementation seam,
  and an observable check. Report unmapped requirements and orphan screens.
- Prefer inspected repository routes, components, state patterns, validation,
  and data boundaries. Use `TBD` instead of naming a framework or library not
  found in the project.
- Describe focus order, keyboard behavior, labels, semantics, contrast, and
  narrow-layout priority where applicable.
- Carry loading, empty, error, success, authorization, offline, validation, and
  destructive states only when the selected behavior can reach them.
- Order implementation by real dependencies and independently verifiable
  outcomes, not generic foundation/polish phases.
- Keep visual direction separate unless `design-direction` was explicitly used.
- Report exact open decisions with their implementation impact and owner or
  decision point.

Run the selector-aware validator separately. A passing handoff validates the
artifact contract, not the implementation, and grants no implementation or Git
authority.
