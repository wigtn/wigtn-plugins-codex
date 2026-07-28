#!/usr/bin/env python3
"""Deterministic WorkGraph contract, lifecycle, migration, and CLI tests."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SCRIPTS = (
    ROOT / "plugins" / "wigtn-plugins-with-codex" / "scripts"
)
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from workgraph_core import (  # noqa: E402
    atomic_write_json,
    digest_bytes,
    empty_graph,
    inspect_drift,
    merge_import,
    migrate,
    plan_graph,
    ready_tasks,
    set_task_dependency,
    summary,
    update_task,
    validate_graph,
)


CLI = PLUGIN_SCRIPTS / "wigtn.py"
DIGEST = "a" * 64


def valid_graph() -> dict:
    return {
        "schema_version": "1.0",
        "graph_id": "WG-CONTRACT",
        "revision": 7,
        "sources": [
            {
                "id": "SRC-PRD",
                "kind": "wigtn",
                "path": "docs/prd.md",
                "sha256": DIGEST,
            }
        ],
        "requirements": [
            {
                "id": "FR-01",
                "source_id": "SRC-PRD",
                "text": "Persist the user preference.",
                "source_sha256": DIGEST,
                "status": "active",
            },
            {
                "id": "FR-02",
                "source_id": "SRC-PRD",
                "text": "Expose the preference in settings.",
                "source_sha256": DIGEST,
                "status": "active",
            },
        ],
        "artifacts": [
            {
                "id": "ART-SCREEN",
                "kind": "screen-spec",
                "path": "docs/screen.md",
                "requirement_ids": ["FR-02"],
                "status": "ready",
            }
        ],
        "tasks": [
            {
                "id": "TASK-DATA",
                "title": "Persist preference",
                "requirement_ids": ["FR-01"],
                "artifact_ids": [],
                "depends_on": [],
                "intended_paths": ["src/data.py"],
                "protected_paths": [".git"],
                "risk": "medium",
                "status": "verified",
                "check_ids": ["CHK-01"],
                "blocker": None,
                "evidence_refs": [".wigtn/evidence.json"],
            },
            {
                "id": "TASK-SCREEN",
                "title": "Add preference control",
                "requirement_ids": ["FR-02"],
                "artifact_ids": ["ART-SCREEN"],
                "depends_on": ["TASK-DATA"],
                "intended_paths": ["src/settings.tsx"],
                "protected_paths": [".git"],
                "risk": "low",
                "status": "ready",
                "check_ids": ["CHK-02"],
                "blocker": None,
                "evidence_refs": [],
            },
        ],
        "checks": [
            {
                "id": "CHK-01",
                "task_ids": ["TASK-DATA"],
                "requirement_ids": ["FR-01"],
                "command": "pytest tests/test_data.py",
                "status": "passed",
                "evidence_ref": ".wigtn/evidence.json",
            },
            {
                "id": "CHK-02",
                "task_ids": ["TASK-SCREEN"],
                "requirement_ids": ["FR-02"],
                "command": "npm test -- settings",
                "status": "pending",
                "evidence_ref": None,
            },
        ],
        "release_gates": [
            {
                "id": "GATE-DEFAULT",
                "requires_task_ids": ["TASK-DATA", "TASK-SCREEN"],
                "requires_requirement_ids": ["FR-01", "FR-02"],
                "status": "blocked",
                "authority_actions": [],
            }
        ],
        "metadata": {"fixture": "valid"},
    }


def expect_valid(name: str, document: dict) -> None:
    errors = validate_graph(document)
    if errors:
        raise AssertionError(f"{name}: expected valid\n" + "\n".join(errors))


def expect_invalid(
    name: str, mutation: Callable[[dict], None], expected: str
) -> None:
    document = valid_graph()
    mutation(document)
    errors = validate_graph(document)
    if not any(expected in error for error in errors):
        raise AssertionError(
            f"{name}: expected error containing {expected!r}\n"
            + "\n".join(errors)
        )


def imported_document(text: str = "Persist the user preference.") -> dict:
    return {
        "schema_version": "1.0",
        "artifact_type": "acceptance",
        "source_artifacts": [{"kind": "wigtn", "path": "docs/prd.md"}],
        "requirements": [
            {
                "id": "FR-01",
                "text": text,
                "status": "not-verifiable",
                "code_evidence": [],
                "check_ids": [],
                "gaps": ["Not inspected."],
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
        "limitations": ["Imported only."],
        "metadata": {"source_formats": ["wigtn"]},
    }


def run_cli(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(CLI),
            "--root",
            str(root),
            "--json",
            *arguments,
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    cases = 0

    expect_valid("empty", empty_graph("contract"))
    cases += 1
    expect_valid("full", valid_graph())
    cases += 1
    if summary(valid_graph())["next_task_ids"] != ["TASK-SCREEN"]:
        raise AssertionError("summary: wrong next task")
    cases += 1
    if [item["id"] for item in ready_tasks(valid_graph())] != ["TASK-SCREEN"]:
        raise AssertionError("ready_tasks: dependency resolution failed")
    cases += 1

    invalid_cases: list[tuple[str, Callable[[dict], None], str]] = [
        (
            "schema-version",
            lambda graph: graph.update(schema_version="2.0"),
            "schema_version",
        ),
        (
            "negative-revision",
            lambda graph: graph.update(revision=-1),
            "non-negative",
        ),
        (
            "unsafe-source-path",
            lambda graph: graph["sources"][0].update(path="../prd.md"),
            "safe repository-relative",
        ),
        (
            "duplicate-source",
            lambda graph: graph["sources"].append(deepcopy(graph["sources"][0])),
            "duplicate identifier",
        ),
        (
            "unknown-requirement-source",
            lambda graph: graph["requirements"][0].update(source_id="SRC-NOPE"),
            "unknown source",
        ),
        (
            "duplicate-requirement",
            lambda graph: graph["requirements"].append(
                deepcopy(graph["requirements"][0])
            ),
            "duplicate identifier",
        ),
        (
            "bad-requirement-digest",
            lambda graph: graph["requirements"][0].update(source_sha256="bad"),
            "lowercase SHA-256",
        ),
        (
            "unknown-artifact-requirement",
            lambda graph: graph["artifacts"][0].update(
                requirement_ids=["FR-99"]
            ),
            "unknown reference",
        ),
        (
            "unsafe-artifact-path",
            lambda graph: graph["artifacts"][0].update(path="/tmp/screen.md"),
            "safe repository-relative",
        ),
        (
            "task-without-requirement",
            lambda graph: graph["tasks"][0].update(requirement_ids=[]),
            "at least 1",
        ),
        (
            "unknown-task-requirement",
            lambda graph: graph["tasks"][0].update(requirement_ids=["FR-99"]),
            "unknown reference",
        ),
        (
            "unknown-artifact",
            lambda graph: graph["tasks"][1].update(artifact_ids=["ART-NOPE"]),
            "unknown reference",
        ),
        (
            "unknown-dependency",
            lambda graph: graph["tasks"][1].update(depends_on=["TASK-NOPE"]),
            "unknown reference",
        ),
        (
            "self-dependency",
            lambda graph: graph["tasks"][1].update(depends_on=["TASK-SCREEN"]),
            "cannot depend on itself",
        ),
        (
            "dependency-cycle",
            lambda graph: graph["tasks"][0].update(
                depends_on=["TASK-SCREEN"], status="draft"
            ),
            "dependency cycle",
        ),
        (
            "blocked-without-reason",
            lambda graph: graph["tasks"][1].update(status="blocked"),
            "require a blocker",
        ),
        (
            "reason-on-ready",
            lambda graph: graph["tasks"][1].update(blocker="Waiting"),
            "only blocked",
        ),
        (
            "unsafe-intended-path",
            lambda graph: graph["tasks"][1].update(
                intended_paths=["../../secret"]
            ),
            "safe repository-relative",
        ),
        (
            "unknown-check",
            lambda graph: graph["tasks"][1].update(check_ids=["CHK-99"]),
            "unknown reference",
        ),
        (
            "verified-without-pass",
            lambda graph: graph["tasks"][1].update(
                status="verified", evidence_refs=[".wigtn/evidence.json"]
            ),
            "linked passing check",
        ),
        (
            "verified-without-evidence",
            lambda graph: graph["tasks"][0].update(evidence_refs=[]),
            "needs evidence",
        ),
        (
            "check-no-backlink",
            lambda graph: graph["checks"][1].update(task_ids=["TASK-DATA"]),
            "does not link back",
        ),
        (
            "passed-check-no-evidence",
            lambda graph: graph["checks"][0].update(evidence_ref=None),
            "require an evidence reference",
        ),
        (
            "pending-check-with-evidence",
            lambda graph: graph["checks"][1].update(
                evidence_ref=".wigtn/evidence.json"
            ),
            "cannot retain evidence",
        ),
        (
            "ready-before-dependency",
            lambda graph: graph["tasks"][0].update(
                status="implemented", evidence_refs=[]
            ),
            "all dependencies",
        ),
        (
            "unknown-gate-task",
            lambda graph: graph["release_gates"][0].update(
                requires_task_ids=["TASK-NOPE"]
            ),
            "unknown reference",
        ),
        (
            "gate-ready-too-early",
            lambda graph: graph["release_gates"][0].update(status="ready"),
            "requires verified tasks",
        ),
        (
            "released-no-authority",
            lambda graph: (
                graph["tasks"][1].update(
                    status="verified",
                    evidence_refs=[".wigtn/evidence.json"],
                ),
                graph["checks"][1].update(
                    status="passed",
                    evidence_ref=".wigtn/evidence.json",
                ),
                graph["release_gates"][0].update(status="released"),
            ),
            "explicit authority",
        ),
        (
            "invalid-authority-action",
            lambda graph: graph["release_gates"][0].update(
                authority_actions=["publish"]
            ),
            "invalid action",
        ),
        (
            "unknown-root-key",
            lambda graph: graph.update(secret=True),
            "unknown keys",
        ),
    ]
    for name, mutation, expected in invalid_cases:
        expect_invalid(name, mutation, expected)
        cases += 1

    base = empty_graph("plan")
    base["sources"] = deepcopy(valid_graph()["sources"])
    base["requirements"] = deepcopy(valid_graph()["requirements"])
    planned = plan_graph(
        base,
        verification_commands=["pytest"],
        protected_paths=[".git"],
    )
    expect_valid("planned", planned)
    if len(planned["tasks"]) != 2 or len(planned["checks"]) != 2:
        raise AssertionError("plan: one task/check per requirement expected")
    cases += 1
    if plan_graph(
        planned,
        verification_commands=["pytest"],
        protected_paths=[".git"],
    ) != planned:
        raise AssertionError("plan: second run must be idempotent")
    cases += 1
    refined = update_task(
        planned,
        planned["tasks"][0]["id"],
        title="Refined task",
        risk="high",
        intended_paths=["src/refined.py"],
        expected_revision=planned["revision"],
    )
    expect_valid("task-update", refined)
    if (
        refined["revision"] != planned["revision"] + 1
        or refined["tasks"][0]["title"] != "Refined task"
        or refined["tasks"][0]["risk"] != "high"
        or refined["tasks"][0]["intended_paths"] != ["src/refined.py"]
    ):
        raise AssertionError("task update did not apply requested fields")
    cases += 1
    if update_task(
        refined,
        refined["tasks"][0]["id"],
        title="Refined task",
        risk="high",
        intended_paths=["src/refined.py"],
    ) != refined:
        raise AssertionError("task update was not idempotent")
    cases += 1
    try:
        update_task(
            refined,
            refined["tasks"][0]["id"],
            title="Conflict",
            expected_revision=planned["revision"],
        )
    except ValueError as exc:
        if "revision conflict" not in str(exc):
            raise
    else:
        raise AssertionError("stale revision update was accepted")
    cases += 1
    try:
        update_task(
            refined,
            refined["tasks"][0]["id"],
            intended_paths=["../escape"],
        )
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe task update path was accepted")
    cases += 1
    dependency_target = refined["tasks"][1]["id"]
    dependency_source = refined["tasks"][0]["id"]
    depended = set_task_dependency(
        refined, dependency_target, dependency_source
    )
    expect_valid("task-dependency", depended)
    target = next(
        item for item in depended["tasks"] if item["id"] == dependency_target
    )
    if target["depends_on"] != [dependency_source] or target["status"] != "draft":
        raise AssertionError("dependency did not demote ready task to draft")
    cases += 1
    if (
        set_task_dependency(depended, dependency_target, dependency_source)
        != depended
    ):
        raise AssertionError("dependency add was not idempotent")
    cases += 1
    try:
        set_task_dependency(depended, dependency_source, dependency_target)
    except ValueError as exc:
        if "cycle" not in str(exc):
            raise
    else:
        raise AssertionError("dependency cycle was accepted")
    cases += 1

    with tempfile.TemporaryDirectory(prefix="wigtn-workgraph-core-") as temporary:
        root = Path(temporary)
        source = root / "docs" / "prd.md"
        source.parent.mkdir(parents=True)
        source.write_text("FR-01: Persist the user preference.\n", encoding="utf-8")
        imported = merge_import(
            empty_graph("import"),
            imported_document(),
            [source],
            root,
        )
        expect_valid("imported", imported)
        cases += 1
        repeated = merge_import(
            imported,
            imported_document(),
            [source],
            root,
        )
        if repeated != imported:
            raise AssertionError("import: unchanged second run must be idempotent")
        cases += 1
        planned_import = plan_graph(
            imported, verification_commands=["pytest"], protected_paths=[".git"]
        )
        source.write_text(
            "FR-01: Persist the preference with encryption.\n", encoding="utf-8"
        )
        drifted, drift = inspect_drift(planned_import, root)
        if not drift or drifted["requirements"][0]["status"] != "stale":
            raise AssertionError("drift: requirement was not marked stale")
        if drifted["tasks"][0]["status"] != "stale":
            raise AssertionError("drift: linked task was not marked stale")
        if drifted["checks"][0]["status"] != "stale":
            raise AssertionError("drift: linked check was not marked stale")
        cases += 1
        imported_changed = merge_import(
            planned_import,
            imported_document("Persist the preference with encryption."),
            [source],
            root,
        )
        if imported_changed["requirements"][0]["status"] != "active":
            raise AssertionError("reimport: changed requirement must become active")
        if imported_changed["tasks"][0]["status"] != "stale":
            raise AssertionError("reimport: old task evidence must stay stale")
        cases += 1
        output = root / "atomic.json"
        atomic_write_json(output, empty_graph("atomic"))
        expect_valid("atomic", json.loads(output.read_text(encoding="utf-8")))
        cases += 1

    legacy = {
        "schema_version": "0.1",
        "requirements": [
            {"id": "FR-01", "text": "Persist preference."},
            "Expose preference.",
        ],
    }
    migrated = migrate(legacy, "legacy")
    expect_valid("migrated", migrated)
    if [item["id"] for item in migrated["requirements"]] != ["FR-01", "REQ-02"]:
        raise AssertionError("migration: stable/derived IDs are wrong")
    cases += 1
    if migrate(migrated, "legacy") != migrated:
        raise AssertionError("migration: current document must be idempotent")
    cases += 1
    try:
        migrate({"schema_version": "9.9"}, "future")
    except ValueError:
        cases += 1
    else:
        raise AssertionError("migration: unsupported version was accepted")

    with tempfile.TemporaryDirectory(prefix="wigtn-workgraph-cli-") as temporary:
        root = Path(temporary)
        source = root / "prd.md"
        source.write_text(
            "## Functional Requirements\n\n"
            "- FR-01: Persist preference.\n"
            "- FR-02: Display preference.\n",
            encoding="utf-8",
        )
        dry_init = run_cli(root, "init")
        if dry_init.returncode or (root / ".wigtn").exists():
            raise AssertionError("CLI init dry-run mutated the repository")
        cases += 1
        applied_init = run_cli(root, "init", "--apply")
        if applied_init.returncode or not (root / ".wigtn/workgraph.json").is_file():
            raise AssertionError(applied_init.stderr)
        cases += 1
        before = (root / ".wigtn/workgraph.json").read_text(encoding="utf-8")
        dry_import = run_cli(root, "import", str(source))
        if dry_import.returncode:
            raise AssertionError(dry_import.stderr)
        if (root / ".wigtn/workgraph.json").read_text(encoding="utf-8") != before:
            raise AssertionError("CLI import dry-run mutated WorkGraph")
        cases += 1
        applied_import = run_cli(root, "import", str(source), "--apply")
        if applied_import.returncode:
            raise AssertionError(applied_import.stderr)
        cases += 1
        applied_plan = run_cli(root, "plan", "--apply")
        if applied_plan.returncode:
            raise AssertionError(applied_plan.stderr)
        cases += 1
        after_plan = (root / ".wigtn/workgraph.json").read_text(encoding="utf-8")
        repeated_plan = run_cli(root, "plan", "--apply")
        if repeated_plan.returncode:
            raise AssertionError(repeated_plan.stderr)
        if (root / ".wigtn/workgraph.json").read_text(encoding="utf-8") != after_plan:
            raise AssertionError("CLI plan apply was not idempotent")
        cases += 1
        cli_graph = json.loads(after_plan)
        first_task, second_task = [item["id"] for item in cli_graph["tasks"]]
        dry_task_update = run_cli(
            root,
            "task",
            "update",
            first_task,
            "--title",
            "CLI refined",
            "--risk",
            "high",
            "--path",
            "src/cli.py",
        )
        if dry_task_update.returncode:
            raise AssertionError(dry_task_update.stderr)
        if (root / ".wigtn/workgraph.json").read_text(encoding="utf-8") != after_plan:
            raise AssertionError("CLI task update dry-run mutated WorkGraph")
        cases += 1
        applied_task_update = run_cli(
            root,
            "task",
            "update",
            first_task,
            "--title",
            "CLI refined",
            "--risk",
            "high",
            "--path",
            "src/cli.py",
            "--apply",
        )
        if applied_task_update.returncode:
            raise AssertionError(applied_task_update.stderr)
        cases += 1
        revision_after_update = json.loads(
            (root / ".wigtn/workgraph.json").read_text(encoding="utf-8")
        )["revision"]
        applied_dependency = run_cli(
            root,
            "task",
            "depend",
            second_task,
            "--on",
            first_task,
            "--expected-revision",
            str(revision_after_update),
            "--apply",
        )
        if applied_dependency.returncode:
            raise AssertionError(applied_dependency.stderr)
        cases += 1
        stale_update = run_cli(
            root,
            "task",
            "update",
            second_task,
            "--title",
            "Should fail",
            "--expected-revision",
            str(revision_after_update),
            "--apply",
        )
        if stale_update.returncode != 2 or "revision conflict" not in stale_update.stdout:
            raise AssertionError("CLI stale revision was not rejected")
        cases += 1
        for command in ("status", "next", "doctor"):
            completed = run_cli(root, command)
            if completed.returncode:
                raise AssertionError(f"CLI {command}: {completed.stderr}")
            json.loads(completed.stdout)
            cases += 1
        source.write_text(
            "## Functional Requirements\n\n"
            "- FR-01: Encrypt preference.\n"
            "- FR-02: Display preference.\n",
            encoding="utf-8",
        )
        drift_check = run_cli(root, "diff", "--check")
        if drift_check.returncode != 1:
            raise AssertionError("CLI diff --check did not report source drift")
        cases += 1
        before_drift_apply = json.loads(
            (root / ".wigtn/workgraph.json").read_text(encoding="utf-8")
        )
        drift_apply = run_cli(root, "diff", "--apply")
        if drift_apply.returncode:
            raise AssertionError(drift_apply.stderr)
        after_drift_apply = json.loads(
            (root / ".wigtn/workgraph.json").read_text(encoding="utf-8")
        )
        if after_drift_apply["revision"] != before_drift_apply["revision"] + 1:
            raise AssertionError("CLI diff --apply did not advance one revision")
        cases += 1
        repeated_drift = run_cli(root, "diff", "--apply")
        if repeated_drift.returncode:
            raise AssertionError(repeated_drift.stderr)
        after_repeated = json.loads(
            (root / ".wigtn/workgraph.json").read_text(encoding="utf-8")
        )
        if after_repeated != after_drift_apply:
            raise AssertionError("CLI repeated drift apply was not idempotent")
        cases += 1

    if cases < 30:
        raise AssertionError(f"expected at least 30 cases, ran {cases}")
    print(f"WorkGraph contract: PASS ({cases} deterministic cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
