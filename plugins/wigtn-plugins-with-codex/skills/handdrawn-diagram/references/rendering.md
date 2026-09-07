# Mermaid Hand-drawn Rendering

Use the renderer already selected by the repository. Check `command -v mmdc`
and `./node_modules/.bin/mmdc`, then record `mmdc --version`. Do not change a
project manifest or download a floating package version. If no renderer exists,
explain the missing dependency. Use existing authorization for an exact-version
installation; ask only when it is outside the authorized scope.

Start from this accessible source shape:

```mermaid
---
config:
  look: handDrawn
  theme: base
  flowchart:
    htmlLabels: false
  themeVariables:
    fontFamily: "Apple SD Gothic Neo, Malgun Gothic, Noto Sans KR, sans-serif"
    primaryColor: "#FFFFFF"
    primaryTextColor: "#172033"
    primaryBorderColor: "#475569"
    lineColor: "#475569"
    secondaryColor: "#F3E8FF"
    tertiaryColor: "#FFF7ED"
---
flowchart TD
  accTitle: 요청 처리 흐름
  accDescr: 요청을 검사하고 성공 또는 재시도로 분기하는 흐름
  A(["시작"]) --> B["처리"]
  B --> C{"성공?"}
  C -->|"예"| D["완료"]
  C -->|"아니오"| E["재시도"]
```

Quote every visible label. For a CJK flowchart, keep `htmlLabels: false`; Mermaid
11.16.0's handDrawn HTML-label path can under-measure Korean text. Keep decision
labels to one or two short words and move the full question into `accDescr` or
nearby prose. Use diamonds only for decisions and label every branch. Keep most
nodes neutral; reserve purple for the primary path, amber for attention, and red
for failure. Avoid emoji and decorative nodes.

Render both formats from the same source:

```bash
mmdc -i diagram.mmd -o diagram.svg -b white
mmdc -i diagram.mmd -o diagram.png -b white -s 2
python3 scripts/verify-artifacts.py diagram.mmd diagram.svg diagram.png
```

Run these commands from the skill directory or use an absolute path to the
verifier. If Chromium requires sandbox flags, use a temporary Puppeteer config;
do not add machine-specific flags to repository configuration.

For Korean labels, prefer earlier `<br/>` breaks and shorter wording over
smaller text. Put a long Latin identifier on its own line rather than editing
generated SVG. After deterministic verification, inspect the PNG at full
resolution for clipping, overlap, contrast, arrow direction, and group meaning.
