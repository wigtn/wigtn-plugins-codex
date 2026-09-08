#!/usr/bin/env python3
"""Validate optional WIGTN project context without dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re


REQUIRED = {
    "schema_version",
    "requirement_sources",
    "verification_commands",
    "protected_paths",
    "prd_profile",
    "evidence_path",
}
OPTIONAL = {"lifecycle_profile", "workgraph_path"}


def safe_path(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    return not (
        path.is_absolute()
        or ".." in path.parts
        or re.match(r"^[A-Za-z]:/", normalized)
        or "://" in normalized
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("context", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors = []
    try:
        document = json.loads(args.context.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        document = {}
        errors.append(f"$: invalid JSON: {exc}")
    if not isinstance(document, dict):
        document = {}
        errors.append("$: must be an object")
    missing = sorted(REQUIRED - document.keys())
    unknown = sorted(document.keys() - REQUIRED - OPTIONAL)
    if missing:
        errors.append("$: missing keys: " + ", ".join(missing))
    if unknown:
        errors.append("$: unknown keys: " + ", ".join(unknown))
    if document.get("schema_version") != "1.0":
        errors.append("$.schema_version: must equal '1.0'")
    if document.get("prd_profile") not in {"auto", "compact", "full"}:
        errors.append("$.prd_profile: must be auto, compact, or full")
    if (
        "lifecycle_profile" in document
        and document.get("lifecycle_profile") not in {"lite", "flow", "studio"}
    ):
        errors.append("$.lifecycle_profile: must be lite, flow, or studio")
    for key in ("requirement_sources", "protected_paths"):
        values = document.get(key)
        if not isinstance(values, list):
            errors.append(f"$.{key}: must be an array")
        elif any(not safe_path(value) for value in values):
            errors.append(f"$.{key}: paths must be non-empty and repository-relative")
        elif len(values) != len(set(values)):
            errors.append(f"$.{key}: duplicate paths are not allowed")
    commands = document.get("verification_commands")
    if not isinstance(commands, list) or any(
        not isinstance(command, str) or not command.strip()
        for command in commands if isinstance(commands, list)
    ):
        errors.append("$.verification_commands: must contain non-empty strings")
    if not safe_path(document.get("evidence_path")):
        errors.append("$.evidence_path: must be a repository-relative path")
    if "workgraph_path" in document and not safe_path(
        document.get("workgraph_path")
    ):
        errors.append("$.workgraph_path: must be a repository-relative path")
    result = {"valid": not errors, "errors": errors}
    if args.json:
        print(json.dumps(result, indent=2))
    elif errors:
        print("Project context: FAIL")
        for error in errors:
            print(f"- {error}")
    else:
        print("Project context: PASS")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
