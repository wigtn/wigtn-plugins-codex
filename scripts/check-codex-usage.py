#!/usr/bin/env python3
"""Regression checks for Codex JSONL usage parsing and cost math."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import subprocess
import sys

from codex_usage import api_equivalent_cost, cold_api_equivalent_cost, read_events


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="wigtn-codex-usage-") as temporary:
        path = Path(temporary) / "events.jsonl"
        events = [
            {"type": "item.completed", "item": {"type": "command_execution"}},
            {"type": "item.completed", "item": {"type": "agent_message"}},
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 1000,
                    "cached_input_tokens": 200,
                    "cache_write_input_tokens": 100,
                    "output_tokens": 300,
                    "reasoning_output_tokens": 120,
                },
            },
        ]
        path.write_text("\n".join(json.dumps(event) for event in events) + "\n")
        usage = read_events(path)
        assert usage["uncached_input_tokens"] == 700
        assert usage["visible_output_tokens"] == 180
        assert usage["tool_items"] == 1
        cost = api_equivalent_cost(
            usage,
            input_per_million=4.0,
            cached_input_per_million=0.4,
            cache_write_per_million=5.0,
            output_per_million=20.0,
        )
        assert abs(cost - 0.00938) < 1e-12
        cold_cost = cold_api_equivalent_cost(
            usage, input_per_million=4.0, output_per_million=20.0
        )
        assert abs(cold_cost - 0.01) < 1e-12
    with tempfile.TemporaryDirectory(prefix="wigtn-explicit-pricing-") as temporary:
        root = Path(temporary)
        events = root / "runs" / "candidate" / "prd.1.events.jsonl"
        events.parent.mkdir(parents=True)
        events.write_text(json.dumps({"type": "turn.completed", "usage": {
            "input_tokens": 1000, "output_tokens": 100}}) + "\n")
        summary = Path(__file__).with_name("summarize-token-efficiency.py")
        full = ["--input-per-million", "4", "--cached-input-per-million", "0.4",
                "--cache-write-per-million", "5", "--output-per-million", "20"]
        for flags, expected in [([], 0), (["--input-per-million", "4"], 2),
                                (full, 0), (full[:-1] + ["nan"], 2)]:
            result = subprocess.run([sys.executable, "-B", str(summary), str(root), *flags],
                                    capture_output=True, text=True)
            assert result.returncode == expected, result.stdout + result.stderr
            if not flags:
                data = json.loads((root / "TOKEN-EFFICIENCY.json").read_text())
                assert data["rates_usd_per_million"] is None
                assert data["runs"][0]["api_equivalent_usd"] is None
    print("Explicit pricing: PASS (unpriced/partial/explicit/nonfinite)")
    print("Codex usage: PASS (JSONL fields + API-equivalent cost)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
