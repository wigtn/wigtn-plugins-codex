#!/usr/bin/env python3
"""Report Evidence Contract validity, source drift, and missing code evidence."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = PLUGIN_ROOT / "scripts" / "validate-evidence.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    validated = subprocess.run(
        [sys.executable, str(VALIDATOR), str(args.artifact)],
        text=True,
        capture_output=True,
    )
    contract_valid = validated.returncode == 0
    contract_errors = [
        line.removeprefix("- ").strip()
        for line in validated.stderr.splitlines()
        if line.startswith("- ")
    ]
    try:
        document = json.loads(args.artifact.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 2

    drift = []
    missing = []
    for source in document.get("source_artifacts", []):
        path = args.root / source.get("path", "")
        if not path.is_file():
            missing.append(source.get("path", ""))
        elif source.get("sha256") and digest(path) != source["sha256"]:
            drift.append(source["path"])
    for requirement in document.get("requirements", []):
        for evidence in requirement.get("code_evidence", []):
            path = args.root / evidence.get("path", "")
            if not path.is_file():
                missing.append(evidence.get("path", ""))
                continue
            lines = len(path.read_text(errors="ignore").splitlines())
            if evidence.get("line_end", 0) > lines:
                missing.append(
                    f"{evidence.get('path')}:{evidence.get('line_end')} > {lines}"
                )
    statuses = Counter(
        item.get("status", "unknown")
        for item in document.get("requirements", [])
    )
    result = {
        "healthy": contract_valid and not drift and not missing,
        "contract_valid": contract_valid,
        "contract_errors": contract_errors,
        "source_drift": sorted(set(drift)),
        "missing_or_invalid_evidence": sorted(set(missing)),
        "requirements_by_status": dict(sorted(statuses.items())),
        "release_authority": document.get("release_authority", {}),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Evidence status: " + ("HEALTHY" if result["healthy"] else "ATTENTION"))
        print("Requirements: " + json.dumps(result["requirements_by_status"]))
        for item in result["source_drift"]:
            print(f"- source drift: {item}")
        for item in result["missing_or_invalid_evidence"]:
            print(f"- missing/invalid evidence: {item}")
        for item in result["contract_errors"]:
            print(f"- contract: {item}")
    return 0 if result["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
