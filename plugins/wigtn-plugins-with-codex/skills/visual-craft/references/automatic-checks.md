# Automatic craft checks

Run after creating or substantially editing the requested artifact, before delivery.
Inspect findings, fix confirmed defects, and rerun affected checks. Do not run a
repository-wide scan, install hooks, or generate additional deliverables by default.

## Source checks

For HTML or Markdown, run with explicit file paths:

```sh
python3 <skill-directory>/scripts/audit-source.py <artifact.html> [<document.md>]
```

Resolve `<skill-directory>` to this skill's installed location. The
[source checker](../scripts/audit-source.py) uses only Python's standard library,
reads files without modifying them, and prints JSON with rule, severity and line.
It does not follow external links or execute embedded scripts.

- `error`: duplicate IDs and missing document language.
- `review`: unresolved same-document fragments, missing source-level labels/alt,
  skipped heading levels, hard-broken
  headings, repeated em dashes/separators and forced Markdown line breaks.
- Exit 0: no definite source errors (review findings may remain); 1: source errors;
  2: input or unsupported-format errors. Check the JSON, not just the exit code.
- Quotations, code, SVG, math and explicitly hidden HTML are excluded from copy
  heuristics. Markdown fences, quote lines, frontmatter and common code forms are
  excluded. This lightweight parser does not implement all Markdown dialects.

Fragment targets may be created at runtime or used by a hash router; verify them
in the running UI before treating them as broken links.
Do not rewrite preserved quotations or brand marks just to clear a finding.
Keep intentional cases with a short reason; there is no required zero-warning score.
JSX/TSX, PDF, DOCX and PPTX are deliberately unsupported by the source checker.
Use the relevant renderer/browser or existing format-specific validators instead.

## Rendered UI checks

After opening the authorized preview using the available browser workflow, read
[audit-rendered.js](../scripts/audit-rendered.js) and pass its function expression
to the supported read-only page evaluation API. For Browser's documented runtime:

```js
const checkSource = await fs.readFile('/absolute/skill-directory/scripts/audit-rendered.js', 'utf8');
const result = await tab.playwright.evaluate(checkSource);
nodeRepl.write(result);
```

Use the environment's approved file reader and browser API; `fs` above is the Node
file module, not a page global. The function only reads DOM geometry and computed
styles. It does not navigate, mutate DOM, fetch resources or launch a browser.
Never use it to bypass a blocked URL or unavailable browser permission.

Check wide and narrow layouts and relevant opened panels through the normal browser
workflow. The detector examines the current viewport, so scroll to other meaningful
sections before checking them. Nested scrollable tables are allowed; full-page
horizontal overflow is reported. Clipped text, small text and small targets are
review findings because truncation, metadata and inline links may be intentional.

Read the measured findings alongside the screenshot and actual task. Keyboard
behavior, contrast, long Korean heading wraps, meaningful information density and
summary/list consistency still require appropriate checks. If browser inspection
is blocked, return source findings and explicitly mark rendered checks unavailable.
No findings means only that these detectors found nothing, not visual QA passed.
