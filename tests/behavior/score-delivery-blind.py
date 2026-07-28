#!/usr/bin/env python3
"""Score two anonymous model-judge passes without replacing human review."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import re
import statistics
import sys


ARMS = ("IM-M56-BARE", "IM-M56-ORDINARY", "IM-M56-VERIFIED", "IM-M55-VERIFIED")
DIMS = (
    "completeness",
    "correctness",
    "scope_discipline",
    "maintainability",
    "evidence_quality",
)


def order(task: str) -> list[str]:
    return sorted(
        ARMS,
        key=lambda arm: hashlib.sha256(
            f"wigtn-v03-blind:{task}:{arm}".encode()
        ).hexdigest(),
    )


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
            labels = {
                chr(65 + index): arm
                for index, arm in enumerate(order(result["task"]))
            }
            seen = set()
            for candidate in result["candidates"]:
                label = candidate["label"]
                scores = [int(candidate[dim]) for dim in DIMS]
                if label in seen or label not in labels or any(
                    score < 0 or score > 4 for score in scores
                ):
                    raise ValueError(f"invalid judge record: {path}")
                seen.add(label)
                rows.append(
                    {
                        "judge": judge,
                        "task": result["task"],
                        "arm": labels[label],
                        "scores": scores,
                        "total": sum(scores),
                        "blockers": len(candidate.get("blockers", [])),
                        "high": len(candidate.get("high", [])),
                        "rank": result["ranking_best_to_worst"].index(label) + 1,
                    }
                )
            if seen != set(labels):
                raise ValueError(f"missing labels: {path}")
    out = [
        "# Blind delivery screening",
        "",
        "> Model judges are a reproducible screening layer, not human sign-off.",
        "",
        "| Arm | quality /100 | completeness | correctness | scope | maintainability | evidence | blockers | high |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ARMS:
        selected = [row for row in rows if row["arm"] == arm]
        if not selected:
            raise ValueError(f"no valid judge records for {arm}")
        means = [
            statistics.mean(row["scores"][index] for row in selected)
            for index in range(len(DIMS))
        ]
        quality = statistics.mean(sum(row["scores"]) for row in selected) * 5
        out.append(
            f"| {arm} | {quality:.1f} | "
            + " | ".join(f"{value:.2f}" for value in means)
            + f" | {sum(row['blockers'] for row in selected)} | "
            f"{sum(row['high'] for row in selected)} |"
        )
    out.extend(
        [
            "",
            "## Paired comparison with GPT-5.6 bare",
            "",
            "| Arm | mean score delta /100 | win | tie | loss |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    bare = {
        (row["judge"], row["task"]): row["total"]
        for row in rows
        if row["arm"] == "IM-M56-BARE"
    }
    for arm in ARMS[1:]:
        selected = [row for row in rows if row["arm"] == arm]
        deltas = [
            (row["total"] - bare[(row["judge"], row["task"])]) * 5
            for row in selected
        ]
        out.append(
            f"| {arm} | {statistics.mean(deltas):+.1f} | "
            f"{sum(delta > 0 for delta in deltas)} | "
            f"{sum(delta == 0 for delta in deltas)} | "
            f"{sum(delta < 0 for delta in deltas)} |"
        )
    judge_rows = {
        (row["judge"], row["task"], row["arm"]): row for row in rows
    }
    top_agreement = 0
    pair_agree = 0
    pair_total = 0
    for task in sorted({row["task"] for row in rows}):
        ranks = {
            judge: {
                arm: judge_rows[(judge, task, arm)]["rank"] for arm in ARMS
            }
            for judge in ("J56", "J55")
        }
        if min(ranks["J56"], key=ranks["J56"].get) == min(
            ranks["J55"], key=ranks["J55"].get
        ):
            top_agreement += 1
        for index, left in enumerate(ARMS):
            for right in ARMS[index + 1 :]:
                direction56 = ranks["J56"][left] < ranks["J56"][right]
                direction55 = ranks["J55"][left] < ranks["J55"][right]
                pair_agree += direction56 == direction55
                pair_total += 1
    out.extend(
        [
            "",
            "## Judge agreement",
            "",
            f"- Same top candidate: {top_agreement}/4 tasks",
            f"- Same pairwise order: {pair_agree}/{pair_total} candidate pairs",
            "",
            "The paired sample is eight judge-task observations per arm. These "
            "descriptive deltas are not confidence intervals, and the two model "
            "judges are not independent human reviewers.",
        ]
    )
    (root / "RESULTS.md").write_text("\n".join(out) + "\n")
    print(root / "RESULTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
