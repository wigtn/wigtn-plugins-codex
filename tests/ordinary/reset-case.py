#!/usr/bin/env python3
"""Archive and reconstruct one ordinary-gate worktree after infra failure."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "ordinary"))

from task_bank import BY_ID  # noqa: E402


def write_files(root: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    parser.add_argument("arm")
    parser.add_argument("case")
    parser.add_argument("repeat", type=int)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.case not in BY_ID or args.repeat < 1:
        raise SystemExit("invalid case or repeat")
    work = args.run_root / "work" / args.arm / args.case / str(args.repeat)
    if not work.is_dir() or args.archive.exists():
        raise SystemExit("worktree missing or archive already exists")
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(work), str(args.archive))
    write_files(work, BY_ID[args.case]["files"])
    (work / "USER-DRAFT.txt").write_text(
        f"sentinel:{args.arm}:{args.case}:{args.repeat}\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
