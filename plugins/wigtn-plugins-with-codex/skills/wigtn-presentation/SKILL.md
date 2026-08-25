---
name: wigtn-presentation
description: Create WIGTN-branded presentations, pitch decks, company introductions, or internal slides using WIGTN’s ink navy, signature purple dot, and logo rules. Use only when WIGTN branding is explicit. Do not use for general presentations, another brand, or a generic PPT request.
---

# WIGTN Presentation

Apply WIGTN identity as a brand overlay on the host presentation workflow. Do
not replace its narrative, source, rendering, overflow, or output-format rules.

## Workflow

1. Establish audience, purpose, duration, language, and output route from context.
   - For PowerPoint, local deck, or an unspecified format, use the available
     presentation workflow and deliver PPTX.
   - For Google Slides, follow the host's native Slides routing.
   - Create HTML only when the user explicitly requests HTML; then read the
     [HTML delivery contract](references/html-delivery.md).
2. Read [brand](references/brand.md) and [design guide](references/design-guide.md).
3. Build one audience-facing message per slide. Apply one base theme and the
   documented `section-inverse` exception only when it strengthens section rhythm.
4. Use an approved user-provided logo when available. Otherwise use the
   canonical text wordmark with a purple period; do not search assumed local paths.
5. Render or preview every slide using the selected output workflow. Check
   clipping, overflow, font substitution, contrast, source notes, and visual rhythm.
6. For HTML, run `python3 scripts/verify-html-deck.py <deck.html>` from this
   skill directory before browser inspection.
7. Return only the final artifact and a concise verification summary.

Do not apply WIGTN identity to a generic or third-party presentation without explicit user intent.
