#!/usr/bin/env python3
"""Verify structural integrity of a Mermaid handDrawn source, SVG, and PNG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
HANGUL = re.compile(r"[가-힣]")


def inspect(source: Path, svg: Path, png: Path) -> dict[str, object]:
    errors: list[str] = []
    for path in (source, svg, png):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        return {"valid": False, "errors": errors}

    source_text = source.read_text(encoding="utf-8", errors="replace")
    if not re.search(r"look\s*:\s*handDrawn\b", source_text, re.I):
        errors.append("source: missing config look: handDrawn")
    if "accTitle:" not in source_text or "accDescr:" not in source_text:
        errors.append("source: accTitle and accDescr are required")
    if (
        HANGUL.search(source_text)
        and re.search(r"\bflowchart\b", source_text, re.I)
        and not re.search(r"htmlLabels\s*:\s*false\b", source_text, re.I)
    ):
        errors.append("source: Korean flowcharts require htmlLabels: false")

    svg_text = svg.read_text(encoding="utf-8", errors="replace")
    try:
        root = ET.fromstring(svg_text)
        if root.tag.rsplit("}", 1)[-1] != "svg":
            errors.append("SVG: root element is not <svg>")
    except ET.ParseError as exc:
        errors.append(f"SVG: invalid XML: {exc}")
    if "syntax error" in svg_text.casefold():
        errors.append("SVG: renderer reported a syntax error")
    if re.search(r"(?:href|src)=[\"']https?://", svg_text, re.I):
        errors.append("SVG: external network resource is not portable")
    if HANGUL.search(source_text) and not HANGUL.search(svg_text):
        errors.append("SVG: Korean source labels are absent from rendered text")

    png_bytes = png.read_bytes()
    width = height = 0
    if len(png_bytes) < 24 or not png_bytes.startswith(PNG_SIGNATURE):
        errors.append("PNG: invalid signature or truncated header")
    else:
        width, height = struct.unpack(">II", png_bytes[16:24])
        if width < 200 or height < 120:
            errors.append(f"PNG: render is too small ({width}x{height})")

    return {
        "valid": not errors,
        "errors": errors,
        "source": str(source),
        "svg": str(svg),
        "png": str(png),
        "png_width": width,
        "png_height": height,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("svg", type=Path)
    parser.add_argument("png", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = inspect(args.source, args.svg, args.png)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["valid"]:
        print(
            "Hand-drawn artifacts: PASS "
            f"({result['png_width']}x{result['png_height']})"
        )
    else:
        print("Hand-drawn artifacts: FAIL")
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
