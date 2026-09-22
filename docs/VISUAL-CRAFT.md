# Visual Craft: scope and validation

Release: v0.5.7. No model-quality or token-saving claim.

## Design choice

One implicitly discoverable skill supports frontend UI and authored documents.
The entrypoint carries common decisions; UI and document guidance load by artifact.
No third-party runtime dependency, hook, renderer, style menu or mandatory planning file is added.
Read-only checks use Python and the already-authorized browser workflow.
Existing format and product skills retain responsibility for their own outputs.
The new skill does not force WIGTN branding on unrelated documents.

The default excludes typo-only edits, ordinary chat and backend work. Direction-only
requests still belong to design-direction; PRD and screen content contracts belong
to their existing skills. A relevant craft pass can accompany those artifacts without
starting a second workflow. Skill selection remains a model decision, not a keyword hook.

## Research provenance

Reviewed upstream main on 2026-09-22. These are independently written instructions
informed by the following design approaches, not vendored upstream skill files.
Upstream links may change after this review.

- [Anthropic frontend-design](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md):
  brief-specific design, content-led hierarchy, meaningful structural markers and plain copy.
- [Taste-skill](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/SKILL.md):
  concrete examples of decorative dots, broken headings and detached explanatory text.
  Do not import its global font bans, motion defaults, punctuation replacement in quotes,
  or forced asymmetric layouts.
- [Impeccable](https://github.com/pbakaus/impeccable):
  focused simplification, typography, layout and copy review with bounded visual checks.
  Do not import its binary launcher, installer, hooks or whole command suite.

Korean writing, source fidelity, publication formats and cooperation with existing
WIGTN contracts are local additions. An em dash in a quotation, a status dot and the
WIGTN logo period are intentionally different from decorative new copy.

## Validation and practical limits

Run `bash scripts/validate.sh` for packaging, resource links, explicit/implicit policy
and repository regressions. The trigger fixtures are lexical examples only: changing
their mapping does not establish actual Codex routing. No automatic visual-quality
score is introduced. Historical full8/full9 experiment catalogs retain their old
skill membership; neither represents the ten-skill package introduced in v0.5.7.

Before claiming a quality improvement, compare generated artifacts with and without
the skill using the same brief, assets, model and settings. Inspect rendered outputs,
preserved content and task completion; include latency and input usage rather than
rewarding deletion alone. Useful behavioral cases include:

| Request | Observable outcome to inspect |
|---|---|
| Korean product landing page | Natural heading wraps at narrow/wide widths; functional CTA; no invented proof |
| Dense operations dashboard | Required columns and actions remain usable; no marketing hero added |
| Technical report from supplied measurements | Exact data, sources and limitations survive; no fabricated improvement |
| Word report with a long table | Valid requested file; readable repeated headers and page breaks |
| Generic slides | Requested deck format, no accidental WIGTN brand |
| WIGTN deck | Approved brand and logo dot preserved; readable slides |
| Existing legal text and quotations | Source text unchanged despite punctuation preferences |
| Small CSS or typo fix | Only requested change, no redesign or new documents |

These cases define a follow-up behavioral evaluation, not completed model runs.

## Checks executed on 2026-09-22

- Full `bash scripts/validate.sh`: PASS, including ten core skill manifests,
  all resource links, 65 lexical routing examples and existing repository contracts.
- `git diff --check`: PASS.
- Personal installation of this skill only: validated with `quick_validate.py`.
- Real Codex app-server `skills/list` with forceReload: one enabled user-scope
  `visual-craft` entry, no related discovery errors. No model generation was run.
- The entrypoint is 55 lines; the UI and document references are selected by task.
  File length is an implementation fact, not a measured token saving.

Before v0.5.7, local testing used a personal copy with the unqualified
`$visual-craft` default prompt. After installing v0.5.7, archive that copy only after
checking for local edits and confirming the packaged skill is enabled, so duplicate
discovery does not remain. The plugin uses `$wigtn-plugins-with-codex:visual-craft`.

## Automatic detectors added on 2026-09-23

The skill now routes artifact completion through `references/automatic-checks.md`.
`scripts/audit-source.py` checks explicit HTML/Markdown files and emits bounded JSON
findings with rule, severity and source line. `scripts/audit-rendered.js` is a
read-only expression for an existing authorized browser evaluation API. It reports
viewport overflow and contextual clipping, small text and small target findings.
Neither script installs a hook, fetches resources or modifies the artifact.

Source checks deliberately do not claim browser visibility, full Markdown parsing,
JSX support or document-format validation. Rendered checks cover only the current
viewport, excluding iframe contents and shadow roots. Contrast, keyboard behavior,
copy correctness and aesthetic quality are not certified. Browser permission blocks
remain blocks; the detector is not an alternate browser launcher.

Validation: 17 regression tests passed, including a Node VM fixture with ten DOM
geometry assertions. Tests cover positive findings, protected quotations/code,
native labels, inert templates, decoded fragment targets, bounded reporting,
unsupported inputs and read-only operation. Geometry fixtures do not constitute a
real-browser integration test. The three existing smoke-test HTML files returned
no source findings; this is not a rendered or interaction pass.
