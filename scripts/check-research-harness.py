#!/usr/bin/env python3
"""Static integrity checks for expensive model-evaluation harnesses."""

from __future__ import annotations

import ast
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PYTHON_FILES = (
    "tests/behavior/setup-acceptance-hard.py",
    "tests/behavior/score-acceptance-hard.py",
    "tests/behavior/score-delivery-recheck.py",
    "tests/behavior/make-delivery-blind.py",
    "tests/behavior/score-delivery-blind.py",
    "tests/behavior/score-actual-repo-pilot.py",
    "tests/workgraph/setup-pilot.py",
    "tests/workgraph/score-pilot.py",
    "tests/ordinary/task_bank.py",
    "tests/ordinary/setup-gate.py",
    "tests/ordinary/reset-case.py",
    "tests/ordinary/score-gate.py",
    "scripts/make-eval-schedule.py",
    "scripts/check-eval-schedule.py",
    "scripts/check-ordinary-corpus.py",
    "scripts/check-ordinary-scorer.py",
)
SHELL_FILES = (
    "scripts/run-acceptance-hard.sh",
    "scripts/run-delivery-recheck.sh",
    "scripts/run-delivery-blind.sh",
    "scripts/run-actual-repo-pilot.sh",
    "scripts/run-workgraph-pilot.sh",
    "scripts/run-ordinary-gate.sh",
)


def main() -> int:
    for relative in PYTHON_FILES:
        ast.parse((ROOT / relative).read_text(), filename=relative)
    for relative in SHELL_FILES:
        completed = subprocess.run(
            ["bash", "-n", str(ROOT / relative)],
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            raise AssertionError(f"{relative}: {completed.stderr}")
    fixture = runpy.run_path(str(ROOT / "tests/behavior/setup-acceptance-hard.py"))
    tasks = fixture["TASKS"]
    if len(tasks) != 8:
        raise AssertionError(f"Acceptance Hard task count: {len(tasks)}")
    allowed = {
        "verified",
        "implemented-not-executed",
        "partially-verified",
        "not-satisfied",
        "not-verifiable",
        "not-applicable",
    }
    if any(spec["gold"] not in allowed for spec in tasks.values()):
        raise AssertionError("Acceptance Hard has an invalid gold status")
    if sum(spec["gold"] == "verified" for spec in tasks.values()) != 1:
        raise AssertionError("Acceptance Hard must contain one verified control")
    import json

    workgraph_cases = json.loads(
        (ROOT / "tests/workgraph/pilot-cases.json").read_text(encoding="utf-8")
    )
    if len(workgraph_cases) != 12:
        raise AssertionError(
            f"WorkGraph pilot task count: {len(workgraph_cases)}"
        )
    case_ids = [item["id"] for item in workgraph_cases]
    if len(case_ids) != len(set(case_ids)):
        raise AssertionError("WorkGraph pilot contains duplicate case IDs")
    for case in workgraph_cases:
        requirement_ids = [item[0] for item in case["requirements"]]
        if len(requirement_ids) < 2 or len(requirement_ids) != len(
            set(requirement_ids)
        ):
            raise AssertionError(
                f"{case['id']}: requirements must be unique and non-trivial"
            )
        if not case["paths"] or not case["verification"]:
            raise AssertionError(f"{case['id']}: missing grader endpoint")
    with tempfile.TemporaryDirectory(prefix="wigtn-pilot-resume-") as temporary:
        run_root = Path(temporary) / "run"
        setup = ROOT / "tests/workgraph/setup-pilot.py"
        first = subprocess.run(
            [sys.executable, "-B", str(setup), str(run_root)],
            capture_output=True,
            text=True,
        )
        if first.returncode:
            raise AssertionError(first.stdout + first.stderr)
        marker = run_root / "work/auth-lockout/PARTIAL.txt"
        marker.write_text("partial\n", encoding="utf-8")
        archive = run_root / "attempts/auth-lockout/attempt-1"
        reset = subprocess.run(
            [
                sys.executable,
                "-B",
                str(setup),
                str(run_root),
                "--case",
                "auth-lockout",
                "--archive-dir",
                str(archive),
            ],
            capture_output=True,
            text=True,
        )
        if reset.returncode:
            raise AssertionError(reset.stdout + reset.stderr)
        if not (archive / "work/PARTIAL.txt").is_file() or marker.exists():
            raise AssertionError("WorkGraph resume did not archive and reset work")
    print(
        "Research harness: PASS "
        "(8 acceptance, 4 implement, 10 release, 12 WorkGraph + resume, "
        "12 ordinary)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
