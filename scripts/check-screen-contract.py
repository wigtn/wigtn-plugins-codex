#!/usr/bin/env python3
"""Regression checks for the five-artifact screen contract."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "plugins/wigtn-plugins-with-codex/scripts/validate-screen-spec.py"


VALID = {
    "01-IA.md": "# Information Architecture\n\n| Page | FR |\n|---|---|\n| /x | FR-001 |\n",
    "02-USER-FLOW.md": (
        "# User Flow\n\n```mermaid\nflowchart LR\nA --> B\n```\n\n"
        "## Flow Coverage\n\n| AC | Flow |\n|---|---|\n| AC-001 | A |\n"
    ),
    "03-SCREEN-SPEC.md": (
        "# Screen Specifications\n\n## Screen: /x\n\n"
        "| Linked FRs | FR-001 |\n|---|---|\n"
        "\n### Wireframe Anchor\n\n→ `04-WIREFRAME.html#screen-x`\n"
    ),
    "04-WIREFRAME.html": (
        "<!doctype html><html><body><section id=\"screen-x\">X</section>"
        "</body></html>\n"
    ),
    "05-DEV-HANDOFF.md": (
        "# Dev Handoff\n\n| FR | Screen |\n|---|---|\n| FR-001 | /x |\n\n"
        "## Suggested Implementation Order\n\n1. X\n"
    ),
}


def run(directory: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(directory), "--json"],
        text=True,
        capture_output=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        valid = root / "valid"
        valid.mkdir()
        for name, text in VALID.items():
            (valid / name).write_text(text, encoding="utf-8")
        passed = run(valid)
        assert passed.returncode == 0 and '"valid": true' in passed.stdout

        broken = root / "broken"
        broken.mkdir()
        for name, text in VALID.items():
            (broken / name).write_text(text, encoding="utf-8")
        (broken / "04-WIREFRAME.html").write_text(
            '<section id="screen-other">{feature-name}</section>\n',
            encoding="utf-8",
        )
        failed = run(broken)
        assert failed.returncode == 1
        assert "unresolved template placeholders" in failed.stdout
        assert "missing referenced anchor #screen-x" in failed.stdout
    print("Screen contract: PASS (bundle/anchor/requirement)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
