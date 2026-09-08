# WIGTN presentation brand contract

Apply this overlay only to an explicit WIGTN presentation. The host
presentation workflow owns narrative, citations, generation, rendering, and
format-specific limits.

## Identity

- Wordmark: lowercase `wigtn.` in a heavy geometric sans-serif; only the period
  is purple.
- Tone: minimal, confident, technical; ink navy with one restrained purple cue.
- Use Light or Dark as the deck-wide base. A named `section-inverse` may invert
  a real section divider, then return to the base theme.

| Token | HEX | Role |
|---|---|---|
| Ink | `#1E1E28` | light-theme text, dark surfaces |
| Ink Deep | `#15151E` | dark-theme background |
| Purple | `#9B51E0` | light-theme signature and accent |
| Purple Bright | `#A85FEA` | dark-theme signature and accent |
| Purple Deep | `#6B2EAA` | restrained single-hue depth |
| White | `#FFFFFF` | light canvas, dark-theme text |
| Off White | `#FAFAFA` | light secondary surface |

## Signature and assets

Choose one repeatable signature location: page number, section number,
title-ending period, or fixed corner. Use exactly one signature treatment per
slide. Do not add another dot beside a logo that already includes it.

Use an approved user-provided or repository logo and preserve its ratio and
clear space. Do not search assumed paths or synthesize an image logo. Without
an approved asset, use editable text runs: `wigtn` in Ink/White and the period
in Purple/Purple Bright.

## Composition

- Give each slide one audience-facing message and no more than three visible
  hierarchy levels.
- Prefer asymmetric alignment, deliberate whitespace, and one strong
  composition over repeated cards, badges, or dashboard panels.
- Vary adjacent silhouettes. Use a cover, numbered agenda, section divider,
  comparison, image/text, timeline, quote, KPI, or concise closing only when
  the content supports that role.
- Keep the purple signature subordinate to the message.
- Use native shapes or the host diagram route for PPTX/Slides. Use CSS or
  inline SVG only for an explicitly requested HTML deck. Invoke
  `handdrawn-diagram` only for an explicit sketch aesthetic.

## Type and motion

Prefer fonts already available in the output environment. Use a present Korean
sans-serif for Korean and one geometric display face when available. Do not
download fonts or add a CDN without explicit authorization. Split content
before shrinking below the host workflow's readable minimum.

Use restrained 0.2–0.4 second fades or short vertical movement, at most one or
two entrance patterns per slide. Respect reduced motion and avoid parallax,
perpetual motion, or heavy glow.

## Final review

Inspect every rendered slide at full size for overflow, clipping, overlap,
title wrapping, contrast, signature placement, logo distortion, source notes,
and font substitution. Use a contact sheet for deck rhythm only.

Avoid generic indigo, rainbow gradients, mixed Light/Dark body slides outside
`section-inverse`, centered text everywhere, repeated card grids, distorted
logos, glow, and decorative dot clouds.
