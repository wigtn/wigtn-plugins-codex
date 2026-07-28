#!/usr/bin/env python3
"""Regression checks for optional project context."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT / "plugins/wigtn-plugins-with-codex/scripts/validate-project-context.py"
)


def check(name: str, expected: int, diagnostic: str) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            str(ROOT / f"tests/evidence/{name}.json"),
            "--json",
        ],
        text=True,
        capture_output=True,
    )
    if completed.returncode != expected or diagnostic not in completed.stdout:
        raise AssertionError(completed.stdout + completed.stderr)


def main() -> int:
    check("valid-project-context", 0, '"valid": true')
    check("invalid-project-context", 1, "repository-relative")
    print("Project context: PASS (valid/invalid)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
