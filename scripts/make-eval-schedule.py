#!/usr/bin/env python3
"""Create a deterministic, counterbalanced evaluation schedule."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import sys


def key(seed: str, value: str) -> str:
    return sha256(f"{seed}\0{value}".encode("utf-8")).hexdigest()


def load_cases(path: Path) -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line or line.startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) != 2 or not all(column.strip() for column in columns):
            raise ValueError(f"{path}:{line_number}: expected CASE<TAB>PROMPT")
        case_id, prompt = columns
        if case_id in seen:
            raise ValueError(f"{path}:{line_number}: duplicate case {case_id}")
        seen.add(case_id)
        cases.append((case_id, prompt))
    if not cases:
        raise ValueError(f"{path}: no cases")
    return cases


def schedule(
    cases: list[tuple[str, str]],
    arms: list[str],
    repeat: int,
    seed: str,
) -> list[tuple[str, int, str, str, str, int]]:
    if repeat < 1:
        raise ValueError("repeat must be positive")
    if len(arms) < 2 or len(arms) != len(set(arms)):
        raise ValueError("at least two unique arms are required")
    pairs: list[tuple[str, str, int]] = []
    prompts = dict(cases)
    for case_id, _ in cases:
        for repetition in range(1, repeat + 1):
            pair_id = f"{case_id}.{repetition}"
            pairs.append((pair_id, case_id, repetition))
    pairs.sort(key=lambda item: key(seed, f"pair:{item[0]}"))

    rows: list[tuple[str, int, str, str, str, int]] = []
    global_order = 0
    arm_count = len(arms)
    for pair_index, (pair_id, case_id, repetition) in enumerate(pairs):
        block = pair_index // arm_count
        within_block = pair_index % arm_count
        base_arms = sorted(
            arms, key=lambda arm: key(seed, f"block:{block}:arm:{arm}")
        )
        ordered_arms = (
            base_arms[within_block:] + base_arms[:within_block]
        )
        for within_pair, arm in enumerate(ordered_arms, start=1):
            global_order += 1
            rows.append(
                (
                    pair_id,
                    global_order,
                    arm,
                    case_id,
                    prompts[case_id],
                    repetition,
                )
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path)
    parser.add_argument("--arms", nargs="+", required=True)
    parser.add_argument("--repeat", type=int, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        rows = schedule(
            load_cases(args.cases), args.arms, args.repeat, args.seed
        )
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2
    content = "pair_id\torder\tarm\tcase\tprompt\trepeat\n" + "\n".join(
        "\t".join(str(value) for value in row) for row in rows
    ) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
