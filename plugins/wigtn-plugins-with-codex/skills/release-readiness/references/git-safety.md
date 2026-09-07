# Git Safety

- Treat a dirty worktree as shared user state.
- Stage explicit paths after reviewing their diff; avoid broad staging when unrelated files exist.
- Never discard, overwrite, amend, rebase, force-push, or delete without explicit authority.
- Do not bypass hooks unless the user asks and understands the consequence.
- Before push, inspect branch and upstream. Before PR creation, inspect the base branch and summarize the actual diff. Ask only when a consequential target remains ambiguous after inspecting the request and repository.
- If identity, authentication, conflicts, or protections block the requested action, report the exact blocker without destructive recovery.
