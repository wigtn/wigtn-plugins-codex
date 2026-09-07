#!/usr/bin/env python3
"""Validate selected WIGTN screen artifacts and their dependency closure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


ARTIFACTS = {
    "ia": "01-IA.md",
    "flow": "02-USER-FLOW.md",
    "screen": "03-SCREEN-SPEC.md",
    "wireframe": "04-WIREFRAME.html",
    "handoff": "05-DEV-HANDOFF.md",
}
DEPENDENCIES = {
    "ia": set(),
    "flow": set(),
    "screen": {"ia"},
    "wireframe": {"ia", "screen"},
    "handoff": {"ia", "flow", "screen", "wireframe"},
}
# Template tokens start immediately after ``{`` and do not contain CSS-style
# declarations. This catches new project-native placeholders without mistaking
# ordinary formatted CSS blocks (``{ color: ...; }``) for unresolved tokens.
KNOWN_PLACEHOLDER = re.compile(r"\{(?=[A-Za-z0-9가-힣])[^{}\n;:]+\}")
REQ_ID = re.compile(r"\b(?:FR|REQ|AC)-[A-Za-z0-9][A-Za-z0-9._-]*\b")
ANCHOR_REF = re.compile(r"04-WIREFRAME\.html#([A-Za-z][A-Za-z0-9._:-]*)")
HTML_ID = re.compile(r'\bid=["\']([A-Za-z][A-Za-z0-9._:-]*)["\']')
HTML_FRAGMENT = re.compile(r'\bhref=["\']#([A-Za-z][A-Za-z0-9._:-]*)["\']')
REMOTE_RESOURCE = re.compile(
    r'<(?:script|link|img|source|video|audio|iframe|embed|object)\b[^>]*'
    r'(?:src|href|poster|data|srcset)\s*=\s*["\']?[^"\'>]*'
    r'(?:(?:https?:)?//)'
    r'|(?:@import\s+(?:url\(\s*)?|url\(\s*)["\']?\s*(?:(?:https?:)?//)',
    re.I,
)
SCREEN_HEADING = re.compile(r"^## (?:Screen|화면):\s*(.+?)\s*$", re.M)


def has_ia_page_map(text: str) -> bool:
    """Accept an English or Korean structured page map without loose prose hits."""
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip().casefold() for cell in line.strip().strip("|").split("|")]
        if any(cell == "page" or "페이지" in cell for cell in cells):
            return True
        has_information_unit = any(
            "정보 단위" in cell or cell == "화면" for cell in cells
        )
        has_route = any(
            cell in {"route", "path", "url"} or "경로" in cell for cell in cells
        )
        if has_information_unit and has_route:
            return True
    return False


def require(text: str, needle: str, path: str, errors: list[str]) -> None:
    if needle not in text:
        errors.append(f"{path}: missing {needle!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument(
        "--artifacts",
        nargs="+",
        default=["all"],
        help="Comma- or space-separated ia,flow,screen,wireframe,handoff or all",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    requested_tokens = {
        item.strip()
        for value in args.artifacts
        for item in value.split(",")
        if item.strip()
    }
    requested = set(ARTIFACTS) if requested_tokens == {"all"} else requested_tokens
    unknown = requested - set(ARTIFACTS)
    if not requested:
        errors.append("--artifacts must select at least one artifact")
    if unknown:
        errors.append("unknown artifacts: " + ", ".join(sorted(unknown)))
    selected = set(requested - unknown)
    pending = list(selected)
    while pending:
        name = pending.pop()
        for dependency in DEPENDENCIES[name] - selected:
            selected.add(dependency)
            pending.append(dependency)
    texts: dict[str, str] = {}
    for artifact in sorted(selected):
        name = ARTIFACTS[artifact]
        path = args.directory / name
        if not path.is_file():
            errors.append(f"{name}: missing artifact")
            continue
        texts[name] = path.read_text(encoding="utf-8", errors="replace")

    for name, text in texts.items():
        placeholders = sorted(set(KNOWN_PLACEHOLDER.findall(text)))
        if placeholders:
            errors.append(
                f"{name}: unresolved template placeholders: "
                + ", ".join(placeholders[:5])
            )

    ia = texts.get("01-IA.md", "")
    flow = texts.get("02-USER-FLOW.md", "")
    screen = texts.get("03-SCREEN-SPEC.md", "")
    wireframe = texts.get("04-WIREFRAME.html", "")
    handoff = texts.get("05-DEV-HANDOFF.md", "")
    if ia:
        if not has_ia_page_map(ia):
            errors.append(
                "01-IA.md: missing structured page map "
                "(Page/페이지 or 정보 단위 + Route/경로 columns)"
            )
    if flow:
        require(flow, "```mermaid", "02-USER-FLOW.md", errors)
        require(flow, "Flow Coverage", "02-USER-FLOW.md", errors)
    if handoff:
        if not REQ_ID.search(handoff):
            errors.append("05-DEV-HANDOFF.md: missing requirement ID")
        require(handoff, "Suggested Implementation Order", "05-DEV-HANDOFF.md", errors)

    anchors: list[str] = []
    if screen:
        screens = SCREEN_HEADING.findall(screen)
        if not screens:
            errors.append("03-SCREEN-SPEC.md: no screen headings")
        elif len(screens) != len(set(screens)):
            errors.append("03-SCREEN-SPEC.md: duplicate screen heading")
        anchors = ANCHOR_REF.findall(screen)
        if len(anchors) != len(set(anchors)):
            errors.append("03-SCREEN-SPEC.md: duplicate wireframe anchor")
    if wireframe:
        if REMOTE_RESOURCE.search(wireframe):
            errors.append(
                "04-WIREFRAME.html: external network resource breaks portability"
            )
        if 'name="viewport"' not in wireframe and "name='viewport'" not in wireframe:
            errors.append("04-WIREFRAME.html: missing viewport meta")
        html_ids = set(HTML_ID.findall(wireframe))
        for fragment in sorted(set(HTML_FRAGMENT.findall(wireframe)) - html_ids):
            errors.append(f"04-WIREFRAME.html: broken internal link #{fragment}")
        for anchor in sorted(set(anchors) - html_ids):
            errors.append(f"04-WIREFRAME.html: missing referenced anchor #{anchor}")
        screen_ids = {value for value in html_ids if value.startswith("screen-")}
        if not screen_ids:
            errors.append("04-WIREFRAME.html: no screen-* id")

    ia_ids = set(REQ_ID.findall(ia))
    screen_req_ids = set(REQ_ID.findall(screen))
    handoff_ids = set(REQ_ID.findall(handoff))
    for requirement in sorted(screen_req_ids - ia_ids) if ia and screen else []:
        errors.append(
            f"03-SCREEN-SPEC.md: {requirement} is absent from 01-IA.md"
        )
    for requirement in sorted(screen_req_ids - handoff_ids) if handoff and screen else []:
        errors.append(
            f"05-DEV-HANDOFF.md: missing screen requirement {requirement}"
        )

    result = {"valid": not errors, "errors": errors}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif errors:
        print("Screen contract: FAIL")
        for error in errors:
            print(f"- {error}")
    else:
        print("Screen contract: PASS")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
