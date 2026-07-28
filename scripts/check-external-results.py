#!/usr/bin/env python3
"""Validate the frozen external paired-result packet and summary arithmetic."""

from pathlib import Path
import json
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
RESULTS = (
    ROOT
    / "tests"
    / "external"
    / "swe-bench-verified"
    / "results-2026-07-28.json"
)


def close(actual: float, expected: float, tolerance: float = 0.11) -> bool:
    return abs(actual - expected) <= tolerance


def main() -> int:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    runs = data["runs"]
    failures = []
    if len(runs) != 8:
        failures.append(f"expected 8 confirmatory runs, found {len(runs)}")
    keys = {(run["task"], run["arm"], run["trial"]) for run in runs}
    if len(keys) != len(runs):
        failures.append("duplicate task/arm/trial key")
    if not all(run["official_resolved"] for run in runs):
        failures.append("all recorded confirmatory runs must be officially resolved")
    arms = {
        arm: [run for run in runs if run["arm"] == arm]
        for arm in ("bare", "plugin")
    }
    for arm, selected in arms.items():
        if len(selected) != 4:
            failures.append(f"{arm}: expected 4 runs, found {len(selected)}")
    summary = data["paired_summary"]["overall_median"]
    fields = {
        "wall_seconds": ("bare_wall_seconds", "plugin_wall_seconds", "wall_overhead_percent"),
        "output_tokens": ("bare_output_tokens", "plugin_output_tokens", "output_overhead_percent"),
        "commands": ("bare_commands", "plugin_commands", "command_overhead_percent"),
    }
    for source, (bare_key, plugin_key, overhead_key) in fields.items():
        bare = statistics.median(run[source] for run in arms["bare"])
        plugin = statistics.median(run[source] for run in arms["plugin"])
        overhead = (plugin / bare - 1) * 100
        if not close(bare, summary[bare_key]):
            failures.append(f"{bare_key}: recorded {summary[bare_key]}, computed {bare}")
        if not close(plugin, summary[plugin_key]):
            failures.append(f"{plugin_key}: recorded {summary[plugin_key]}, computed {plugin}")
        if not close(overhead, summary[overhead_key]):
            failures.append(
                f"{overhead_key}: recorded {summary[overhead_key]}, computed {overhead}"
            )
    post = data["post_reform_forward_test"]
    if post["wall_excluded_reason"] == "":
        failures.append("post-reform wall-time exclusion needs a reason")
    replication = data["gpt_5_5_exploratory_replication"]
    replication_runs = replication["runs"]
    if replication["model"] != "gpt-5.5":
        failures.append("exploratory replication must identify model gpt-5.5")
    if len(replication_runs) != 2:
        failures.append(
            f"expected 2 exploratory replication runs, found {len(replication_runs)}"
        )
    if {run["arm"] for run in replication_runs} != {"bare", "plugin"}:
        failures.append("exploratory replication must contain bare and plugin arms")
    if not all(run["official_resolved"] for run in replication_runs):
        failures.append("all exploratory replication runs must be officially resolved")
    replication_by_arm = {run["arm"]: run for run in replication_runs}
    if set(replication_by_arm) == {"bare", "plugin"}:
        for field, recorded in replication["observed_delta_percent"].items():
            bare_value = replication_by_arm["bare"][field]
            plugin_value = replication_by_arm["plugin"][field]
            computed = (plugin_value / bare_value - 1) * 100
            if not close(computed, recorded):
                failures.append(
                    f"gpt-5.5 {field} delta: recorded {recorded}, computed {computed}"
                )
    if failures:
        print("External paired results: FAIL")
        print("\n".join(failures))
        return 1
    print(
        "External paired results: PASS "
        "(8 confirmatory runs, 4 pairs, 2 exploratory replication runs)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
