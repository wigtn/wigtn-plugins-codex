#!/usr/bin/env python3
"""Migrate a WIGTN WorkGraph with an atomic backup and explicit apply."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

from workgraph_core import atomic_write_json, migrate, read_json, validate_graph


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workgraph", type=Path)
    parser.add_argument("--graph-name")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        source = args.workgraph.resolve()
        document = read_json(source)
        migrated = migrate(document, args.graph_name or source.parent.parent.name)
        errors = validate_graph(migrated)
        if errors:
            raise ValueError("\n".join(errors))
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2
    target = (args.output or source).resolve()
    print(
        f"Would migrate {source} to WorkGraph 1.0 at {target}"
        if not args.apply
        else f"Migrating {source} to WorkGraph 1.0 at {target}"
    )
    if not args.apply:
        return 0
    try:
        if target == source:
            backup = source.with_suffix(source.suffix + ".bak")
            shutil.copy2(source, backup)
            print(f"Backup: {backup}")
        atomic_write_json(target, migrated)
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
