#!/usr/bin/env python3
"""Validate the frozen FeatureBench pilot result and its claim boundary."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "tests/external/featurebench/results-2026-07-28.json"


def fail(message: str) -> None:
    raise SystemExit(f"featurebench-results: {message}")


def main() -> None:
    data = json.loads(RESULTS.read_text())
    pairs = data["primary_pairs"]
    summary = data["summary"]

    if len(pairs) != 4:
        fail("expected four frozen primary pairs")
    if len({pair["instance"] for pair in pairs}) != 4:
        fail("primary instances must be unique")

    raw_positive = sum(pair["raw_outcome"] == "positive-discordant" for pair in pairs)
    raw_negative = sum(pair["raw_outcome"] == "negative-discordant" for pair in pairs)
    eligible = [
        pair
        for pair in pairs
        if pair["integrity"] in {"eligible", "eligible-with-host-cache-risk"}
    ]
    eligible_positive = sum(
        pair["adjudicated_outcome"] == "positive-discordant" for pair in eligible
    )
    eligible_negative = sum(
        pair["adjudicated_outcome"] == "negative-discordant" for pair in eligible
    )

    expected = {
        "raw_primary_positive_discordant": raw_positive,
        "raw_primary_negative_discordant": raw_negative,
        "integrity_eligible_primary_pairs": len(eligible),
        "eligible_positive_discordant": eligible_positive,
        "eligible_negative_discordant": eligible_negative,
    }
    for key, value in expected.items():
        if summary[key] != value:
            fail(f"{key} is {summary[key]!r}; recomputed {value!r}")

    leaked = [pair for pair in pairs if pair["integrity"] == "invalid-reference-leakage"]
    if len(leaked) != 1 or not leaked[0].get("integrity_evidence"):
        fail("the invalid reference-leakage adjudication must retain evidence")
    if data["reverse_order_repeat"]["replicates_primary_positive"] is not False:
        fail("reverse-order repeat must record non-replication")
    if summary["replicated_positive_tasks"] != 0:
        fail("pilot has no replicated positive task")
    if summary["general_quality_lift_supported"] is not False:
        fail("pilot cannot support a general quality-lift claim")

    print("featurebench-results: ok (4 pairs, 0 eligible positive, 0 replicated positive)")


if __name__ == "__main__":
    main()
