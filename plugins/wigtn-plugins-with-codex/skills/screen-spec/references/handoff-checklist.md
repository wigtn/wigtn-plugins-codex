# Developer Handoff Checklist

Use this checklist only when `handoff` is selected. It reviews the selected
screen artifacts; it does not authorize implementation or Git actions.

## Accessibility

- Use appropriate landmarks and heading order.
- Give every input a visible label or accessible name.
- Give icon-only controls an accessible label.
- Define keyboard focus and interaction order.
- Meet WCAG AA contrast for meaningful text and controls.
- Describe loading, error, validation, and permission state semantics.

## Responsive behavior

- Define at least desktop and mobile behavior for applicable screens.
- Keep touch targets at least 44×44 CSS pixels.
- Avoid mobile horizontal scrolling and unreadably small body text.
- State how navigation, tables, forms, and dense content collapse.
- Use one responsive wireframe artifact rather than a disconnected mobile copy.

## States and microcopy

- Cover only applicable loading, empty, error, success, unauthorized, offline,
  validation, and destructive-confirmation states.
- Give each failure or empty state a useful next action.
- Use action labels such as “저장하기” rather than ambiguous “확인”.
- Do not expose raw server errors or fabricate operational promises.

Read [microcopy patterns](microcopy-patterns.md) only when material forms or
user-facing recovery states need detailed copy.

## Component contract

- Identify input type, required state, validation, and option source.
- Identify reusable components and repository-native equivalents when known.
- Describe consequential state transitions, disabled/loading behavior, and
  destructive effects.
- Keep visual direction separate unless `design-direction` was explicitly used.

## Coverage

- Every in-scope FR maps to at least one screen.
- Every screen maps back to an in-scope requirement or recorded assumption.
- Acceptance scenarios map to a user flow when flow is selected.
- Screen-spec wireframe anchors resolve to real IDs.
- Page IDs, routes, roles, states, and requirement IDs agree across the
  selected artifact closure.

## Completion report

Report only material gaps using this shape:

| Severity | Artifact / screen | Gap | Required correction |
|---|---|---|---|

Run the selector-aware screen validator and report its result separately from
visual inspection. A passing handoff does not verify implementation. Continue
into implementation only when the user separately requests it; use
`verified-delivery` only through its qualified explicit invocation.
