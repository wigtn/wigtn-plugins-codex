#!/usr/bin/env python3
"""Verify structural integrity of a Mermaid handDrawn source, SVG, and PNG."""

from __future__ import annotations

import argparse
import binascii
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
HANGUL = re.compile(r"[가-힣]")
REMOTE_RESOURCE = re.compile(
    r'(?:href|src)\s*=\s*["\']?[^"\'>]*(?:(?:https?:)?//)'
    r'|(?:@import\s+(?:url\(\s*)?|url\(\s*)["\']?\s*(?:(?:https?:)?//)',
    re.I,
)


def inspect_png(data: bytes) -> tuple[int, int, list[str]]:
    errors: list[str] = []
    width = height = 0
    if not data.startswith(PNG_SIGNATURE):
        return width, height, ["PNG: invalid signature"]
    offset = len(PNG_SIGNATURE)
    chunks: list[bytes] = []
    while offset < len(data):
        if len(data) - offset < 12:
            errors.append("PNG: truncated chunk header")
            break
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            errors.append(f"PNG: truncated {kind.decode('ascii', 'replace')} chunk")
            break
        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : end])[0]
        actual_crc = binascii.crc32(kind + payload) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            errors.append(f"PNG: invalid {kind.decode('ascii', 'replace')} CRC")
        chunks.append(kind)
        if len(chunks) == 1:
            if kind != b"IHDR" or length != 13:
                errors.append("PNG: first chunk must be a 13-byte IHDR")
            else:
                width, height = struct.unpack(">II", payload[:8])
                if width == 0 or height == 0:
                    errors.append("PNG: dimensions must be non-zero")
        offset = end
        if kind == b"IEND":
            if length != 0:
                errors.append("PNG: IEND chunk must be empty")
            if offset != len(data):
                errors.append("PNG: trailing bytes after IEND")
            break
    if b"IDAT" not in chunks:
        errors.append("PNG: missing IDAT chunk")
    if not chunks or chunks[-1] != b"IEND":
        errors.append("PNG: missing terminal IEND chunk")
    return width, height, errors


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
    if REMOTE_RESOURCE.search(svg_text):
        errors.append("SVG: external network resource is not portable")
    if HANGUL.search(source_text) and not HANGUL.search(svg_text):
        errors.append("SVG: Korean source labels are absent from rendered text")

    width, height, png_errors = inspect_png(png.read_bytes())
    errors.extend(png_errors)
    if width and height and (width < 200 or height < 120):
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
