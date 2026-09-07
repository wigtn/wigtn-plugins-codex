#!/usr/bin/env python3
"""Summarize detailed Codex usage without treating cost as quality."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from codex_usage import api_equivalent_cost, cold_api_equivalent_cost, read_events


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--input-per-million", type=float)
    parser.add_argument("--cached-input-per-million", type=float)
    parser.add_argument("--cache-write-per-million", type=float)
    parser.add_argument("--output-per-million", type=float)
    args = parser.parse_args()
    rates = {
        "input_per_million": args.input_per_million,
        "cached_input_per_million": args.cached_input_per_million,
        "cache_write_per_million": args.cache_write_per_million,
        "output_per_million": args.output_per_million,
    }
    priced = all(value is not None for value in rates.values())
    if any(value is not None for value in rates.values()) and not priced:
        parser.error("provide all four rates or none")
    if priced and any(not math.isfinite(value) or value < 0 for value in rates.values()):
        parser.error("rates must be finite and nonnegative")
    rows = []
    for events_path in sorted((args.run_root / "runs").glob("*/*.events.jsonl")):
        stem = events_path.name.removesuffix(".events.jsonl")
        arm = events_path.parent.name
        case, repeat_text = stem.rsplit(".", 1)
        usage = read_events(events_path)
        rows.append(
            {
                "arm": arm,
                "case": case,
                "repeat": int(repeat_text),
                **usage,
                "api_equivalent_usd": api_equivalent_cost(usage, **rates) if priced else None,
                "cold_api_equivalent_usd": cold_api_equivalent_cost(
                    usage,
                    input_per_million=args.input_per_million,
                    output_per_million=args.output_per_million,
                ) if priced else None,
            }
        )
    if not rows:
        raise SystemExit("no Codex JSONL event files found")

    arms: dict[str, dict[str, float]] = {}
    for row in rows:
        aggregate = arms.setdefault(
            row["arm"],
            {
                "runs": 0,
                "input_tokens": 0,
                "cached_input_tokens": 0,
                "cache_write_input_tokens": 0,
                "output_tokens": 0,
                "reasoning_output_tokens": 0,
                "visible_output_tokens": 0,
                "tool_items": 0,
                "api_equivalent_usd": 0.0,
                "cold_api_equivalent_usd": 0.0,
            },
        )
        aggregate["runs"] += 1
        for field in aggregate:
            if field != "runs":
                if row[field] is None:
                    aggregate[field] = None
                elif aggregate[field] is not None:
                    aggregate[field] += row[field]

    document = {"schema_version": "1.0", "rates_usd_per_million": rates if priced else None, "runs": rows, "arms": arms}
    (args.run_root / "TOKEN-EFFICIENCY.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    def money(value):
        return "unknown/unpriced" if value is None else f"${value:.6f}"

    def count(value):
        return "unknown" if value is None else str(int(value))

    report = [
        "# Token efficiency",
        "",
        "API-equivalent cost is a comparison metric using the recorded rates; it is not a ChatGPT subscription charge.",
        "",
        "| Arm | Case | Repeat | Input | Cached | Cache write | Output | Reasoning | Visible | Tool items | Estimated USD | Cold USD |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        report.append(
            f"| {row['arm']} | {row['case']} | {row['repeat']} | "
            f"{count(row['input_tokens'])} | {count(row['cached_input_tokens'])} | "
            f"{count(row['cache_write_input_tokens'])} | {count(row['output_tokens'])} | "
            f"{count(row['reasoning_output_tokens'])} | {count(row['visible_output_tokens'])} | "
            f"{count(row['tool_items'])} | {money(row['api_equivalent_usd'])} | "
            f"{money(row['cold_api_equivalent_usd'])} |"
        )
    report.extend(
        [
            "",
            "## Arm totals",
            "",
            "| Arm | Runs | Input | Cached | Output | Reasoning | Tool items | Estimated USD | Cold USD |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for arm, row in sorted(arms.items()):
        report.append(
            f"| {arm} | {int(row['runs'])} | {count(row['input_tokens'])} | "
            f"{count(row['cached_input_tokens'])} | {count(row['output_tokens'])} | "
            f"{count(row['reasoning_output_tokens'])} | {count(row['tool_items'])} | "
            f"{money(row['api_equivalent_usd'])} | "
            f"{money(row['cold_api_equivalent_usd'])} |"
        )
    (args.run_root / "TOKEN-EFFICIENCY.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print(args.run_root / "TOKEN-EFFICIENCY.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
