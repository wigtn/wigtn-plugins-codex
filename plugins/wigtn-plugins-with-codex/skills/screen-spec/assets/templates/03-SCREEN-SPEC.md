# Screen Specifications — {feature-name}

## Assumptions and open decisions

- {fact, inference, or unresolved decision}

Duplicate the following section only for an in-scope screen.

## Screen: {screen-id} — {screen-name}

| Field | Contract |
|---|---|
| Route / entry | {confirmed route, entry condition, or TBD + owner} |
| Audience / authorization | {roles and server-enforced boundary if known} |
| Requirements | {FR/AC IDs} |
| Purpose | {one observable user outcome} |

### States

| State | Trigger | Visible behavior | Recovery / next action | Requirements |
|---|---|---|---|---|
| {applicable state} | {condition} | {what the user observes} | {action} | {IDs} |

### Components and data

| Element | Role | Input / source | Validation or boundary | States |
|---|---|---|---|---|
| {component or region} | {purpose} | {known source or TBD} | {rule or open decision} | {state names} |

### Interactions

| User action | Preconditions | Result | Failure behavior | Requirements |
|---|---|---|---|---|
| {action} | {condition} | {observable result} | {recovery} | {IDs} |

### Responsive behavior

| Context | Behavior |
|---|---|
| Wide | {project-native layout behavior} |
| Narrow | {priority, order, collapse, or overflow behavior} |

### Copy and accessibility

- Primary action label: {project-native action text}
- Error or empty recovery: {message plus next action}
- Focus / keyboard / semantics: {applicable contract}

### Wireframe anchor

`04-WIREFRAME.html#screen-{slug-1}`

Do not invent exact breakpoints, components, APIs, storage, or policies. Record
unknowns as `TBD` with an owner or decision point.
