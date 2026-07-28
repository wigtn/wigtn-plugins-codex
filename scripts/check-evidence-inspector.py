#!/usr/bin/env python3
"""Regression test Evidence Contract health and drift inspection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
INSPECTOR = (
    ROOT / "plugins/wigtn-plugins-with-codex/scripts/inspect-evidence.py"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(root: Path, artifact: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(INSPECTOR),
            str(artifact),
            "--root",
            str(root),
            "--json",
        ],
        text=True,
        capture_output=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="wigtn-evidence-status-") as temp:
        root = Path(temp)
        source = root / "requirements.md"
        code = root / "feature.py"
        source.write_text("REQ-01\n")
        code.write_text("VALUE = 1\n")
        artifact = root / "evidence.json"
        artifact.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "artifact_type": "acceptance",
                    "source_artifacts": [
                        {
                            "kind": "requirements",
                            "path": "requirements.md",
                            "sha256": sha(source),
                        }
                    ],
                    "requirements": [
                        {
                            "id": "REQ-01",
                            "text": "VALUE exists.",
                            "status": "implemented-not-executed",
                            "code_evidence": [
                                {
                                    "path": "feature.py",
                                    "line_start": 1,
                                    "line_end": 1,
                                }
                            ],
                            "check_ids": [],
                            "gaps": ["No relevant executed check."],
                        }
                    ],
                    "checks": [],
                    "release_authority": {
                        "source_request": "",
                        "commit": False,
                        "push": False,
                        "pull_request": False,
                        "deploy": False,
                    },
                    "external_actions": [],
                    "limitations": ["Fixture."],
                }
            )
        )
        healthy = inspect(root, artifact)
        if healthy.returncode:
            raise AssertionError(healthy.stdout + healthy.stderr)
        source.write_text("REQ-01 changed\n")
        drift = inspect(root, artifact)
        if drift.returncode != 1 or "requirements.md" not in drift.stdout:
            raise AssertionError("source drift was not detected")
    print("Evidence inspector: PASS (health/drift)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
