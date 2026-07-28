#!/usr/bin/env python3
"""Verify packet membership and hashes without trusting unlisted files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    manifest_path = args.packet / "PACKET-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    errors = []
    listed = set()
    for item in manifest.get("files", []):
        relative = PurePosixPath(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"unsafe path: {relative}")
            continue
        listed.add(relative.as_posix())
        path = args.packet / relative
        if not path.is_file():
            errors.append(f"missing: {relative}")
        elif digest(path) != item["sha256"]:
            errors.append(f"hash mismatch: {relative}")
        elif path.stat().st_size != item["bytes"]:
            errors.append(f"size mismatch: {relative}")
    actual = {
        path.relative_to(args.packet).as_posix()
        for path in args.packet.rglob("*")
        if path.is_file() and path != manifest_path
    }
    for extra in sorted(actual - listed):
        errors.append(f"unlisted: {extra}")
    if errors:
        print("Eval packet: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Eval packet: PASS ({len(listed)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
