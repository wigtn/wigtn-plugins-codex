# v0.5.7: Visual Craft and read-only artifact checks

UI and document creation can now use `visual-craft` to review hierarchy, density,
natural copy, wrapping and decorative clutter. The Core catalog grows from nine
to ten skills. Existing skills and their invocation policies remain available.

## Artifact-specific guidance

The skill supports frontend interfaces and authored documents, reports and slides.
It loads UI or document references according to the requested artifact, respects
existing brands and format-specific workflows, and preserves source quotations,
data and requirements. It excludes ordinary chat, backend work and typo-only edits.
Invoke it explicitly with `$wigtn-plugins-with-codex:visual-craft`, or let Codex
select it for a matching creation or substantial refinement request.

## Automatic checks

- The Python standard-library checker reads explicit HTML/Markdown files and
  reports duplicate IDs, language declarations, fragment targets, source-level
  labels, heading structure and contextual copy patterns. It does not execute
  embedded scripts, fetch links or edit files.
- A read-only browser expression measures viewport overflow, clipped text, small
  text and small targets within the current viewport. It uses an already-authorized
  browser; no browser launcher, hook or third-party package is installed.
- Confirmed source defects and contextual review findings are separate. Intentional
  truncation, dynamic hash routes, quotations and brand marks must not be rewritten
  simply to clear a warning. Findings are not aesthetic scores.

## Validation and limitations

- The release runs `bash scripts/validate.sh`, including 17 detector regression
  tests and ten synthetic DOM geometry assertions inside the Node fixture test.
  CI explicitly provisions Node so the geometry fixture can run.
- Source checks of three local HTML samples found no findings. Real-browser
  integration and visual quality comparison remain unverified. Geometry fixtures
  do not replace browser testing, keyboard checks or a full accessibility audit.
- Automatic selection metadata and lexical fixtures do not establish model routing
  accuracy. No GPT-6 quality, speed or token-saving improvement is claimed.
- Historical full8/full9 ablation catalogs retain their original skill membership;
  they do not represent the new ten-skill package.
- Knowledge Wiki receives only the matching version under the shared-version policy.

If you installed the temporary personal `visual-craft` copy, compare it with the
packaged skill and archive it after the plugin update, preserving any local edits.
Start a new Codex task to pick up the updated plugin.

[Design rationale and research sources](VISUAL-CRAFT.md)
