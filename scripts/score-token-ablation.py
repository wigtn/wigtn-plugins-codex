#!/usr/bin/env python3
"""Score a focused baseline-versus-candidate token-efficiency ablation."""

from __future__ import annotations

import json
from pathlib import Path
import re
import statistics
import sys
import csv

from codex_usage import api_equivalent_cost, cold_api_equivalent_cost, read_events


RATES = {
    "input_per_million": 4.0,
    "cached_input_per_million": 0.4,
    "cache_write_per_million": 5.0,
    "output_per_million": 20.0,
}


def median(rows: list[dict[str, object]], field: str) -> float:
    return statistics.median(float(row[field]) for row in rows)


def main(root_arg: str) -> int:
    root = Path(root_arg)
    rows: list[dict[str, object]] = []
    failures: list[str] = []
    schedule_path = root / "SCHEDULE.tsv"
    expected: set[tuple[str, str, int]] = set()
    if not schedule_path.is_file():
        failures.append("SCHEDULE.tsv is missing")
    else:
        with schedule_path.open(encoding="utf-8", newline="") as handle:
            for item in csv.DictReader(handle, delimiter="\t"):
                key = (item["arm"], item["case"], int(item["repeat"]))
                if key in expected:
                    failures.append(f"duplicate schedule row: {key}")
                expected.add(key)
    for meta_path in sorted((root / "runs").glob("*/*.meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        stem = meta_path.name.removesuffix(".meta.json")
        output = meta_path.with_name(f"{stem}.out.md").read_text(
            encoding="utf-8", errors="replace"
        )
        usage = read_events(meta_path.with_name(f"{stem}.events.jsonl"))
        contract = True
        if meta["case"] == "prd-create":
            contract = all(
                marker in output
                for marker in ("wigtn-prd-profile: compact", "FR-", "AC-")
            )
        row = {
            **meta,
            **usage,
            "contract": contract,
            "exact_status": bool(re.search(r"\bnot-verifiable\b", output, re.I)),
            "api_equivalent_usd": api_equivalent_cost(usage, **RATES),
            "cold_api_equivalent_usd": cold_api_equivalent_cost(
                usage,
                input_per_million=RATES["input_per_million"],
                output_per_million=RATES["output_per_million"],
            ),
        }
        rows.append(row)
        if meta["exit_code"] != 0 or not output.strip():
            failures.append(
                f"{meta['arm']}/{meta['case']}.{meta['repeat']}: unhealthy execution"
            )

    selected: dict[tuple[str, str], list[dict[str, object]]] = {}
    observed = {
        (str(row["arm"]), str(row["case"]), int(row["repeat"])) for row in rows
    }
    for missing in sorted(expected - observed):
        failures.append(f"scheduled run missing: {missing}")
    for extra in sorted(observed - expected):
        failures.append(f"run absent from schedule: {extra}")
    for row in rows:
        selected.setdefault((str(row["arm"]), str(row["case"])), []).append(row)
    for key in (
        ("baseline", "prd-create"),
        ("baseline", "acceptance-uncertain"),
        ("candidate", "prd-create"),
        ("candidate", "acceptance-uncertain"),
    ):
        if not selected.get(key):
            failures.append(f"missing cell: {key[0]}/{key[1]}")

    candidate_prd = selected.get(("candidate", "prd-create"), [])
    baseline_prd = selected.get(("baseline", "prd-create"), [])
    candidate_acceptance = selected.get(("candidate", "acceptance-uncertain"), [])
    if candidate_prd and not all(bool(row["contract"]) for row in candidate_prd):
        failures.append("candidate PRD contract regression")
    if candidate_acceptance and not all(
        bool(row["exact_status"]) for row in candidate_acceptance
    ):
        failures.append("candidate acceptance omitted exact not-verifiable")
    if candidate_acceptance and any(
        int(row["tool_items"]) for row in candidate_acceptance
    ):
        failures.append("candidate acceptance executed a prohibited tool")
    if candidate_prd and baseline_prd:
        if median(candidate_prd, "tool_items") >= median(baseline_prd, "tool_items"):
            failures.append("candidate PRD did not reduce median tool items")
        if median(candidate_prd, "input_tokens") >= median(baseline_prd, "input_tokens"):
            failures.append("candidate PRD did not reduce median input tokens")

    report = [
        "# Token ablation results",
        "",
        "| Arm | Case | Repeat | Contract | Exact status | Input | Cached | Output | Reasoning | Tools | Cold USD |",
        "|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        report.append(
            f"| {row['arm']} | {row['case']} | {row['repeat']} | "
            f"{'yes' if row['contract'] else 'no'} | "
            f"{'yes' if row['exact_status'] else 'no'} | {row['input_tokens']} | "
            f"{row['cached_input_tokens']} | {row['output_tokens']} | "
            f"{row['reasoning_output_tokens']} | {row['tool_items']} | "
            f"${row['cold_api_equivalent_usd']:.6f} |"
        )
    report.extend(
        [
            "",
            "## Median comparison",
            "",
            "| Case | Arm | Input | Output | Tools | Cold USD |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for case in ("prd-create", "acceptance-uncertain"):
        for arm in ("baseline", "candidate"):
            cell = selected.get((arm, case), [])
            if cell:
                report.append(
                    f"| {case} | {arm} | {median(cell, 'input_tokens'):.1f} | "
                    f"{median(cell, 'output_tokens'):.1f} | "
                    f"{median(cell, 'tool_items'):.1f} | "
                    f"${median(cell, 'cold_api_equivalent_usd'):.6f} |"
                )
    if failures:
        report.extend(["", "## Failures", "", *[f"- {item}" for item in failures]])
    (root / "ABLATION-RESULTS.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    (root / "ABLATION-RESULTS.json").write_text(
        json.dumps({"passed": not failures, "failures": failures, "runs": rows}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    if failures:
        print("Token ablation: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Token ablation: PASS ({len(rows)} runs)")
    print(root / "ABLATION-RESULTS.md")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: score-token-ablation.py RUN_ROOT")
    raise SystemExit(main(sys.argv[1]))
