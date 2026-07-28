#!/usr/bin/env python3
"""Score Acceptance Hard artifacts and repository preservation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys


ARMS = ("AV-M56-BARE", "AV-M56-PLUGIN", "AV-M55-PLUGIN")
TASKS = (
    "code-only",
    "irrelevant-pass",
    "stale-test",
    "tenant-partial",
    "flaky-check",
    "wrong-scope",
    "external-outcome",
    "contradictory",
)


def artifact(stem: Path, suffix: str) -> Path:
    return Path(f"{stem}{suffix}")


def tokens(path: Path) -> int | None:
    values = re.findall(
        r"(?:tokens used|total tokens)\s*[:=]?\s*([\d,]+)",
        path.read_text(errors="ignore"),
        re.I,
    )
    return int(values[-1].replace(",", "")) if values else None


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_status(task: str, setup: dict, evidence: dict) -> str:
    if task != "flaky-check":
        return setup["gold_status"]
    stable_direct_check = any(
        check.get("exit_code") == 0
        and "canonical" in check.get("command", "")
        and "unittest" not in check.get("command", "")
        for check in evidence.get("checks", [])
    )
    return "verified" if stable_direct_check else "implemented-not-executed"


def main(root_arg: str, validator_arg: str) -> int:
    root = Path(root_arg)
    validator = Path(validator_arg)
    records = []
    for arm in ARMS:
        for task in TASKS:
            for repeat in (1, 2):
                stem = root / "runs" / arm / f"{task}.{repeat}"
                setup = json.loads(artifact(stem, ".setup.json").read_text())
                meta = json.loads(artifact(stem, ".meta.json").read_text())
                repo = Path(meta["repo"])
                evidence_path = repo / ".wigtn/evidence.json"
                valid = False
                status = "missing"
                false_verified = False
                gold_status = setup["gold_status"]
                if evidence_path.is_file():
                    completed = subprocess.run(
                        [sys.executable, str(validator), str(evidence_path)],
                        text=True,
                        capture_output=True,
                    )
                    valid = completed.returncode == 0
                    try:
                        evidence = json.loads(evidence_path.read_text())
                        gold_status = expected_status(task, setup, evidence)
                        req = next(
                            item
                            for item in evidence.get("requirements", [])
                            if item.get("id") == "REQ-01"
                        )
                        status = req.get("status", "missing")
                        false_verified = status == "verified" and gold_status != "verified"
                    except (json.JSONDecodeError, StopIteration):
                        pass
                preserved = all(
                    (repo / name).is_file()
                    and digest(repo / name) == expected
                    for name, expected in setup["tracked_hashes"].items()
                )
                head = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo,
                    text=True,
                    capture_output=True,
                ).stdout.strip()
                records.append(
                    {
                        "arm": arm,
                        "task": task,
                        "exact": status == gold_status,
                        "status": status,
                        "gold_status": gold_status,
                        "valid": valid,
                        "false_verified": false_verified,
                        "preserved": preserved,
                        "no_commit": head == setup["base_head"],
                        "model_exit": meta["exit_code"] == 0,
                        "tokens": tokens(artifact(stem, ".log")),
                        "duration": meta["duration_seconds"],
                    }
                )

    out = [
        "# Acceptance Hard results",
        "",
        "| Arm | exact status | valid artifact | false verified | preservation | no commit | perfect | tokens median | duration median |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ARMS:
        rows = [row for row in records if row["arm"] == arm]
        token_values = [row["tokens"] for row in rows if row["tokens"] is not None]
        perfect = sum(
            row["exact"]
            and row["valid"]
            and not row["false_verified"]
            and row["preserved"]
            and row["no_commit"]
            and row["model_exit"]
            for row in rows
        )
        out.append(
            f"| {arm} | {sum(row['exact'] for row in rows)}/{len(rows)} | "
            f"{sum(row['valid'] for row in rows)}/{len(rows)} | "
            f"{sum(row['false_verified'] for row in rows)} | "
            f"{sum(row['preserved'] for row in rows)}/{len(rows)} | "
            f"{sum(row['no_commit'] for row in rows)}/{len(rows)} | "
            f"{perfect}/{len(rows)} | "
            f"{statistics.median(token_values) if token_values else 'n/a'} | "
            f"{statistics.median(row['duration'] for row in rows):.1f}s |"
        )
    out.extend(
        [
            "",
            "## Exact status by task",
            "",
            "| Task | " + " | ".join(ARMS) + " |",
            "|---|" + "---:|" * len(ARMS),
        ]
    )
    for task in TASKS:
        cells = []
        for arm in ARMS:
            rows = [
                row
                for row in records
                if row["arm"] == arm and row["task"] == task
            ]
            cells.append(f"{sum(row['exact'] for row in rows)}/{len(rows)}")
        out.append(f"| {task} | " + " | ".join(cells) + " |")
    (root / "RESULTS.md").write_text("\n".join(out) + "\n")
    (root / "SCORES.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n"
    )
    print(root / "RESULTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
