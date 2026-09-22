#!/usr/bin/env python3
"""Validate core and placebo ablation marketplace construction."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build-ablation-marketplace.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="wigtn-ablation-builder-") as tmp:
        root = Path(tmp)
        records = {}
        expected_counts = {
            "core4": 4,
            "placebo4": 4,
            "full8": 8,
            "full9": 9,
        }
        for variant, expected_count in expected_counts.items():
            destination = root / variant
            completed = subprocess.run(
                [sys.executable, str(BUILDER), variant, str(destination)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode:
                raise AssertionError(completed.stdout + completed.stderr)
            record = json.loads(
                (destination / "ABLATION.json").read_text(encoding="utf-8")
            )
            if len(record["skills"]) != expected_count:
                raise AssertionError(
                    f"{variant}: expected {expected_count} skills"
                )
            records[variant] = record

        historical = {
            "product-spec", "acceptance-verifier", "verified-delivery",
            "release-readiness", "screen-spec", "design-direction",
            "handdrawn-diagram", "wigtn-presentation", "work-planner",
        }
        for variant, expected in (("full9", historical), ("full8", historical - {"work-planner"})):
            if set(records[variant]["skills"]) != expected:
                raise AssertionError(f"{variant}: historical inventory changed")

        core_chars = records["core4"]["description_characters"]
        placebo_chars = records["placebo4"]["description_characters"]
        if core_chars != placebo_chars:
            raise AssertionError(
                f"placebo metadata mismatch: core={core_chars}, "
                f"placebo={placebo_chars}"
            )
        if "work-planner" in records["full8"]["skills"]:
            raise AssertionError("full8 unexpectedly contains work-planner")
        if "work-planner" not in records["full9"]["skills"]:
            raise AssertionError("full9 is missing work-planner")
    print("Ablation builder: PASS (core4/placebo4/full8/full9)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
