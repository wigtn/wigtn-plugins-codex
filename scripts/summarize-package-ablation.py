#!/usr/bin/env python3
"""Summarize package-ablation outcomes without using a model judge."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRD_VALIDATOR = (
    ROOT
    / "plugins"
    / "wigtn-plugins-with-codex"
    / "skills"
    / "product-spec"
    / "scripts"
    / "validate-prd.py"
)


def total_tokens(path: Path) -> int | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    matches = re.findall(r"tokens used\s*\n([\d,]+)", text, re.I)
    return int(matches[-1].replace(",", "")) if matches else None


def score_prd(path: Path) -> tuple[bool, str]:
    completed = subprocess.run(
        [sys.executable, str(PRD_VALIDATOR), str(path), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return False, "scorer-error"
    return bool(result.get("valid")), str(result.get("profile", "unknown"))


def score_ordinary(text: str) -> tuple[bool, str]:
    copy_fix = bool(
        re.search(r"\[\s*\.\.\.", text)
        or re.search(r"\.slice\(\)\s*\.sort", text)
        or re.search(r"\.toSorted\(", text)
    )
    regression = bool(
        re.search(
            r"expect\(\s*(?:input|original)\s*\)\s*\.toEqual",
            text,
            re.I,
        )
    )
    heavy_workflow = bool(
        re.search(r"wigtn-prd-profile", text, re.I)
        or re.search(
            r"^#{1,4}\s+.*(?:PRD|screen spec|화면\s*정의|release plan)",
            text,
            re.I | re.M,
        )
    )
    detail = "heavy-trigger" if heavy_workflow else "lean"
    return copy_fix and regression and not heavy_workflow, detail


def format_number(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.1f}"
    return f"{int(value):,}"


def load_rows(run_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for meta_path in sorted((run_root / "runs").glob("*/*.meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        stem = meta_path.name.removesuffix(".meta.json")
        output_path = meta_path.with_name(f"{stem}.out.md")
        log_path = meta_path.with_name(f"{stem}.log")
        output = output_path.read_text(encoding="utf-8", errors="ignore")
        if meta["case"] == "prd-create":
            outcome, detail = score_prd(output_path)
        elif meta["case"] == "ordinary-coding":
            outcome, detail = score_ordinary(output)
        else:
            outcome, detail = False, "unsupported-case"
        rows.append(
            {
                **meta,
                "run_root": str(run_root),
                "outcome": outcome,
                "detail": detail,
                "tokens": total_tokens(log_path),
                "output_bytes": len(output.encode("utf-8")),
            }
        )
    return rows


def render(rows: list[dict[str, Any]], roots: list[Path]) -> str:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model"], row["arm"], row["case"])].append(row)

    report = [
        "# Package ablation summary",
        "",
        "Deterministic outcomes only: PRDs use the versioned PRD validator; "
        "ordinary coding requires a non-mutating copy fix, a source-array "
        "regression assertion, and no heavy workflow document.",
        "",
        f"Run roots: {', '.join(f'`{root}`' for root in roots)}",
        "",
        "| Model | Arm | Case | Outcome | Profile/detail | Median tokens | "
        "Median bytes | Median duration |",
        "|---|---|---|---:|---|---:|---:|---:|",
    ]
    arm_order = {
        "bare": 0,
        "placebo4": 1,
        "core4": 2,
        "full8": 3,
        "full9": 3,
    }
    case_order = {"prd-create": 0, "ordinary-coding": 1}
    for key in sorted(
        grouped,
        key=lambda item: (
            item[0],
            arm_order.get(item[1], 99),
            case_order.get(item[2], 99),
        ),
    ):
        model, arm, case = key
        items = grouped[key]
        tokens = [item["tokens"] for item in items if item["tokens"] is not None]
        details = sorted({item["detail"] for item in items})
        report.append(
            f"| {model} | {arm} | {case} | "
            f"{sum(bool(item['outcome']) for item in items)}/{len(items)} | "
            f"{', '.join(details)} | "
            f"{format_number(statistics.median(tokens) if tokens else None)} | "
            f"{format_number(statistics.median(item['output_bytes'] for item in items))} | "
            f"{format_number(statistics.median(item['duration_seconds'] for item in items))}s |"
        )
    return "\n".join(report) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = [row for root in args.run_root for row in load_rows(root)]
    if not rows:
        raise SystemExit("no package-ablation metadata found")
    report = render(rows, args.run_root)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(args.output)
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
