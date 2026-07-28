#!/usr/bin/env python3
"""Create isolated WorkGraph planning pilot repositories and prompts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "tests" / "workgraph" / "pilot-cases.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--case")
    parser.add_argument("--archive-dir", type=Path)
    args = parser.parse_args()
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    if args.case:
        cases = [case for case in cases if case["id"] == args.case]
        if not cases:
            raise SystemExit(f"unknown case: {args.case}")
    for case in cases:
        work = args.run_root / "work" / case["id"]
        prompt = args.run_root / "prompts" / f"{case['id']}.txt"
        if work.exists():
            if args.archive_dir is None:
                raise SystemExit(f"work already exists: {work}")
            args.archive_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(work), str(args.archive_dir / "work"))
        (work / "docs").mkdir(parents=True)
        (work / ".wigtn").mkdir()
        prompt.parent.mkdir(parents=True, exist_ok=True)
        requirements = "\n".join(
            f"- {requirement_id}: {text}"
            for requirement_id, text in case["requirements"]
        )
        paths = "\n".join(f"- `{path}`" for path in case["paths"])
        (work / "docs" / "PRD.md").write_text(
            f"# {case['title']}\n\n"
            "## Functional Requirements\n\n"
            f"{requirements}\n\n"
            "## Suggested implementation paths\n\n"
            f"{paths}\n\n"
            "## Planning note\n\n"
            "Sequence persistence or shared primitives before behavior that "
            "depends on them. Do not implement the feature in this task.\n",
            encoding="utf-8",
        )
        project = {
            "schema_version": "1.0",
            "requirement_sources": ["docs/PRD.md"],
            "verification_commands": [case["verification"]],
            "protected_paths": [".git", ".env", "USER-DRAFT.txt"],
            "prd_profile": "auto",
            "evidence_path": ".wigtn/evidence.json",
            "lifecycle_profile": "flow",
            "workgraph_path": ".wigtn/workgraph.json",
        }
        (work / ".wigtn" / "project.json").write_text(
            json.dumps(project, indent=2) + "\n", encoding="utf-8"
        )
        (work / "USER-DRAFT.txt").write_text(
            f"sentinel:{case['id']}\n", encoding="utf-8"
        )
        prompt.write_text(
            "Use $wigtn-plugins-with-codex:work-planner to create a saved, "
            "cross-session implementation plan from docs/PRD.md. Inspect "
            ".wigtn/project.json. Show the official CLI dry-run before each "
            "mutation and then apply it. Refine the generated WorkGraph so "
            "tasks have meaningful intended paths, real dependencies where "
            "ordering is required, repository-defined checks, protected paths, "
            "and proportionate risk. Validate the final graph and report next "
            "task IDs. Do not implement code, run the feature checks, alter "
            "USER-DRAFT.txt, or perform Git/remote actions.\n",
            encoding="utf-8",
        )
    print(f"WorkGraph pilot setup: {len(cases)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
