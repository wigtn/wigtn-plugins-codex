#!/usr/bin/env python3
"""Validate a WIGTN five-artifact screen specification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


FILES = (
    "01-IA.md",
    "02-USER-FLOW.md",
    "03-SCREEN-SPEC.md",
    "04-WIREFRAME.html",
    "05-DEV-HANDOFF.md",
)
KNOWN_PLACEHOLDER = re.compile(
    r"\{(?:feature-name|YYYY-MM-DD|route-[^}]+|slug-[^}]+|role-[^}]+|"
    r"audience|auth|요약|분기|처리|대상 화면|endpoint|sub-task-list)[^}]*\}"
)
REQ_ID = re.compile(r"\b(?:FR|REQ|AC)-[A-Za-z0-9][A-Za-z0-9._-]*\b")
ANCHOR_REF = re.compile(r"04-WIREFRAME\.html#([A-Za-z][A-Za-z0-9._:-]*)")
HTML_ID = re.compile(r'\bid=["\']([A-Za-z][A-Za-z0-9._:-]*)["\']')
SCREEN_HEADING = re.compile(r"^## Screen:\s*(.+?)\s*$", re.M)


def require(text: str, needle: str, path: str, errors: list[str]) -> None:
    if needle not in text:
        errors.append(f"{path}: missing {needle!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    texts: dict[str, str] = {}
    for name in FILES:
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
    require(ia, "Page", "01-IA.md", errors)
    require(flow, "```mermaid", "02-USER-FLOW.md", errors)
    require(flow, "Flow Coverage", "02-USER-FLOW.md", errors)
    require(handoff, "FR", "05-DEV-HANDOFF.md", errors)
    require(handoff, "Suggested Implementation Order", "05-DEV-HANDOFF.md", errors)

    screens = SCREEN_HEADING.findall(screen)
    if not screens:
        errors.append("03-SCREEN-SPEC.md: no screen headings")
    elif len(screens) != len(set(screens)):
        errors.append("03-SCREEN-SPEC.md: duplicate screen heading")
    anchors = ANCHOR_REF.findall(screen)
    if len(anchors) != len(set(anchors)):
        errors.append("03-SCREEN-SPEC.md: duplicate wireframe anchor")
    html_ids = set(HTML_ID.findall(wireframe))
    for anchor in sorted(set(anchors) - html_ids):
        errors.append(f"04-WIREFRAME.html: missing referenced anchor #{anchor}")
    screen_ids = {value for value in html_ids if value.startswith("screen-")}
    if not screen_ids:
        errors.append("04-WIREFRAME.html: no screen-* id")

    ia_ids = set(REQ_ID.findall(ia))
    screen_req_ids = set(REQ_ID.findall(screen))
    handoff_ids = set(REQ_ID.findall(handoff))
    for requirement in sorted(screen_req_ids - ia_ids):
        errors.append(
            f"03-SCREEN-SPEC.md: {requirement} is absent from 01-IA.md"
        )
    for requirement in sorted(screen_req_ids - handoff_ids):
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
