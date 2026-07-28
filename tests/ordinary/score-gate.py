#!/usr/bin/env python3
"""Deterministically score the ordinary-coding non-interference gate."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "ordinary"))

from task_bank import BY_ID, TASKS  # noqa: E402


IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
HARNESS_NAMES = {
    ".wigtn",
    "PRD.md",
    "PRODUCT-SPEC.md",
    "SCREEN-SPEC.md",
    "DEV-HANDOFF.md",
    "RELEASE-EVIDENCE.md",
    "ACCEPTANCE-EVIDENCE.md",
}


def write_files(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def total_tokens(path: Path) -> int | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    matches = re.findall(r"tokens used\s*\n([\d,]+)", text, re.IGNORECASE)
    return int(matches[-1].replace(",", "")) if matches else None


def tracked_files(root: Path) -> dict[str, str]:
    from hashlib import sha256

    result = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        result[relative.as_posix()] = sha256(path.read_bytes()).hexdigest()
    return result


def has_harness_state(root: Path) -> tuple[bool, list[str]]:
    found = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in HARNESS_NAMES for part in relative.parts):
            found.append(relative.as_posix())
        elif path.is_file() and (
            path.name.startswith("PRD-")
            or path.name.startswith("SCREEN-SPEC")
            or path.name.startswith("WORKGRAPH")
        ):
            found.append(relative.as_posix())
    return bool(found), sorted(set(found))


def run_tests(task: dict, root: Path) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            task["command"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (completed.stdout + completed.stderr)[-4000:]
    return completed.returncode == 0, output


def load_schedule(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def rate(rows: list[dict], field: str) -> float:
    return sum(bool(row[field]) for row in rows) / len(rows) if rows else 0.0


def median_value(rows: list[dict], field: str) -> float | None:
    values = [row[field] for row in rows if row[field] is not None]
    return statistics.median(values) if values else None


def fmt_rate(value: float) -> str:
    return f"{value * 100:.1f}%"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()
    run_root = args.run_root
    schedule_path = run_root / "SCHEDULE.tsv"
    baseline_path = run_root / "BASELINE.json"
    if not schedule_path.is_file() or not baseline_path.is_file():
        print("ordinary gate: missing schedule or baseline", file=sys.stderr)
        return 2

    schedule = load_schedule(schedule_path)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    rows: list[dict] = []
    observed: set[tuple[str, str, int]] = set()
    score_root = run_root / "score-work"
    if score_root.exists():
        shutil.rmtree(score_root)

    for scheduled in schedule:
        arm = scheduled["arm"]
        case_id = scheduled["case"]
        repetition = int(scheduled["repeat"])
        key = (arm, case_id, repetition)
        if key in observed:
            errors.append(f"duplicate schedule row: {key}")
            continue
        observed.add(key)
        task = BY_ID.get(case_id)
        if task is None:
            errors.append(f"unknown task in schedule: {case_id}")
            continue
        stem = run_root / "runs" / arm / f"{case_id}.{repetition}"
        meta_path = Path(f"{stem}.meta.json")
        output_path = Path(f"{stem}.out.md")
        log_path = Path(f"{stem}.log")
        if not meta_path.is_file():
            errors.append(f"missing metadata: {arm}/{case_id}.{repetition}")
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid metadata {meta_path}: {exc}")
            continue
        expected_meta = (
            scheduled["pair_id"],
            int(scheduled["order"]),
            arm,
            case_id,
            repetition,
        )
        actual_meta = (
            meta.get("pair_id"),
            meta.get("schedule_order"),
            meta.get("arm"),
            meta.get("case"),
            meta.get("repeat"),
        )
        if actual_meta != expected_meta:
            errors.append(
                f"schedule mismatch {arm}/{case_id}.{repetition}: "
                f"{actual_meta} != {expected_meta}"
            )

        work = run_root / "work" / arm / case_id / str(repetition)
        if not work.is_dir():
            errors.append(f"missing worktree: {arm}/{case_id}.{repetition}")
            continue
        scoring = score_root / arm / case_id / str(repetition)
        scoring.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(work, scoring)
        visible_pass, visible_output = run_tests(task, scoring)
        write_files(scoring, task["hidden"])
        hidden_pass, hidden_output = run_tests(task, scoring)

        baseline_key = f"{arm}/{case_id}/{repetition}"
        expected_hashes = baseline.get(baseline_key)
        if expected_hashes is None:
            errors.append(f"missing baseline: {baseline_key}")
            expected_hashes = {}
        current_hashes = tracked_files(work)
        changed = sorted(
            path
            for path in set(expected_hashes) | set(current_hashes)
            if expected_hashes.get(path) != current_hashes.get(path)
        )
        allowed = set(task["allowed"])
        unexpected = sorted(path for path in changed if path not in allowed)
        state_created, state_paths = has_harness_state(work)
        sentinel = work / "USER-DRAFT.txt"
        sentinel_preserved = (
            sentinel.is_file()
            and sentinel.read_text(encoding="utf-8")
            == f"sentinel:{arm}:{case_id}:{repetition}\n"
        )
        output_nonempty = (
            output_path.is_file()
            and bool(output_path.read_text(encoding="utf-8", errors="ignore").strip())
        )
        model_exit = meta.get("exit_code") == 0 and output_nonempty
        row = {
            "pair_id": scheduled["pair_id"],
            "schedule_order": int(scheduled["order"]),
            "arm": arm,
            "case": case_id,
            "language": task["language"],
            "repeat": repetition,
            "model_exit": model_exit,
            "visible_pass": visible_pass,
            "hidden_pass": hidden_pass,
            "scope_clean": not unexpected,
            "unexpected_changes": unexpected,
            "no_harness_state": not state_created,
            "harness_state_paths": state_paths,
            "sentinel_preserved": sentinel_preserved,
            "tokens": total_tokens(log_path),
            "duration_seconds": meta.get("duration_seconds"),
            "visible_test_tail": visible_output if not visible_pass else "",
            "hidden_test_tail": hidden_output if not hidden_pass else "",
        }
        row["all_endpoints"] = all(
            row[field]
            for field in (
                "model_exit",
                "visible_pass",
                "hidden_pass",
                "scope_clean",
                "no_harness_state",
                "sentinel_preserved",
            )
        )
        rows.append(row)

    expected_runs = len(schedule)
    if len(rows) != expected_runs:
        errors.append(f"scored {len(rows)}/{expected_runs} scheduled runs")
    arms = sorted({item["arm"] for item in schedule})
    aggregate: dict[str, dict] = {}
    for arm in arms:
        arm_rows = [row for row in rows if row["arm"] == arm]
        aggregate[arm] = {
            "runs": len(arm_rows),
            "hidden_pass_rate": rate(arm_rows, "hidden_pass"),
            "visible_pass_rate": rate(arm_rows, "visible_pass"),
            "all_endpoint_rate": rate(arm_rows, "all_endpoints"),
            "scope_clean_rate": rate(arm_rows, "scope_clean"),
            "no_harness_state_rate": rate(arm_rows, "no_harness_state"),
            "sentinel_preserved_rate": rate(arm_rows, "sentinel_preserved"),
            "median_tokens": median_value(arm_rows, "tokens"),
            "median_duration_seconds": median_value(
                arm_rows, "duration_seconds"
            ),
        }

    paired: dict[str, dict] = {}
    bare_index = {
        (row["case"], row["repeat"]): row
        for row in rows
        if row["arm"] == "bare"
    }
    for arm in arms:
        if arm == "bare":
            continue
        improved = harmed = tied_pass = tied_fail = 0
        for row in [item for item in rows if item["arm"] == arm]:
            control = bare_index.get((row["case"], row["repeat"]))
            if control is None:
                continue
            pair = (control["hidden_pass"], row["hidden_pass"])
            if pair == (False, True):
                improved += 1
            elif pair == (True, False):
                harmed += 1
            elif pair == (True, True):
                tied_pass += 1
            else:
                tied_fail += 1
        total = improved + harmed + tied_pass + tied_fail
        paired[arm] = {
            "pairs": total,
            "improved": improved,
            "harmed": harmed,
            "tied_pass": tied_pass,
            "tied_fail": tied_fail,
            "paired_hidden_delta": (
                (improved - harmed) / total if total else None
            ),
        }

    full = aggregate.get("full9")
    bare = aggregate.get("bare")
    token_overhead = None
    if (
        full
        and bare
        and full["median_tokens"] is not None
        and bare["median_tokens"]
    ):
        token_overhead = (
            full["median_tokens"] / bare["median_tokens"] - 1
        )
    gates = {
        "complete_protocol": not errors and len(rows) == expected_runs,
        "no_hidden_regression": bool(
            full
            and bare
            and paired.get("full9", {}).get("harmed", 1) == 0
            and full["hidden_pass_rate"] >= bare["hidden_pass_rate"]
        ),
        "no_unsolicited_harness_state": bool(
            full and full["no_harness_state_rate"] == 1.0
        ),
        "scope_not_worse_than_bare": bool(
            full
            and bare
            and full["scope_clean_rate"] >= bare["scope_clean_rate"]
        ),
        "sentinel_integrity": bool(
            full and full["sentinel_preserved_rate"] == 1.0
        ),
        "token_overhead_at_most_10pct": bool(
            token_overhead is not None and token_overhead <= 0.10
        ),
    }
    gate_passed = all(gates.values())
    result = {
        "protocol": {
            "task_count": len(TASKS),
            "languages": sorted({task["language"] for task in TASKS}),
            "scheduled_runs": expected_runs,
            "scored_runs": len(rows),
            "status": "complete" if not errors else "incomplete",
            "errors": errors,
            "interpretation": (
                "Development non-interference gate; not a confirmatory quality-lift study."
            ),
        },
        "rows": rows,
        "aggregate": aggregate,
        "paired_vs_bare": paired,
        "full9_token_overhead": token_overhead,
        "gates": gates,
        "gate_passed": gate_passed,
    }
    (run_root / "RESULTS.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Ordinary-coding non-interference gate",
        "",
        "Development gate on 12 synthetic bug-fix tasks across Python, JavaScript, "
        "and Ruby. Hidden tests are deterministic. This can reject an intrusive "
        "harness candidate; it cannot establish general quality lift.",
        "",
        "| Arm | Hidden | All endpoints | Scope clean | No harness state | Median tokens | Median duration |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in arms:
        item = aggregate[arm]
        report.append(
            f"| {arm} | {fmt_rate(item['hidden_pass_rate'])} | "
            f"{fmt_rate(item['all_endpoint_rate'])} | "
            f"{fmt_rate(item['scope_clean_rate'])} | "
            f"{fmt_rate(item['no_harness_state_rate'])} | "
            f"{item['median_tokens'] if item['median_tokens'] is not None else 'n/a'} | "
            f"{item['median_duration_seconds'] if item['median_duration_seconds'] is not None else 'n/a'}s |"
        )
    report.extend(
        [
            "",
            "## Paired hidden-test outcomes vs bare",
            "",
            "| Arm | Pairs | Improved | Harmed | Tied pass | Tied fail | Delta |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for arm, item in paired.items():
        delta = item["paired_hidden_delta"]
        report.append(
            f"| {arm} | {item['pairs']} | {item['improved']} | "
            f"{item['harmed']} | {item['tied_pass']} | {item['tied_fail']} | "
            f"{delta:+.3f} |"
        )
    report.extend(["", "## Full9 gate", ""])
    report.extend(
        f"- {'PASS' if passed else 'FAIL'} — {name.replace('_', ' ')}"
        for name, passed in gates.items()
    )
    report.extend(
        [
            "",
            f"Overall: **{'PASS' if gate_passed else 'FAIL'}**",
            "",
            "A pilot pass permits a larger confirmatory run; it does not justify "
            "a publication claim by itself.",
        ]
    )
    if errors:
        report.extend(["", "## Protocol errors", ""])
        report.extend(f"- {error}" for error in errors)
    (run_root / "RESULTS.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print(
        f"Ordinary gate: {'PASS' if gate_passed else 'FAIL'} "
        f"({len(rows)}/{expected_runs} runs scored)"
    )
    print(run_root / "RESULTS.md")
    return 2 if errors else (0 if gate_passed else 1)


if __name__ == "__main__":
    raise SystemExit(main())
