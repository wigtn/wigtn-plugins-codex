#!/usr/bin/env python3
"""Regression tests for the dependency-free evidence validator."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT
    / "plugins"
    / "wigtn-plugins-with-codex"
    / "scripts"
    / "validate-evidence.py"
)
FIXTURES = ROOT / "tests" / "evidence"


def run_path(path: Path, expected: int, message: str | None = None) -> str:
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    if completed.returncode != expected:
        raise AssertionError(
            f"{path.name}: expected exit {expected}, "
            f"got {completed.returncode}\n{output}"
        )
    if message is not None and message not in output:
        raise AssertionError(
            f"{path.name}: missing diagnostic {message!r}\n{output}"
        )
    return output


def run_fixture(name: str, expected: int, message: str | None = None) -> str:
    return run_path(FIXTURES / name, expected, message)


def run_mutation(
    directory: Path,
    source: dict,
    name: str,
    mutate,
    message: str,
) -> None:
    document = deepcopy(source)
    mutate(document)
    path = directory / f"{name}.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    run_path(path, 1, message)


def main() -> int:
    run_fixture("valid-acceptance.json", 0, "PASS")
    run_fixture(
        "invalid-unexecuted.json",
        1,
        "verified requirements need a referenced passing check",
    )
    run_fixture(
        "invalid-authority.json",
        1,
        "performed push lacks recorded user authority",
    )
    valid = json.loads(
        (FIXTURES / "valid-acceptance.json").read_text(encoding="utf-8")
    )
    with tempfile.TemporaryDirectory(prefix="wigtn-evidence-tests-") as tmp:
        directory = Path(tmp)
        run_mutation(
            directory,
            valid,
            "absolute-path",
            lambda doc: doc["requirements"][0]["code_evidence"][0].update(
                {"path": "/tmp/implementation.py"}
            ),
            "must be a repository-relative path",
        )
        run_mutation(
            directory,
            valid,
            "duplicate-check",
            lambda doc: doc["checks"].append(deepcopy(doc["checks"][0])),
            "duplicate check id",
        )
        run_mutation(
            directory,
            valid,
            "bad-passed-exit",
            lambda doc: doc["checks"][0].update({"exit_code": 1}),
            "passed checks must have exit code 0",
        )
        run_mutation(
            directory,
            valid,
            "unknown-key",
            lambda doc: doc.update({"quality_score": 10}),
            "unknown keys: quality_score",
        )
        run_mutation(
            directory,
            valid,
            "partial-without-gap",
            lambda doc: doc["requirements"][0].update(
                {"status": "partially-verified", "gaps": []}
            ),
            "partially-verified requires at least one gap",
        )
        run_mutation(
            directory,
            valid,
            "implemented-with-passing-check",
            lambda doc: doc["requirements"][0].update(
                {"status": "implemented-not-executed"}
            ),
            "use verified when a relevant passing check is referenced",
        )
        run_mutation(
            directory,
            valid,
            "wrong-version",
            lambda doc: doc.update({"schema_version": "2.0"}),
            "must equal '1.0'",
        )
    print("Evidence contract: PASS (10 cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
