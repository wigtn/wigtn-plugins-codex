#!/usr/bin/env python3
"""Exercise positive and regression paths of the ordinary gate scorer."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "ordinary"))

from task_bank import BY_ID  # noqa: E402


def write_files(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def call(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, text=True, capture_output=True, check=False, timeout=60
    )


def main() -> int:
    arms = ["bare", "core4", "full8", "full9"]
    with tempfile.TemporaryDirectory(prefix="wigtn-ordinary-scorer-") as temporary:
        run_root = Path(temporary) / "run"
        setup = call(
            [
                sys.executable,
                "-B",
                str(ROOT / "tests/ordinary/setup-gate.py"),
                str(run_root),
                "--arms",
                *arms,
                "--repeat",
                "1",
            ]
        )
        if setup.returncode:
            raise AssertionError(setup.stdout + setup.stderr)
        schedule = call(
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts/make-eval-schedule.py"),
                str(run_root / "CASES.tsv"),
                "--arms",
                *arms,
                "--repeat",
                "1",
                "--seed",
                "ordinary-scorer-self-test",
                "--output",
                str(run_root / "SCHEDULE.tsv"),
            ]
        )
        if schedule.returncode:
            raise AssertionError(schedule.stdout + schedule.stderr)

        with (run_root / "SCHEDULE.tsv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        for row in rows:
            repetition = int(row["repeat"])
            task = BY_ID[row["case"]]
            work = (
                run_root
                / "work"
                / row["arm"]
                / row["case"]
                / str(repetition)
            )
            write_files(work, task["fixed"])
            stem = (
                run_root
                / "runs"
                / row["arm"]
                / f"{row['case']}.{repetition}"
            )
            stem.parent.mkdir(parents=True, exist_ok=True)
            Path(f"{stem}.meta.json").write_text(
                json.dumps(
                    {
                        "pair_id": row["pair_id"],
                        "schedule_order": int(row["order"]),
                        "arm": row["arm"],
                        "case": row["case"],
                        "repeat": repetition,
                        "exit_code": 0,
                        "duration_seconds": 1,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            Path(f"{stem}.out.md").write_text("done\n", encoding="utf-8")
            Path(f"{stem}.log").write_text(
                "tokens used\n1,000\n", encoding="utf-8"
            )

        scorer = ROOT / "tests/ordinary/score-gate.py"
        positive = call([sys.executable, "-B", str(scorer), str(run_root)])
        if positive.returncode:
            raise AssertionError(positive.stdout + positive.stderr)
        positive_result = json.loads(
            (run_root / "RESULTS.json").read_text(encoding="utf-8")
        )
        if not positive_result["gate_passed"]:
            raise AssertionError("positive scorer fixture did not pass")

        regression = BY_ID["py-ttl-boundary"]
        regressed_work = (
            run_root / "work/full9/py-ttl-boundary/1"
        )
        write_files(regressed_work, regression["files"])
        negative = call([sys.executable, "-B", str(scorer), str(run_root)])
        if negative.returncode != 1:
            raise AssertionError(
                "hidden regression was not rejected\n"
                + negative.stdout
                + negative.stderr
            )
        negative_result = json.loads(
            (run_root / "RESULTS.json").read_text(encoding="utf-8")
        )
        if negative_result["gates"]["no_hidden_regression"]:
            raise AssertionError("no_hidden_regression remained true")
    print("Ordinary scorer: PASS (positive + hidden-regression rejection)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
