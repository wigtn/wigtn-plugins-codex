#!/usr/bin/env python3
"""Regression tests for Compact and Full PRD profiles."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT
    / "plugins"
    / "wigtn-plugins-with-codex"
    / "skills"
    / "product-spec"
    / "scripts"
    / "validate-prd.py"
)
FIXTURES = ROOT / "tests" / "prd"


def check(name: str, expected: int, diagnostic: str) -> None:
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR), str(FIXTURES / name), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    if completed.returncode != expected:
        raise AssertionError(
            f"{name}: expected exit {expected}, got "
            f"{completed.returncode}\n{output}"
        )
    if diagnostic not in output:
        raise AssertionError(f"{name}: missing {diagnostic!r}\n{output}")


def main() -> int:
    check("valid-compact.md", 0, '"profile": "compact"')
    check("valid-compact-generic-id.md", 0, '"profile": "compact"')
    check("valid-full.md", 0, '"profile": "full"')
    check("invalid-compact.md", 1, '"code": "acceptance-shape"')
    print("PRD contracts: PASS (4 cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
