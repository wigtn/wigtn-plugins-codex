#!/usr/bin/env python3
"""Regression checks for diagram and WIGTN presentation delivery contracts."""

from __future__ import annotations

import binascii
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import zlib


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "plugins" / "wigtn-plugins-with-codex" / "skills"
DIAGRAM_CHECK = CORE / "handdrawn-diagram" / "scripts" / "verify-artifacts.py"
HTML_CHECK = CORE / "wigtn-presentation" / "scripts" / "verify-html-deck.py"


def png(width: int, height: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
        )

    rows = b"".join(b"\x00" + b"\xff\xff\xff" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], text=True, capture_output=True, check=False
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "flow.mmd"
        svg = root / "flow.svg"
        image = root / "flow.png"
        source.write_text(
            "---\nconfig:\n  look: handDrawn\n  flowchart:\n"
            "    htmlLabels: false\n---\nflowchart TD\n"
            "  accTitle: 요청 처리 흐름\n  accDescr: 요청을 처리하는 흐름\n"
            '  A["요청"] --> B["완료"]\n',
            encoding="utf-8",
        )
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180">'
            "<text>요청 처리 흐름</text></svg>\n",
            encoding="utf-8",
        )
        image.write_bytes(png(320, 180))
        passed = run(str(DIAGRAM_CHECK), str(source), str(svg), str(image), "--json")
        assert passed.returncode == 0 and '"valid": true' in passed.stdout

        source.write_text('flowchart TD\n  A["요청"] --> B["완료"]\n', encoding="utf-8")
        failed = run(str(DIAGRAM_CHECK), str(source), str(svg), str(image), "--json")
        assert failed.returncode == 1 and "look: handDrawn" in failed.stdout

        deck = root / "deck.html"
        deck.write_text(
            '<!doctype html><html><head><meta name="viewport" content="width=device-width">'
            '<style>:root{--ink:#1E1E28;--purple:#9B51E0}'
            '@media(prefers-reduced-motion:reduce){*{transition:none}}</style></head><body>'
            '<section class="slide"><span class="wigtn-dot"></span></section>'
            '<section class="slide"><span class="wigtn-dot-char">.</span></section>'
            '<script>addEventListener("keydown",e=>{if(e.key==="ArrowRight"){}'
            'if(e.key==="ArrowLeft"){}})</script></body></html>',
            encoding="utf-8",
        )
        passed = run(str(HTML_CHECK), str(deck), "--json")
        assert passed.returncode == 0 and '"valid": true' in passed.stdout

        deck.write_text(
            '<html><head><script src="https://cdn.example.test/deck.js"></script></head>'
            '<body><section class="slide"></section></body></html>',
            encoding="utf-8",
        )
        failed = run(str(HTML_CHECK), str(deck), "--json")
        assert failed.returncode == 1 and "external network resource" in failed.stdout

    presentation = CORE / "wigtn-presentation"
    brand = (presentation / "references" / "brand.md").read_text(encoding="utf-8")
    guide = (presentation / "references" / "design-guide.md").read_text(encoding="utf-8")
    skill = (presentation / "SKILL.md").read_text(encoding="utf-8")
    assert "section-inverse" in brand
    assert "brand overlay" in skill and "PPTX" in skill and "HTML" in skill
    assert "design-system-reference" not in guide
    assert "Google Fonts/CDN" not in brand
    print("Visual contracts: PASS (diagram/html/presentation-routing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
