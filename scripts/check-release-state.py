#!/usr/bin/env python3
"""Regression checks for the read-only release-state inspector."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
INSPECTOR = ROOT / "plugins/wigtn-plugins-with-codex/scripts/inspect-release-state.py"


def run(root: Path, *args: str) -> None:
    subprocess.run(args, cwd=root, check=True, capture_output=True, text=True)


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        repo = Path(temp)
        run(repo, "git", "init", "-q", "-b", "main")
        run(repo, "git", "config", "user.email", "test@example.com")
        run(repo, "git", "config", "user.name", "Test")
        (repo / "tracked.txt").write_text("base\n")
        (repo / "staged.txt").write_text("base\n")
        run(repo, "git", "add", ".")
        run(repo, "git", "commit", "-qm", "initial")
        (repo / "tracked.txt").write_text("changed\n")
        (repo / "staged.txt").write_text("staged\n")
        run(repo, "git", "add", "staged.txt")
        (repo / "draft.txt").write_text("draft\n")
        completed = subprocess.run(
            [sys.executable, str(INSPECTOR), str(repo)],
            check=True,
            capture_output=True,
            text=True,
        )
        state = json.loads(completed.stdout)
        assert state["branch"] == "main" and state["upstream"] is None
        assert state["staged"] == ["staged.txt"]
        assert state["unstaged"] == ["tracked.txt"]
        assert state["untracked"] == ["draft.txt"]
        assert state["conflicts"] == [] and state["operation"] == "none"
    print("Release state: PASS (staged/unstaged/untracked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
