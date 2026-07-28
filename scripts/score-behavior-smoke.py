#!/usr/bin/env python3
"""Score only execution health and protocol invariants for behavior smoke runs."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import csv


def total_tokens(path: Path) -> int | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    matches = re.findall(r"tokens used\s*\n([\d,]+)", text, re.IGNORECASE)
    return int(matches[-1].replace(",", "")) if matches else None


def main(root_arg: str) -> int:
    root = Path(root_arg)
    errors: list[str] = []
    rows: list[
        tuple[str, int, str, str, int, int, bool, int | None, int, int]
    ] = []
    schedule_path = root / "SCHEDULE.tsv"
    expected: dict[tuple[str, str, int], tuple[str, int]] = {}
    if not schedule_path.is_file():
        errors.append("SCHEDULE.tsv is missing")
    else:
        with schedule_path.open(encoding="utf-8", newline="") as handle:
            for item in csv.DictReader(handle, delimiter="\t"):
                key = (item["arm"], item["case"], int(item["repeat"]))
                if key in expected:
                    errors.append(f"duplicate schedule row: {key}")
                expected[key] = (item["pair_id"], int(item["order"]))
    observed: set[tuple[str, str, int]] = set()

    for meta_path in sorted((root / "runs").glob("*/*.meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        output_path = meta_path.with_name(meta_path.name.replace(".meta.json", ".out.md"))
        output = (
            output_path.read_text(encoding="utf-8", errors="ignore")
            if output_path.is_file()
            else ""
        )
        nonempty = bool(output.strip())
        log_path = meta_path.with_name(meta_path.name.replace(".meta.json", ".log"))
        row_key = (meta["arm"], meta["case"], meta["repeat"])
        if row_key in observed:
            errors.append(f"duplicate run metadata: {row_key}")
        observed.add(row_key)
        scheduled = expected.get(row_key)
        if scheduled is None:
            errors.append(f"run absent from schedule: {row_key}")
        elif scheduled != (meta.get("pair_id"), meta.get("schedule_order")):
            errors.append(
                f"schedule metadata mismatch: {row_key}, "
                f"expected={scheduled}, observed="
                f"{(meta.get('pair_id'), meta.get('schedule_order'))}"
            )
        rows.append(
            (
                meta.get("pair_id", "missing"),
                meta.get("schedule_order", -1),
                meta["arm"],
                meta["case"],
                meta["repeat"],
                meta["exit_code"],
                nonempty,
                total_tokens(log_path),
                len(output.encode("utf-8")),
                meta["duration_seconds"],
            )
        )
        if meta["exit_code"] != 0 or not nonempty:
            errors.append(
                f"{meta['arm']}/{meta['case']}.{meta['repeat']}: "
                f"exit={meta['exit_code']}, nonempty={nonempty}"
            )

    if not rows:
        errors.append("no behavior run metadata found")
    missing = sorted(set(expected) - observed)
    if missing:
        errors.extend(f"scheduled run missing: {item}" for item in missing)

    report = [
        "# Behavior smoke results",
        "",
        "This report scores execution health only. It does not score answer quality, "
        "causal plugin lift, or real-repository generalization.",
        "",
        "| Pair | Order | Arm | Case | Repeat | Exit | Output | Total tokens | Output bytes | Duration |",
        "|---|---:|---|---|---:|---:|---|---:|---:|---:|",
    ]
    report.extend(
        f"| {pair_id} | {order} | {arm} | {case} | {repeat} | {exit_code} | "
        f"{'yes' if nonempty else 'no'} | "
        f"{tokens if tokens is not None else 'n/a'} | {output_bytes} | {duration}s |"
        for (
            pair_id,
            order,
            arm,
            case,
            repeat,
            exit_code,
            nonempty,
            tokens,
            output_bytes,
            duration,
        ) in rows
    )
    if errors:
        report.extend(["", "## Failures", "", *[f"- {error}" for error in errors]])
    (root / "RESULTS.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    if errors:
        print("Behavior smoke: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Behavior smoke: PASS ({len(rows)} runs)")
    print(root / "RESULTS.md")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: score-behavior-smoke.py RUN_ROOT")
    raise SystemExit(main(sys.argv[1]))
