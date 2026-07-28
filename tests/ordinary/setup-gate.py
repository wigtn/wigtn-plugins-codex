#!/usr/bin/env python3
"""Create isolated ordinary-coding repositories for every arm and repeat."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "ordinary"))

from task_bank import TASKS  # noqa: E402


def write_files(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--arms", nargs="+", required=True)
    parser.add_argument("--repeat", type=int, required=True)
    args = parser.parse_args()
    if args.repeat < 1 or len(args.arms) != len(set(args.arms)):
        raise SystemExit("invalid arms or repeat")

    prompts = args.run_root / "prompts"
    prompts.mkdir(parents=True)
    baseline: dict[str, dict[str, str]] = {}
    cases = []
    for task in TASKS:
        (prompts / f"{task['id']}.txt").write_text(
            task["prompt"]
            + "\n\nWork only inside this repository. Do not create product "
            "requirements, lifecycle state, diagrams, release artifacts, commits, "
            "or remote actions.\n",
            encoding="utf-8",
        )
        cases.append((task["id"], f"prompts/{task['id']}.txt"))
        for arm in args.arms:
            for repetition in range(1, args.repeat + 1):
                work = (
                    args.run_root
                    / "work"
                    / arm
                    / task["id"]
                    / str(repetition)
                )
                write_files(work, task["files"])
                (work / "USER-DRAFT.txt").write_text(
                    f"sentinel:{arm}:{task['id']}:{repetition}\n",
                    encoding="utf-8",
                )
                baseline_key = f"{arm}/{task['id']}/{repetition}"
                baseline[baseline_key] = {
                    path.relative_to(work).as_posix(): digest(path)
                    for path in sorted(work.rglob("*"))
                    if path.is_file()
                }
    (args.run_root / "CASES.tsv").write_text(
        "\n".join(f"{case}\t{prompt}" for case, prompt in cases) + "\n",
        encoding="utf-8",
    )
    (args.run_root / "BASELINE.json").write_text(
        json.dumps(baseline, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Ordinary gate setup: {len(TASKS)} tasks × "
        f"{len(args.arms)} arms × {args.repeat}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
