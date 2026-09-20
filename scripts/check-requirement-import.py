#!/usr/bin/env python3
"""Regression tests for supported read-only requirement imports."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "wigtn-plugins-with-codex"
IMPORTER = PLUGIN / "scripts" / "import-requirements.py"
VALIDATOR = PLUGIN / "scripts" / "validate-evidence.py"
FIXTURES = ROOT / "tests" / "import"


def import_fixture(name: str) -> dict:
    command = [
        sys.executable,
        str(IMPORTER),
        str(FIXTURES / f"{name}.md"),
        "--root",
        str(ROOT),
    ]
    first = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False
    )
    second = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False
    )
    if first.returncode or second.returncode:
        raise AssertionError(first.stderr + second.stderr)
    if first.stdout != second.stdout:
        raise AssertionError(f"{name}: import is not deterministic")
    return json.loads(first.stdout)


def validate(document: dict) -> None:
    with tempfile.TemporaryDirectory(prefix="wigtn-import-tests-") as tmp:
        path = Path(tmp) / "evidence.json"
        path.write_text(json.dumps(document) + "\n", encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR), str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode:
            raise AssertionError(completed.stdout + completed.stderr)


def resume_fixture(name: str) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            str(IMPORTER),
            str(FIXTURES / f"{name}.md"),
            "--root",
            str(ROOT),
            "--existing",
            str(ROOT / "tests/evidence/valid-acceptance.json"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


def check_literal_requirements() -> None:
    spec = importlib.util.spec_from_file_location("requirement_importer", IMPORTER)
    importer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(importer)
    literal = "Use `unit_price * quantity`, __version__, ROUND_HALF_UP and *.csv."
    sources = [
        "REQ-LITERAL: " + literal,
        "| ID | Requirement |\n| --- | --- |\n| REQ-LITERAL | " + literal + " |",
    ]
    for source in sources:
        assert importer.explicit_requirements(source) == [("REQ-LITERAL", literal)]
    assert importer.explicit_requirements("REQ-NEG: -1") == [("REQ-NEG", "-1")]
    assert importer.explicit_requirements("REQ-SPACE: Match `a  b` exactly.") == [
        ("REQ-SPACE", "Match `a  b` exactly.")
    ]
    for before, after in [
        ("Use unit_price.", "Use unitprice."),
        ("Compute x*y.", "Compute xy."),
        ("Match `a  b`.", "Match `a b`."),
    ]:
        existing = {"requirements": [{"id": "REQ-LITERAL", "text": before,
                    "status": "verified", "check_ids": ["CHK-LITERAL"]}],
                    "checks": [{"id": "CHK-LITERAL"}]}
        changed = importer.normalize([(Path("requirements.md"),
                                       "REQ-LITERAL: " + after, "generic")])
        importer.resume(changed, existing)
        assert changed["requirements"][0]["status"] == "not-verifiable"
        assert changed["checks"] == []
        unchanged = importer.normalize([(Path("requirements.md"),
                                         "REQ-LITERAL: " + before, "generic")])
        importer.resume(unchanged, existing)
        assert unchanged["requirements"][0]["status"] == "verified"
        assert len(unchanged["checks"]) == 1


def main() -> int:
    check_literal_requirements()
    expected = {
        "openspec": ("openspec", "OS-", 2),
        "spec-kit": ("spec-kit", "FR-", 2),
        "bmad": ("bmad", "BM-", 2),
    }
    for name, (source_format, prefix, count) in expected.items():
        document = import_fixture(name)
        requirements = document["requirements"]
        if document["metadata"]["source_formats"] != [source_format]:
            raise AssertionError(f"{name}: format detection failed")
        if len(requirements) != count:
            raise AssertionError(
                f"{name}: expected {count} requirements, got {len(requirements)}"
            )
        if not all(item["id"].startswith(prefix) for item in requirements):
            raise AssertionError(f"{name}: requirement IDs are not normalized")
        if not all(item["status"] == "not-verifiable" for item in requirements):
            raise AssertionError(f"{name}: import overclaimed verification")
        validate(document)
    unchanged = resume_fixture("resume-unchanged")
    unchanged_by_id = {
        item["id"]: item for item in unchanged["requirements"]
    }
    if unchanged_by_id["FR-01"]["status"] != "verified":
        raise AssertionError("unchanged evidence was not preserved")
    if [check["id"] for check in unchanged["checks"]] != ["CHK-01"]:
        raise AssertionError("referenced check was not preserved")
    changed = resume_fixture("resume-changed")
    changed_by_id = {item["id"]: item for item in changed["requirements"]}
    if changed_by_id["FR-01"]["status"] != "not-verifiable":
        raise AssertionError("changed requirement retained stale evidence")
    if changed["checks"]:
        raise AssertionError("orphaned check was retained")
    validate(unchanged)
    validate(changed)
    print("Requirement import: PASS (3 formats + literal preservation + resume/drift)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
