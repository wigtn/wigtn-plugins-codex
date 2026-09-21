# v0.5.6 — Preserve requirement text and respect standalone document scope

This patch fixes requirement-text corruption during import and unnecessary
bundle validation for standalone screen specifications and developer handoffs.

## Requirement imports

The importer previously removed underscores, asterisks and backticks and
collapsed whitespace in requirement bodies. For example, `unit_price * quantity`
could become `unitprice quantity`, changing the meaning of the requirement.
The same normalization could treat different requirement bodies as identical
when deciding whether to retain earlier verification evidence.

Requirement bodies now preserve these characters and internal whitespace.
Regression checks cover list/table inputs, identifiers, operators, negative
values, literal spaces, unchanged evidence reuse and invalidation after a
meaningful text change. Existing format and resume checks remain in place.

Re-import affected source documents and rerun verification to repair previously
saved records. This update does not rewrite saved WorkGraphs automatically.
Preserving text can change generated IDs in formats without explicit IDs and
can conservatively invalidate evidence after formatting-only changes.

## Standalone screen specifications and handoffs

The screen-spec skill now follows the requested artifact, path and format.
Existing documents are inputs, and templates are optional references.
For standalone chat or custom Markdown output, the skill reviews the relevant
requirements directly instead of running the numbered WIGTN bundle validator.
That validator remains available when the numbered artifact set and its
companion files are in scope; its existing structural checks are unchanged.

## Compatibility and validation

- All nine Core skills remain available, including explicit-only
  `verified-delivery`. Experimental skill removal is not part of this release.
- Knowledge Wiki receives only the matching manifest version under the
  repository's shared-version policy.
- `bash scripts/validate.sh` passed repository, plugin, skill and deterministic
  regression validation. A negative control reproduced the old importer defect,
  and a WorkGraph CLI smoke check preserved literal requirement text. The
  release log is stored as `release-v0.5.6-validation.log`.
- These are correctness and scope fixes. The patched release has not undergone
  a new model benchmark, and no GPT-6 speed, token or coding-quality improvement
  is claimed.
