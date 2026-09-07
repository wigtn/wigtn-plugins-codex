#!/usr/bin/env python3
"""Parse Codex JSONL events and estimate API-equivalent token cost."""

from __future__ import annotations

from collections import Counter
import argparse
import json
import math
from pathlib import Path


USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)
TOOL_ITEM_TYPES = {
    "command_execution",
    "file_change",
    "mcp_tool_call",
    "web_search",
    "image_generation",
}


def read_events(path: Path) -> dict[str, object]:
    usage = {field: 0 for field in USAGE_FIELDS}
    item_types: Counter[str] = Counter()
    event_count = turn_count = 0
    with path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: invalid JSON event") from error
            event_count += 1
            if event.get("type") == "turn.completed":
                turn_count += 1
                values = event.get("usage")
                if not isinstance(values, dict):
                    raise ValueError(f"{path}:{line_number}: missing usage object")
                for field in USAGE_FIELDS:
                    value = values.get(field)
                    if value is None and field not in {"input_tokens", "output_tokens"}:
                        usage[field] = None
                        continue
                    if type(value) is not int or value < 0:
                        raise ValueError(f"{path}:{line_number}: invalid/missing {field}")
                    if usage[field] is not None:
                        usage[field] += value
                cached = values.get("cached_input_tokens")
                written = values.get("cache_write_input_tokens")
                reasoning = values.get("reasoning_output_tokens")
                if (reasoning is not None and reasoning > values["output_tokens"]
                        or cached is not None and cached > values["input_tokens"]
                        or written is not None and written > values["input_tokens"]
                        or cached is not None and written is not None
                        and cached + written > values["input_tokens"]):
                    raise ValueError(f"{path}:{line_number}: inconsistent usage breakdown")
            if event.get("type") == "item.completed":
                item_type = str((event.get("item") or {}).get("type", "unknown"))
                item_types[item_type] += 1
    if turn_count == 0:
        raise ValueError(f"{path}: missing turn.completed usage event")
    usage["visible_output_tokens"] = (
        usage["output_tokens"] - usage["reasoning_output_tokens"]
        if usage["reasoning_output_tokens"] is not None else None
    )
    usage["uncached_input_tokens"] = (
        usage["input_tokens"] - usage["cached_input_tokens"] - usage["cache_write_input_tokens"]
        if usage["cached_input_tokens"] is not None and usage["cache_write_input_tokens"] is not None
        else None
    )
    usage["turns"] = turn_count
    usage["events"] = event_count
    usage["tool_items"] = sum(
        count for item_type, count in item_types.items() if item_type in TOOL_ITEM_TYPES
    )
    usage["item_types"] = dict(sorted(item_types.items()))
    return usage


def api_equivalent_cost(
    usage: dict[str, object],
    *,
    input_per_million: float,
    cached_input_per_million: float,
    cache_write_per_million: float,
    output_per_million: float,
) -> float | None:
    # A rate table cannot supply telemetry that the service did not report.
    if any(usage.get(field) is None for field in (
        "uncached_input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens"
    )):
        return None
    return (
        int(usage["uncached_input_tokens"]) * input_per_million
        + int(usage["cached_input_tokens"]) * cached_input_per_million
        + int(usage["cache_write_input_tokens"]) * cache_write_per_million
        + int(usage["output_tokens"]) * output_per_million
    ) / 1_000_000


def cold_api_equivalent_cost(
    usage: dict[str, object], *, input_per_million: float, output_per_million: float
) -> float:
    """Price all input as uncached to compare runs independent of cache order."""
    return (
        int(usage["input_tokens"]) * input_per_million
        + int(usage["output_tokens"]) * output_per_million
    ) / 1_000_000


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("events", type=Path)
    parser.add_argument("--input-per-million", type=float)
    parser.add_argument("--cached-input-per-million", type=float)
    parser.add_argument("--cache-write-per-million", type=float)
    parser.add_argument("--output-per-million", type=float)
    args = parser.parse_args()
    rates = {key: getattr(args, key) for key in (
        "input_per_million", "cached_input_per_million",
        "cache_write_per_million", "output_per_million"
    )}
    priced = all(value is not None for value in rates.values())
    if any(value is not None for value in rates.values()) and not priced:
        parser.error("provide all four rates or none")
    if priced and any(not math.isfinite(value) or value < 0 for value in rates.values()):
        parser.error("rates must be finite and nonnegative")
    usage = read_events(args.events)
    usage["rates_usd_per_million"] = rates if priced else None
    usage["api_equivalent_usd"] = api_equivalent_cost(usage, **rates) if priced else None
    usage["cold_api_equivalent_usd"] = cold_api_equivalent_cost(
        usage, input_per_million=args.input_per_million,
        output_per_million=args.output_per_million,
    ) if priced else None
    print(json.dumps(usage, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
