# Developer Handoff — {feature-name}

## Source and scope

- Source requirements: {paths or IDs}
- Included artifacts: {selected artifact files}
- Assumptions and unresolved decisions: {summary}

## Requirement coverage

| Requirement | Screens / flows | Components or seams | Observable check | Gap |
|---|---|---|---|---|
| {FR/AC ID} | {IDs} | {confirmed existing or intended boundary} | {command or behavior} | {none/TBD} |

## Screen implementation contracts

| Screen | Existing route / intended path | Reusable project components | New boundary | States |
|---|---|---|---|---|
| {screen ID} | {confirmed path or TBD} | {inspected components or none found} | {smallest new seam} | {applicable states} |

## Interaction and data boundaries

| Interaction | Input / source | Authorization / validation | Success | Failure / recovery |
|---|---|---|---|---|
| {action} | {known contract or TBD} | {known rule or open decision} | {observable result} | {recovery} |

## Responsive and accessibility

- Reading and focus order: {contract}
- Narrow-layout priority and collapse behavior: {contract}
- Labels, semantics, keyboard, and contrast: {contract}

## Suggested implementation order

1. {dependency or contract that must exist first}
2. {independently verifiable primary behavior}
3. {remaining behavior or integration}

Order by real dependencies and verification endpoints. Do not add project
bootstrap, framework, library, migration, or polish phases without repository
evidence.

## Verification

| Requirement | Existing check or proposed observable check | Status |
|---|---|---|
| {ID} | {exact repository-native command, manual observation, or TBD} | {known/TBD} |

## Open decisions

| Decision | Why implementation depends on it | Owner / decision point |
|---|---|---|
| {decision} | {impact} | {owner or milestone} |

This handoff does not authorize implementation or Git actions and does not
claim that the described behavior already exists.
