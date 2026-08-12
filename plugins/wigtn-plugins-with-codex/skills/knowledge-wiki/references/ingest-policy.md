# Knowledge Wiki Ingest Policy

This policy governs automated Codex-session export to a WIGTN wiki.

## Safety invariants

1. Capture is off unless the Codex-specific config says `enabled: true`.
2. An empty `include` denies every repository; `exclude` always wins.
3. A repository marker may opt one repository into the global target, but it
   cannot override the global kill switch or `exclude`.
4. The wiki cannot live inside the repository being observed.
5. Automated writes are restricted to `per-user/`. `shared/` requires human
   review and a pull request.
6. A home- or root-wide include disables push even when `publish.push` is true.
7. Any undecidable gate, timeout, parsing error, or tool failure fails closed.

## Gates

| Gate | Input | Enforcement |
|---|---|---|
| G0 | cwd and config | deny-by-default scope and tenant resolution |
| G1 | transcript delta | deterministic credential and irreversible-ID scan |
| G2 | accepted delta | ephemeral Codex rewrite into generalized knowledge |
| G3 | generated article | separate Codex call that reports semantic violations |
| G4 | generated article | deterministic export-pattern scan |

G2 and G3 are not approval authorities. Only the full pipeline may publish.

## Denied material

- D1: credentials, tokens, private keys, or authenticated connection strings
- D2: personal data and irreversible personal identifiers
- D3: customer, organization, project-codename, or contract identity
- D4: private infrastructure, hosts, URLs, addresses, or connection details
- D5: copied proprietary source code
- D6: absolute paths that identify a person or machine
- D7: unpublished prices, schedules, personnel, or product information
- D8: third-party non-public material

The system discards rather than redacts a source turn when G1 matches. Generated
articles are discarded rather than partially repaired when G3 or G4 matches.

## Local data handling

Accepted transcript deltas are queued under the plugin's private `PLUGIN_DATA`
directory with owner-only permissions. Nested Codex calls are ephemeral. A job
is deleted after one processing attempt; only body-free event metadata remains.
Jobs are never committed to the wiki. Operators must not print queued job bodies
during diagnosis and should apply their normal local retention policy to plugin
data.
