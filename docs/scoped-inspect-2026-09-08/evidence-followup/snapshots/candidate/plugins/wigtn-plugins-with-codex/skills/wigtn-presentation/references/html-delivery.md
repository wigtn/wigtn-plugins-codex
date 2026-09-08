# Self-contained HTML Delivery

Use this route only when the user explicitly requests an HTML presentation.

- Produce one portable HTML file with embedded CSS and JavaScript.
- Do not use remote fonts, CDN scripts, external stylesheets, or network images.
- Embed approved small assets as data URLs. If assets are too large, obtain
  agreement before changing the deliverable to an HTML bundle.
- Give every slide a `.slide` class and exactly one `.wigtn-dot` or
  `.wigtn-dot-char` signature marker.
- Use a 16:9 stage, `height: 100vh; height: 100dvh`, and `overflow: hidden`.
- Scale typography and spacing with `clamp()` and split overflowing content
  instead of shrinking it below readable size.
- Support Left/Right arrow and Space navigation. Add touch navigation only when
  it remains reliable on the target browser.
- Disable transitions under `prefers-reduced-motion: reduce`.

Run the deterministic checker, then inspect the deck in a browser at desktop
and mobile widths:

```bash
python3 scripts/verify-html-deck.py deck.html
```

The checker validates portability and structural brand markers. Browser review
still owns clipping, wrapping, contrast, interaction, and visual rhythm.
