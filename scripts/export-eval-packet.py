#!/usr/bin/env python3
"""Export a sanitized, hash-addressed evaluation packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil


ALLOWED_SUFFIXES = {".json", ".log", ".md", ".patch", ".txt", ".csv"}
EXCLUDED_PARTS = {"homes", "home", "work", "staging", "prompt-input"}
SECRET = re.compile(
    r"(?i)(authorization:\s*bearer\s+|api[_-]?key[\"'=:\s]+|token[\"'=:\s]+)"
    r"([A-Za-z0-9._~+/=-]{12,})"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_relative(path: Path, root: Path, excluded_prefixes: list[Path]) -> Path:
    relative = path.relative_to(root)
    if any(
        part in EXCLUDED_PARTS
        or part.endswith("-home")
        or part.endswith("-homes")
        for part in relative.parts
    ):
        raise ValueError("excluded")
    for prefix in excluded_prefixes:
        if relative == prefix or prefix in relative.parents:
            raise ValueError("excluded")
    if path.suffix not in ALLOWED_SUFFIXES:
        raise ValueError("unsupported")
    return relative


def sanitize(text: str, roots: list[Path]) -> str:
    value = text
    for root in roots:
        value = value.replace(str(root), "<RUN_ROOT>")
        value = value.replace(str(root.resolve()), "<RUN_ROOT>")
    value = re.sub(r"/Users/[^/\s]+", "/Users/<USER>", value)
    value = SECRET.sub(r"\1<REDACTED>", value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exclude-prefix",
        action="append",
        default=[],
        help="repository-relative run-root prefix to omit; may be repeated",
    )
    parser.add_argument("destination", type=Path)
    parser.add_argument("run_roots", nargs="+", type=Path)
    args = parser.parse_args()
    excluded_prefixes = [Path(value) for value in args.exclude_prefix]
    if any(
        value.is_absolute() or ".." in value.parts or str(value) in {"", "."}
        for value in excluded_prefixes
    ):
        raise SystemExit("exclude prefixes must be safe non-empty relative paths")
    if args.destination.exists():
        raise SystemExit(f"destination already exists: {args.destination}")
    args.destination.mkdir(parents=True)
    records = []
    for index, root in enumerate(args.run_roots, 1):
        if not root.is_dir():
            raise SystemExit(f"run root missing: {root}")
        packet_root = args.destination / f"study-{index:02d}"
        for source in sorted(root.rglob("*")):
            if not source.is_file() or source.is_symlink():
                continue
            try:
                relative = safe_relative(source, root, excluded_prefixes)
            except ValueError:
                continue
            target = packet_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            text = source.read_text(encoding="utf-8", errors="replace")
            target.write_text(sanitize(text, args.run_roots), encoding="utf-8")
            records.append(
                {
                    "path": target.relative_to(args.destination).as_posix(),
                    "sha256": digest(target),
                    "bytes": target.stat().st_size,
                }
            )
    manifest = {
        "packet_version": "1.0",
        "source_count": len(args.run_roots),
        "files": records,
    }
    (args.destination / "PACKET-MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Eval packet: {len(records)} files")
    print(args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
