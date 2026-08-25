#!/usr/bin/env python3
"""Verify portability and structural WIGTN markers in an HTML deck."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re


class DeckParser(HTMLParser):
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.slide_depths: list[int] = []
        self.slide_has_signature: list[bool] = []
        self.has_viewport = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        if tag == "meta" and (values.get("name") or "").casefold() == "viewport":
            self.has_viewport = True
        if tag not in self.VOID_TAGS:
            self.depth += 1
        if "slide" in classes:
            self.slide_depths.append(self.depth)
            self.slide_has_signature.append(False)
        if self.slide_depths and classes.intersection({"wigtn-dot", "wigtn-dot-char"}):
            self.slide_has_signature[-1] = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.VOID_TAGS:
            return
        if self.slide_depths and self.slide_depths[-1] == self.depth:
            self.slide_depths.pop()
        self.depth = max(0, self.depth - 1)


def inspect(path: Path) -> dict[str, object]:
    errors: list[str] = []
    if not path.is_file():
        return {"valid": False, "errors": [f"missing file: {path}"]}
    text = path.read_text(encoding="utf-8", errors="replace")
    parser = DeckParser()
    parser.feed(text)
    if not parser.slide_has_signature:
        errors.append("HTML: no .slide elements")
    missing = [
        str(index)
        for index, present in enumerate(parser.slide_has_signature, 1)
        if not present
    ]
    if missing:
        errors.append("HTML: missing WIGTN signature on slides " + ", ".join(missing))
    if not parser.has_viewport:
        errors.append("HTML: missing viewport meta")
    if re.search(r"<(?:script|link|img)\b[^>]+(?:src|href)=[\"']https?://", text, re.I):
        errors.append("HTML: external network resource is not self-contained")
    upper = text.upper()
    if "#1E1E28" not in upper and "#15151E" not in upper:
        errors.append("HTML: missing WIGTN ink token")
    if "#9B51E0" not in upper and "#A85FEA" not in upper:
        errors.append("HTML: missing WIGTN purple token")
    if "prefers-reduced-motion" not in text:
        errors.append("HTML: missing reduced-motion handling")
    if "ArrowRight" not in text or "ArrowLeft" not in text:
        errors.append("HTML: missing arrow-key navigation")
    return {
        "valid": not errors,
        "errors": errors,
        "slides": len(parser.slide_has_signature),
        "path": str(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = inspect(args.html)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["valid"]:
        print(f"WIGTN HTML deck: PASS ({result['slides']} slides)")
    else:
        print("WIGTN HTML deck: FAIL")
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
