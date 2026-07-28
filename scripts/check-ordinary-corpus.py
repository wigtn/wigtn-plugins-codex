#!/usr/bin/env python3
"""Validate ordinary-coding tasks, hidden faults, and reference solutions."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "ordinary"))

from task_bank import TASKS  # noqa: E402


def write_files(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def run(task: dict, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        task["command"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


def main() -> int:
    identifiers = [task["id"] for task in TASKS]
    if len(TASKS) != 12 or len(identifiers) != len(set(identifiers)):
        raise AssertionError("ordinary corpus must contain 12 unique tasks")
    if Counter(task["language"] for task in TASKS) != {
        "python": 4,
        "javascript": 4,
        "ruby": 4,
    }:
        raise AssertionError("ordinary corpus language balance changed")

    with tempfile.TemporaryDirectory(prefix="wigtn-ordinary-corpus-") as temporary:
        base = Path(temporary)
        for task in TASKS:
            public = base / task["id"] / "public"
            fault = base / task["id"] / "fault"
            reference = base / task["id"] / "reference"
            write_files(public, task["files"])
            visible = run(task, public)
            if visible.returncode:
                raise AssertionError(
                    f"{task['id']}: visible tests reject the starting fixture\n"
                    + visible.stdout
                    + visible.stderr
                )
            shutil.copytree(public, fault)
            write_files(fault, task["hidden"])
            hidden_fault = run(task, fault)
            if hidden_fault.returncode == 0:
                raise AssertionError(
                    f"{task['id']}: injected fault is not detected by hidden tests"
                )
            shutil.copytree(public, reference)
            write_files(reference, task["fixed"])
            write_files(reference, task["hidden"])
            solved = run(task, reference)
            if solved.returncode:
                raise AssertionError(
                    f"{task['id']}: reference solution failed\n"
                    + solved.stdout
                    + solved.stderr
                )
    print("Ordinary corpus: PASS (12 tasks, 3 languages, fault/reference)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
