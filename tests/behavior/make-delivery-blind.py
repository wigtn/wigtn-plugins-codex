#!/usr/bin/env python3
"""Build identity-free implementation review prompts and a human packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


ARMS = ("IM-M56-BARE", "IM-M56-ORDINARY", "IM-M56-VERIFIED", "IM-M55-VERIFIED")
TASKS = ("expense-approval", "webhook-delivery", "tenant-search", "config-migration")
LABELS = ("A", "B", "C", "D")


def path(stem: Path, suffix: str) -> Path:
    return Path(f"{stem}{suffix}")


def order(task: str) -> list[str]:
    return sorted(
        ARMS,
        key=lambda arm: hashlib.sha256(
            f"wigtn-v03-blind:{task}:{arm}".encode()
        ).hexdigest(),
    )


def base_file(repo: Path, head: str, name: str) -> str:
    return subprocess.run(
        ["git", "show", f"{head}:{name}"],
        cwd=repo,
        text=True,
        capture_output=True,
    ).stdout


def main(root_arg: str, blind_arg: str | None = None) -> int:
    root = Path(root_arg)
    blind = Path(blind_arg) if blind_arg else root / "blind"
    prompts = blind / "prompts"
    prompts.mkdir(parents=True, exist_ok=True)
    human = []
    for task in TASKS:
        first = root / "implement" / ARMS[0] / task
        setup = json.loads(path(first, ".setup.json").read_text())
        repo = root / "work" / ARMS[0] / f"im-{task}"
        base_names = [*setup["source_paths"]]
        base_names.extend(
            name
            for name in setup["test_hashes"]
            if name not in base_names
        )
        base = "\n".join(
            f"### {name}\n```python\n{base_file(repo, setup['base_head'], name)}\n```"
            for name in base_names
        )
        labels = {}
        candidates = []
        for label, arm in zip(LABELS, order(task), strict=True):
            labels[label] = arm
            stem = root / "implement" / arm / task
            meta = json.loads(path(stem, ".meta.json").read_text())
            patch = path(stem, ".patch").read_text(errors="ignore")
            candidates.append(
                f"## Candidate {label}\n\n"
                f"Visible tests: {'PASS' if meta['visible_exit'] == 0 else 'FAIL'}\n\n"
                f"Hidden tests: {'PASS' if meta['hidden_exit'] == 0 else 'FAIL'}\n\n"
                f"```diff\n{patch}\n```\n"
            )
        prompt = f"""You are an independent senior code evaluator.

Four anonymous candidates implemented the same request from the same base.
Do not infer model, plugin, or workflow identity. Inspect patches even when
tests pass. Return JSON only with all labels exactly once.

Score each candidate 0..4 for completeness, correctness, scope_discipline,
maintainability, and evidence_quality. Cite blocker/high defects by file and
identifying diff line.

Schema:
{{
  "task": "{task}",
  "candidates": [{{
    "label": "A",
    "completeness": 0,
    "correctness": 0,
    "scope_discipline": 0,
    "maintainability": 0,
    "evidence_quality": 0,
    "blockers": [{{"location": "", "finding": "", "impact": ""}}],
    "high": [],
    "summary": ""
  }}],
  "ranking_best_to_worst": ["A", "B", "C", "D"]
}}

## Request

{setup['prompt']}

## Base repository

{base}

## Anonymous candidates

{''.join(candidates)}
"""
        (prompts / f"{task}.txt").write_text(prompt)
        human.append(
            f"# Task: {task}\n\n## Request\n\n{setup['prompt']}\n\n"
            f"## Base repository\n\n{base}\n\n## Candidates\n\n"
            + "\n".join(candidates)
            + "\n## Independent reviewer sheet\n\n"
            "| Candidate | completeness | correctness | scope | maintainability | evidence |\n"
            "|---|---:|---:|---:|---:|---:|\n"
            "| A | | | | | |\n| B | | | | | |\n| C | | | | | |\n| D | | | | | |\n\n"
            "Ranking:\n\nConfidence:\n\nBlocker/high findings:\n"
        )
    (blind / "HUMAN-REVIEW-PACKET.md").write_text(
        "# Human blind review packet\n\n"
        "> Submit two independent reviews before opening scored RESULTS.md.\n\n"
        + "\n\n---\n\n".join(human)
    )
    print(blind)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))
