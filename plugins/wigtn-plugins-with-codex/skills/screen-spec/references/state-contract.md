# Screen state contract

Cover only states that can occur in the named screen or flow.

| State | Specify when applicable |
|---|---|
| loading / pending | trigger, stable layout, blocked actions, completion signal |
| empty | why no result exists and the next useful action |
| error | observable failure, retained input, recovery, escalation if sourced |
| success | visible result and next state; avoid redundant feedback |
| unauthorized | protected boundary and non-leaking user guidance |
| validation | field or object rule, placement, correction path |
| offline / interrupted | affected actions, retained work, retry behavior |
| destructive confirmation | exact object, consequence, reversibility, final action |

For each applicable state record the trigger, visible behavior, recovery or
next action, and linked requirement. Mark non-applicable states `N/A` only when
the reason is evident. Do not invent time thresholds, retry counts, redirect
routes, server controls, or visual components. Authorization is server behavior;
a hidden menu alone is not evidence of enforcement.
