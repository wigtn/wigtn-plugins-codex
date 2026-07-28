#!/usr/bin/env python3
"""Score anonymous PRD panels from two model judges."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import re
import statistics
import sys


ARMS = ("bare", "placebo4", "core4", "full8")
DIMS = (
    "completeness",
    "implementability",
    "decision_hygiene",
    "traceability",
    "concision",
)


def labels(panel: str) -> dict[str, str]:
    values = list(ARMS)
    random.Random(hashlib.sha256(panel.encode()).digest()).shuffle(values)
    return {chr(65 + index): arm for index, arm in enumerate(values)}


def parse(path: Path) -> dict:
    text = path.read_text(errors="ignore")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return json.loads(match.group())


def main(root_arg: str) -> int:
    root = Path(root_arg)
    rows = []
    for judge in ("J56", "J55"):
        for path in sorted((root / "runs" / judge).glob("*.json")):
            if path.name.endswith(".meta.json"):
                continue
            result = parse(path)
            panel = result["panel"]
            panel_map = labels(panel)
            seen = set()
            ranking = result["ranking_best_to_worst"]
            for candidate in result["candidates"]:
                label = candidate["label"]
                scores = [int(candidate[dim]) for dim in DIMS]
                if label in seen or label not in panel_map or any(
                    score < 0 or score > 4 for score in scores
                ):
                    raise ValueError(f"invalid judge record: {path}")
                seen.add(label)
                rows.append(
                    {
                        "judge": judge,
                        "panel": panel,
                        "source_model": panel.split("-")[0],
                        "arm": panel_map[label],
                        "scores": scores,
                        "total": sum(scores),
                        "omissions": len(candidate.get("material_omissions", [])),
                        "fabrications": len(candidate.get("fabricated_policies", [])),
                        "rank": ranking.index(label) + 1,
                    }
                )
            if seen != set(panel_map):
                raise ValueError(f"missing labels: {path}")

    out = [
        "# Blind PRD screening",
        "",
        "> Model judges are a reproducible screening layer, not human sign-off.",
        "",
        "| Arm | quality /100 | completeness | implementability | decision hygiene | traceability | concision | omissions | fabrications |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ARMS:
        selected = [row for row in rows if row["arm"] == arm]
        means = [
            statistics.mean(row["scores"][index] for row in selected)
            for index in range(len(DIMS))
        ]
        out.append(
            f"| {arm} | {statistics.mean(row['total'] for row in selected) * 5:.1f} | "
            + " | ".join(f"{value:.2f}" for value in means)
            + f" | {sum(row['omissions'] for row in selected)}"
            + f" | {sum(row['fabrications'] for row in selected)} |"
        )

    bare = {
        (row["judge"], row["panel"]): row["total"]
        for row in rows
        if row["arm"] == "bare"
    }
    out.extend(
        [
            "",
            "## Paired comparison with bare",
            "",
            "| Arm | mean score delta /100 | win | tie | loss |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for arm in ARMS[1:]:
        selected = [row for row in rows if row["arm"] == arm]
        deltas = [
            (row["total"] - bare[(row["judge"], row["panel"])]) * 5
            for row in selected
        ]
        out.append(
            f"| {arm} | {statistics.mean(deltas):+.1f} | "
            f"{sum(value > 0 for value in deltas)} | "
            f"{sum(value == 0 for value in deltas)} | "
            f"{sum(value < 0 for value in deltas)} |"
        )
    top_agreement = 0
    pair_agree = 0
    pair_total = 0
    indexed = {
        (row["judge"], row["panel"], row["arm"]): row for row in rows
    }
    panels = sorted({row["panel"] for row in rows})
    for panel in panels:
        rank = {
            judge: {
                arm: indexed[(judge, panel, arm)]["rank"] for arm in ARMS
            }
            for judge in ("J56", "J55")
        }
        top_agreement += min(rank["J56"], key=rank["J56"].get) == min(
            rank["J55"], key=rank["J55"].get
        )
        for index, left in enumerate(ARMS):
            for right in ARMS[index + 1 :]:
                pair_agree += (
                    rank["J56"][left] < rank["J56"][right]
                ) == (rank["J55"][left] < rank["J55"][right])
                pair_total += 1
    out.extend(
        [
            "",
            "## Judge agreement",
            "",
            f"- Same top candidate: {top_agreement}/{len(panels)} panels",
            f"- Same pairwise order: {pair_agree}/{pair_total} candidate pairs",
            "",
            "Each arm has eight judge-panel observations across two source models "
            "and two repeats. These descriptive results are not human validation.",
        ]
    )
    (root / "RESULTS.md").write_text("\n".join(out) + "\n")
    print(root / "RESULTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
