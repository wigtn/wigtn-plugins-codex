#!/usr/bin/env python3
"""Regression tests for deterministic paired evaluation scheduling."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from importlib.util import module_from_spec, spec_from_file_location


module_spec = spec_from_file_location(
    "make_eval_schedule", ROOT / "scripts" / "make-eval-schedule.py"
)
if module_spec is None or module_spec.loader is None:
    raise RuntimeError("schedule module unavailable")
schedule_module = module_from_spec(module_spec)
module_spec.loader.exec_module(schedule_module)


def main() -> int:
    cases = [("alpha", "a.txt"), ("beta", "b.txt"), ("gamma", "c.txt")]
    arms = ["bare", "plugin"]
    first = schedule_module.schedule(cases, arms, 4, "frozen-v1")
    second = schedule_module.schedule(cases, arms, 4, "frozen-v1")
    if first != second:
        raise AssertionError("same seed did not reproduce schedule")
    if first == schedule_module.schedule(cases, arms, 4, "frozen-v2"):
        raise AssertionError("different seed did not change schedule")
    if len(first) != 24:
        raise AssertionError("schedule row count is wrong")
    by_pair: dict[str, list[tuple]] = defaultdict(list)
    for row in first:
        by_pair[row[0]].append(row)
    if len(by_pair) != 12:
        raise AssertionError("pair count is wrong")
    for pair_id, rows in by_pair.items():
        if Counter(row[2] for row in rows) != Counter(arms):
            raise AssertionError(f"{pair_id}: arms are not paired exactly once")
        if len({row[3] for row in rows}) != 1 or len(
            {row[5] for row in rows}
        ) != 1:
            raise AssertionError(f"{pair_id}: pair metadata mismatch")
    first_arm_counts = Counter(rows[0][2] for rows in by_pair.values())
    if set(first_arm_counts) != set(arms):
        raise AssertionError("counterbalance never places both arms first")
    four_arms = ["bare", "core4", "full8", "full9"]
    balanced = schedule_module.schedule(cases, four_arms, 4, "latin-v1")
    position_counts: dict[str, Counter[int]] = defaultdict(Counter)
    for index in range(0, len(balanced), len(four_arms)):
        for position, row in enumerate(
            balanced[index : index + len(four_arms)], start=1
        ):
            position_counts[row[2]][position] += 1
    expected_positions = Counter({1: 3, 2: 3, 3: 3, 4: 3})
    if any(
        position_counts[arm] != expected_positions for arm in four_arms
    ):
        raise AssertionError(
            f"block-wise position balance failed: {dict(position_counts)}"
        )
    try:
        schedule_module.schedule(cases, ["bare", "bare"], 1, "bad")
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate arms were accepted")
    try:
        schedule_module.schedule(cases, arms, 0, "bad")
    except ValueError:
        pass
    else:
        raise AssertionError("zero repetitions were accepted")
    with tempfile.TemporaryDirectory(prefix="wigtn-schedule-score-") as temporary:
        root = Path(temporary)
        rows = schedule_module.schedule([("alpha", "a.txt")], arms, 1, "score")
        (root / "SCHEDULE.tsv").write_text(
            "pair_id\torder\tarm\tcase\tprompt\trepeat\n"
            + "\n".join(
                "\t".join(str(value) for value in row) for row in rows
            )
            + "\n",
            encoding="utf-8",
        )
        for pair_id, order, arm, case_id, _, repetition in rows:
            arm_root = root / "runs" / arm
            arm_root.mkdir(parents=True)
            stem = arm_root / f"{case_id}.{repetition}"
            Path(f"{stem}.meta.json").write_text(
                json.dumps(
                    {
                        "pair_id": pair_id,
                        "schedule_order": order,
                        "arm": arm,
                        "case": case_id,
                        "repeat": repetition,
                        "exit_code": 0,
                        "duration_seconds": 1,
                        "model": "test",
                        "effort": "test",
                        "schedule_seed": "score",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            Path(f"{stem}.out.md").write_text("ok\n", encoding="utf-8")
            Path(f"{stem}.log").write_text("", encoding="utf-8")
        scorer = ROOT / "scripts" / "score-behavior-smoke.py"
        completed = subprocess.run(
            [sys.executable, "-B", str(scorer), str(root)],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode:
            raise AssertionError("complete paired score failed: " + completed.stdout)
        missing_meta = root / "runs/plugin/alpha.1.meta.json"
        missing_meta.unlink()
        incomplete = subprocess.run(
            [sys.executable, "-B", str(scorer), str(root)],
            text=True,
            capture_output=True,
            check=False,
        )
        if incomplete.returncode == 0 or "scheduled run missing" not in incomplete.stdout:
            raise AssertionError("incomplete paired run was not rejected")
    print(
        "Evaluation schedule: PASS "
        "(deterministic/block-balanced/paired)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
