# WIGTN Presentation Brand

Use this identity only for an explicit WIGTN presentation. Preserve the exact
tokens; do not approximate them with generic AI purple.

## Identity

- Wordmark: lowercase `wigtn.` in a heavy geometric sans-serif.
- Signature: only the period is purple.
- Tone: minimal, confident, technical; ink navy with one restrained purple cue.

| Token | HEX | Use |
|---|---|---|
| Ink | `#1E1E28` | Light-theme text, dark surfaces |
| Ink Deep | `#15151E` | Dark-theme background |
| Purple | `#9B51E0` | Light-theme signature and accent |
| Purple Bright | `#A85FEA` | Dark-theme signature and accent |
| Purple Deep | `#6B2EAA` | restrained depth or single-hue gradient end |
| White | `#FFFFFF` | Light background, dark-theme text |
| Off White | `#FAFAFA` | Light secondary surface |

Use either Light or Dark as the base theme for the complete deck. One named
`section-inverse` treatment may invert a section-divider slide, then the deck
must return to its base theme. This is the only theme-mixing exception.

## Signature dot

Choose one repeatable placement for the deck: page number, section number,
title-ending dot, or fixed corner marker. Use exactly one signature treatment
per slide. Do not scatter purple decoration or add a second dot beside a logo
that already contains the purple period.

## Wordmark and assets

Use an approved logo supplied by the user or present in the target repository.
Preserve its ratio and clear space. Do not assume untracked `assets/logo/` or
`docs/images/` files exist and do not synthesize an unofficial image logo.

When no approved logo is available, the canonical fallback is live text:

```text
wigtn + purple period
```

Style `wigtn` in Ink/White and the period in Purple/Purple Bright. For HTML,
use separate spans. For PPTX or Slides, use adjacent text runs so the mark stays
editable and portable.

## Typography

Prefer a font already available in the output environment. Use Pretendard or
Noto Sans KR for Korean when present, and a geometric sans such as Space
Grotesk or Sora for display text when present. Otherwise use a platform Korean
sans-serif fallback consistently. Do not download fonts or add a CDN dependency
without explicit authorization. Verify substitution in the final render.

Keep no more than three visible hierarchy levels per slide. Shorten content or
split the slide before reducing body text below the host presentation workflow's
minimum size.

## Avoid

- purple/pink or rainbow gradients
- generic indigo such as `#6366F1`
- mixed Light/Dark body slides outside `section-inverse`
- centered text on every slide
- repeated dashboard-card layouts
- distorted logos, excessive glow, or decorative dot clouds
