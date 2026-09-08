#!/usr/bin/env python3
"""Inspect Git release state without mutating the repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


DEFAULT_MAX_DIFF_BYTES = 64 * 1024


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def names(root: Path, *args: str) -> list[str]:
    result = git(root, *args)
    return sorted(value for value in result.stdout.split("\0") if value)


def bounded_text(value: str, max_bytes: int) -> tuple[str, int, bool]:
    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value, len(encoded), False
    return encoded[:max_bytes].decode("utf-8", errors="ignore"), len(encoded), True


def diff_section(root: Path, *args: str, max_bytes: int) -> dict[str, object]:
    patch = git(root, "diff", *args).stdout
    stat = git(root, "diff", *args, "--stat").stdout
    bounded_patch, byte_count, truncated = bounded_text(patch, max_bytes)
    return {
        "bytes": byte_count,
        "truncated": truncated,
        "stat": stat,
        "patch": bounded_patch,
    }


def check_section(root: Path, *args: str) -> dict[str, object]:
    result = git(root, "diff", *args, "--check", check=False)
    return {
        "exit_code": result.returncode,
        "clean": result.returncode == 0,
        "output": result.stdout + result.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", nargs="?", type=Path, default=Path("."))
    parser.add_argument(
        "--include-diffs",
        action="store_true",
        help="include bounded staged and unstaged patches plus whitespace checks",
    )
    parser.add_argument(
        "--max-diff-bytes",
        type=int,
        default=DEFAULT_MAX_DIFF_BYTES,
        help="maximum UTF-8 bytes returned for each staged/unstaged patch",
    )
    args = parser.parse_args()
    if args.max_diff_bytes <= 0:
        parser.error("--max-diff-bytes must be positive")
    root = args.repository.resolve()
    probe = git(root, "rev-parse", "--is-inside-work-tree", check=False)
    if probe.returncode or probe.stdout.strip() != "true":
        print(json.dumps({"valid": False, "error": "not a Git worktree"}))
        return 1

    branch_result = git(root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    upstream_result = git(
        root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}",
        check=False,
    )
    upstream = (
        upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    )
    ahead = behind = None
    if upstream:
        counts = git(
            root, "rev-list", "--left-right", "--count", f"HEAD...{upstream}"
        ).stdout.split()
        ahead, behind = (int(counts[0]), int(counts[1]))

    git_dir_text = git(root, "rev-parse", "--git-dir").stdout.strip()
    git_dir = Path(git_dir_text)
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    operation = "none"
    if (git_dir / "MERGE_HEAD").exists():
        operation = "merge"
    elif (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
        operation = "rebase"
    elif (git_dir / "CHERRY_PICK_HEAD").exists():
        operation = "cherry-pick"
    elif (git_dir / "REVERT_HEAD").exists():
        operation = "revert"

    document = {
        "schema_version": "1.0",
        "valid": True,
        "head": head,
        "branch": branch,
        "detached": branch is None,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
        "operation": operation,
        "staged": names(root, "diff", "--cached", "--name-only", "-z"),
        "unstaged": names(root, "diff", "--name-only", "-z"),
        "untracked": names(
            root, "ls-files", "--others", "--exclude-standard", "-z"
        ),
        "conflicts": names(
            root, "diff", "--name-only", "--diff-filter=U", "-z"
        ),
    }
    if args.include_diffs:
        document["diffs"] = {
            "staged": diff_section(
                root, "--cached", max_bytes=args.max_diff_bytes
            ),
            "unstaged": diff_section(root, max_bytes=args.max_diff_bytes),
            "check": {
                "staged": check_section(root, "--cached"),
                "unstaged": check_section(root),
            },
        }
    print(json.dumps(document, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
