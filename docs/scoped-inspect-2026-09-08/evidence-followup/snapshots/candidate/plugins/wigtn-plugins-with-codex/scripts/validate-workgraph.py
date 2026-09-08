#!/usr/bin/env python3
"""Validate a WIGTN WorkGraph without third-party dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from workgraph_core import validate_graph


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workgraph", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        document = json.loads(args.workgraph.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
    else:
        errors = validate_graph(document)
    if args.json:
        print(
            json.dumps(
                {"valid": not errors, "errors": errors},
                ensure_ascii=False,
                indent=2,
            )
        )
    elif errors:
        print("WorkGraph validation: FAIL")
        for error in errors:
            print(f"- {error}")
    else:
        print("WorkGraph validation: PASS")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
