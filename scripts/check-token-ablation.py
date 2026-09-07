#!/usr/bin/env python3
"""Exercise positive and negative token-ablation scorer paths."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCORER = ROOT / "scripts/score-token-ablation.py"


def write_run(
    root: Path,
    arm: str,
    case: str,
    *,
    input_tokens: int,
    tool_items: int,
    output: str,
) -> None:
    stem = root / "runs" / arm / f"{case}.1"
    stem.parent.mkdir(parents=True, exist_ok=True)
    Path(f"{stem}.meta.json").write_text(
        json.dumps(
            {
                "arm": arm,
                "case": case,
                "repeat": 1,
                "exit_code": 0,
                "duration_seconds": 1,
            }
        )
        + "\n"
    )
    Path(f"{stem}.out.md").write_text(output)
    events = [
        *[
            {"type": "item.completed", "item": {"type": "command_execution"}}
            for _ in range(tool_items)
        ],
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": input_tokens,
                "cached_input_tokens": 0,
                "cache_write_input_tokens": 0,
                "output_tokens": 100,
                "reasoning_output_tokens": 20,
            },
        },
    ]
    Path(f"{stem}.events.jsonl").write_text(
        "\n".join(json.dumps(event) for event in events) + "\n"
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="wigtn-token-ablation-") as temporary:
        root = Path(temporary)
        (root / "SCHEDULE.tsv").write_text(
            "pair_id\torder\tarm\tcase\tprompt\trepeat\n"
            "prd-create.1\t1\tbaseline\tprd-create\tprd.txt\t1\n"
            "prd-create.1\t2\tcandidate\tprd-create\tprd.txt\t1\n"
            "acceptance-uncertain.1\t3\tbaseline\tacceptance-uncertain\tacceptance.txt\t1\n"
            "acceptance-uncertain.1\t4\tcandidate\tacceptance-uncertain\tacceptance.txt\t1\n"
        )
        prd = "<!-- wigtn-prd-profile: compact -->\nFR-1\nAC-1\n"
        write_run(root, "baseline", "prd-create", input_tokens=40000, tool_items=2, output=prd)
        write_run(root, "candidate", "prd-create", input_tokens=26000, tool_items=1, output=prd)
        write_run(root, "baseline", "acceptance-uncertain", input_tokens=12000, tool_items=0, output="unknown\n")
        candidate = root / "runs/candidate/acceptance-uncertain.1.out.md"
        write_run(root, "candidate", "acceptance-uncertain", input_tokens=12000, tool_items=0, output="not-verifiable\n")
        passed = subprocess.run(
            [sys.executable, "-B", str(SCORER), str(root)], text=True, capture_output=True
        )
        if passed.returncode:
            raise AssertionError(passed.stdout + passed.stderr)
        candidate.write_text("Not Verifiable\n")
        failed = subprocess.run(
            [sys.executable, "-B", str(SCORER), str(root)], text=True, capture_output=True
        )
        if failed.returncode != 1:
            raise AssertionError("localized status did not fail the ablation scorer")
    print("Token ablation scorer: PASS (positive + canonical regression)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
