# Delivery blind errata

The first runner attempt made zero model calls because the packet directory was
not a Git repository and the CLI trust preflight rejected every invocation.
`--skip-git-repo-check` was added for the read-only anonymous packet. Failed
zero-duration attempts are excluded from judge results.

The first completed screen anonymized labels but left `BLIND-MAP.json` in the
judge-visible run tree. There is no evidence that either judge opened it, but
filesystem-level blinding was not guaranteed. That screen is exploratory.
`blind-v2` does not materialize the mapping, runs from an empty judge working
directory, and resolves the deterministic label order only inside the scorer.
