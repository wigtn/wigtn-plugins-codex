#!/usr/bin/env python3
"""WIGTN lifecycle CLI: deterministic WorkGraph planning and inspection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from workgraph_core import (
    atomic_write_json,
    empty_graph,
    graph_write_lock,
    inspect_drift,
    merge_import,
    plan_graph,
    read_json,
    ready_tasks,
    repository_relative,
    set_task_dependency,
    summary,
    update_task,
    validate_graph,
)


SCRIPT_DIR = Path(__file__).resolve().parent
IMPORTER = SCRIPT_DIR / "import-requirements.py"


def emit(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    elif isinstance(value, str):
        print(value)
    else:
        print(json.dumps(value, ensure_ascii=False, indent=2))


def root_path(args: argparse.Namespace) -> Path:
    return args.root.resolve()


def wigtn_dir(root: Path) -> Path:
    return root / ".wigtn"


def graph_path(root: Path) -> Path:
    return wigtn_dir(root) / "workgraph.json"


def project_path(root: Path) -> Path:
    return wigtn_dir(root) / "project.json"


def evidence_path(root: Path) -> Path:
    return wigtn_dir(root) / "evidence.json"


def require_graph(root: Path) -> dict[str, Any]:
    path = graph_path(root)
    if not path.is_file():
        raise ValueError("WorkGraph missing; run `wigtn.py init --apply` first")
    graph = read_json(path)
    errors = validate_graph(graph)
    if errors:
        raise ValueError("invalid WorkGraph:\n" + "\n".join(errors))
    return graph


def default_project() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "requirement_sources": [],
        "verification_commands": [],
        "protected_paths": [".git"],
        "prd_profile": "auto",
        "evidence_path": ".wigtn/evidence.json",
        "lifecycle_profile": "flow",
        "workgraph_path": ".wigtn/workgraph.json",
    }


def default_evidence() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "artifact_type": "acceptance",
        "source_artifacts": [],
        "requirements": [],
        "checks": [],
        "release_authority": {
            "source_request": "",
            "commit": False,
            "push": False,
            "pull_request": False,
            "deploy": False,
        },
        "external_actions": [],
        "limitations": ["No implementation or checks have been inspected."],
        "metadata": {"generator": "wigtn-cli/1.0"},
    }


def command_init(args: argparse.Namespace) -> int:
    root = root_path(args)
    targets = {
        project_path(root): default_project(),
        graph_path(root): empty_graph(root.name),
        evidence_path(root): default_evidence(),
    }
    existing = [repository_relative(path, root) for path in targets if path.exists()]
    plan = {
        "operation": "init",
        "apply": args.apply,
        "create": [
            repository_relative(path, root)
            for path in targets
            if not path.exists()
        ],
        "preserve": existing,
    }
    emit(plan, args.json)
    if not args.apply:
        return 0
    for path, document in targets.items():
        if not path.exists():
            atomic_write_json(path, document)
    return 0


def run_importer(root: Path, sources: list[Path]) -> dict[str, Any]:
    command = [
        sys.executable,
        str(IMPORTER),
        *[str(path) for path in sources],
        "--root",
        str(root),
    ]
    completed = subprocess.run(
        command,
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise ValueError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout)


def command_import(args: argparse.Namespace) -> int:
    root = root_path(args)
    graph = require_graph(root)
    sources = [(root / path).resolve() for path in args.sources]
    for source in sources:
        repository_relative(source, root)
        if not source.is_file():
            raise ValueError(f"{source}: source does not exist")
    updated = graph
    for source in sources:
        imported = run_importer(root, [source])
        updated = merge_import(updated, imported, [source], root)
    errors = validate_graph(updated)
    if errors:
        raise ValueError("import produced invalid WorkGraph:\n" + "\n".join(errors))
    result = {
        "operation": "import",
        "apply": args.apply,
        "sources": [repository_relative(path, root) for path in sources],
        "requirements": len(updated["requirements"]),
        "revision": updated["revision"],
    }
    emit(result, args.json)
    if args.apply:
        atomic_write_json(graph_path(root), updated)
    return 0


def command_plan(args: argparse.Namespace) -> int:
    root = root_path(args)
    graph = require_graph(root)
    context = project_path(root)
    if context.is_file():
        validation = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "validate-project-context.py"),
             str(context), "--json"],
            text=True, capture_output=True, check=False,
        )
        if validation.returncode:
            raise ValueError(
                "invalid project context: "
                + (validation.stdout.strip() or validation.stderr.strip())
            )
        project = read_json(context)
    else:
        project = default_project()
    updated = plan_graph(
        graph,
        verification_commands=list(project.get("verification_commands", [])),
        protected_paths=list(project.get("protected_paths", [])),
    )
    errors = validate_graph(updated)
    if errors:
        raise ValueError("plan produced invalid WorkGraph:\n" + "\n".join(errors))
    created = sorted(
        {item["id"] for item in updated["tasks"]}
        - {item["id"] for item in graph["tasks"]}
    )
    emit(
        {
            "operation": "plan",
            "apply": args.apply,
            "created_task_ids": created,
            "revision": updated["revision"],
        },
        args.json,
    )
    if args.apply:
        atomic_write_json(graph_path(root), updated)
    return 0


def command_status(args: argparse.Namespace) -> int:
    emit(summary(require_graph(root_path(args))), args.json)
    return 0


def command_next(args: argparse.Namespace) -> int:
    tasks = ready_tasks(require_graph(root_path(args)))
    emit(
        {
            "count": len(tasks),
            "tasks": tasks,
        },
        args.json,
    )
    return 0


def command_diff(args: argparse.Namespace) -> int:
    root = root_path(args)
    graph = require_graph(root)
    updated, drift = inspect_drift(graph, root)
    stale_before = {
        item["id"]
        for collection in ("requirements", "artifacts", "tasks", "checks")
        for item in graph.get(collection, [])
        if item.get("status") == "stale"
    }
    stale_after = {
        item["id"]
        for collection in ("requirements", "artifacts", "tasks", "checks")
        for item in updated.get(collection, [])
        if item.get("status") == "stale"
    }
    emit(
        {
            "operation": "diff",
            "apply": args.apply,
            "source_drift": drift,
            "newly_stale_ids": sorted(stale_after - stale_before),
        },
        args.json,
    )
    if args.apply and (drift or stale_after != stale_before):
        atomic_write_json(graph_path(root), updated)
    return 1 if drift and args.check else 0


def command_doctor(args: argparse.Namespace) -> int:
    root = root_path(args)
    graph = require_graph(root)
    _, drift = inspect_drift(graph, root)
    issues: list[str] = []
    if drift:
        issues.extend(
            f"source drift: {item['path']} ({item['actual']})" for item in drift
        )
    project = project_path(root)
    evidence = evidence_path(root)
    if not project.is_file():
        issues.append(".wigtn/project.json is missing")
    if not evidence.is_file():
        issues.append(".wigtn/evidence.json is missing")
    emit({"healthy": not issues, "issues": issues}, args.json)
    return 1 if issues else 0


def task_view(graph: dict, task_ids: list[str]) -> tuple[dict, dict]:
    """Project an already validated graph; retain complete records and dependencies."""
    tasks = {task["id"]: task for task in graph["tasks"]}
    unknown = sorted(set(task_ids) - tasks.keys())
    if unknown:
        raise ValueError("unknown task IDs: " + ", ".join(unknown))
    included = set(task_ids)
    pending = list(included)
    while pending:
        for dependency in tasks[pending.pop()]["depends_on"]:
            if dependency not in included:
                included.add(dependency)
                pending.append(dependency)
    selected_tasks = [task for task in graph["tasks"] if task["id"] in included]
    artifact_ids = {key for task in selected_tasks for key in task["artifact_ids"]}
    artifacts = [item for item in graph["artifacts"] if item["id"] in artifact_ids]
    check_ids = {key for task in selected_tasks for key in task["check_ids"]}
    checks = [item for item in graph["checks"]
              if item["id"] in check_ids or included.intersection(item["task_ids"])]
    requirement_ids = {key for item in selected_tasks + artifacts + checks
                       for key in item["requirement_ids"]}
    requirements = [item for item in graph["requirements"] if item["id"] in requirement_ids]
    source_ids = {item["source_id"] for item in requirements}
    view = {
        "tasks": selected_tasks, "artifacts": artifacts, "checks": checks,
        "requirements": requirements,
        "sources": [item for item in graph["sources"] if item["id"] in source_ids],
    }
    selection = {
        "requested_task_ids": sorted(set(task_ids)),
        "included_task_ids": [task["id"] for task in selected_tasks],
        "records": {key: {"included": len(items), "total": len(graph[key]),
                           "omitted": len(graph[key]) - len(items)}
                    for key, items in view.items()},
        "boundary": "Task records include transitive dependencies, not dependents. Shared check references may name omitted tasks. Validation, source drift, summary and release gates cover the whole graph; next_tasks covers this selection. Use inspect without --task for the full view.",
    }
    return view, selection


def command_inspect(args: argparse.Namespace) -> int:
    """Read-only validated, drift-adjusted view; never execute saved commands."""
    root = root_path(args)
    graph = require_graph(root)
    current, drift = inspect_drift(graph, root)
    validations = {}
    for label, path, script in (
        ("project", project_path(root), "validate-project-context.py"),
        ("evidence", evidence_path(root), "validate-evidence.py"),
    ):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / script), str(path)],
            text=True, capture_output=True, check=False,
        )
        validations[label] = {
            "valid": result.returncode == 0,
            "exit_code": result.returncode,
            "details": result.stdout + result.stderr,
        }
    valid = all(item["valid"] for item in validations.values())
    current_summary = summary(current)
    if not valid:
        current_summary["next_task_ids"] = []
    payload = {
        "operation": "inspect", "read_only": True,
        "saved_revision": graph["revision"],
        "valid_artifacts": valid, "fresh": not drift,
        "validations": validations, "source_drift": drift,
        "summary": current_summary, "sources": current["sources"],
        "requirements": current["requirements"],
        "tasks": current["tasks"], "checks": current["checks"],
        "release_gates": current["release_gates"],
        "next_tasks": ready_tasks(current) if valid else [],
        "verification_boundary": "Saved evidence validity is structural, not proof of executed behavior. Commands are not executed. Drift is previewed, not persisted.",
    }
    if args.task:
        view, selection = task_view(current, args.task)
        payload.update(view)
        payload["selection"] = selection
        included = set(selection["included_task_ids"])
        payload["next_tasks"] = [task for task in payload["next_tasks"] if task["id"] in included]
    emit(payload, args.json)
    return 0 if valid and not drift else 1


def command_task_update(args: argparse.Namespace) -> int:
    root = root_path(args)
    graph = require_graph(root)
    updated = update_task(
        graph,
        args.task_id,
        title=args.title,
        risk=args.risk,
        intended_paths=args.path if args.path is not None else None,
        replace_paths=args.replace_paths,
        expected_revision=args.expected_revision,
    )
    changed = updated != graph
    emit(
        {
            "operation": "task-update",
            "apply": args.apply,
            "task_id": args.task_id,
            "changed": changed,
            "revision": updated["revision"],
        },
        args.json,
    )
    if args.apply and changed:
        atomic_write_json(graph_path(root), updated)
    return 0


def command_task_depend(args: argparse.Namespace) -> int:
    root = root_path(args)
    graph = require_graph(root)
    updated = set_task_dependency(
        graph,
        args.task_id,
        args.on,
        remove=args.remove,
        expected_revision=args.expected_revision,
    )
    changed = updated != graph
    emit(
        {
            "operation": (
                "task-dependency-remove"
                if args.remove
                else "task-dependency-add"
            ),
            "apply": args.apply,
            "task_id": args.task_id,
            "dependency_id": args.on,
            "changed": changed,
            "revision": updated["revision"],
        },
        args.json,
    )
    if args.apply and changed:
        atomic_write_json(graph_path(root), updated)
    return 0


def parser() -> argparse.ArgumentParser:
    root_parser = argparse.ArgumentParser(description=__doc__)
    root_parser.add_argument("--root", type=Path, default=Path.cwd())
    root_parser.add_argument("--json", action="store_true")
    commands = root_parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--apply", action="store_true")
    init.set_defaults(handler=command_init)
    import_command = commands.add_parser("import")
    import_command.add_argument("sources", nargs="+", type=Path, help="source paths relative to --root, or absolute paths inside it")
    import_command.add_argument("--apply", action="store_true")
    import_command.set_defaults(handler=command_import)
    plan = commands.add_parser("plan")
    plan.add_argument("--apply", action="store_true")
    plan.set_defaults(handler=command_plan)
    status = commands.add_parser("status")
    status.set_defaults(handler=command_status)
    next_command = commands.add_parser("next")
    next_command.set_defaults(handler=command_next)
    diff = commands.add_parser("diff")
    diff.add_argument("--apply", action="store_true")
    diff.add_argument("--check", action="store_true")
    diff.set_defaults(handler=command_diff)
    doctor = commands.add_parser("doctor")
    doctor.set_defaults(handler=command_doctor)
    inspect = commands.add_parser("inspect", help="validated state, drift preview and eligible tasks; read-only")
    inspect.add_argument("--task", action="append", metavar="TASK-ID",
                         help="show this task and its transitive dependencies; repeat for multiple tasks; global validation and drift are retained")
    inspect.set_defaults(handler=command_inspect)
    task = commands.add_parser("task")
    task_commands = task.add_subparsers(dest="task_command", required=True)
    task_update = task_commands.add_parser("update")
    task_update.add_argument("task_id")
    task_update.add_argument("--title")
    task_update.add_argument("--risk", choices=("low", "medium", "high", "critical"))
    task_update.add_argument("--path", action="append")
    task_update.add_argument("--replace-paths", action="store_true")
    task_update.add_argument("--expected-revision", type=int)
    task_update.add_argument("--apply", action="store_true")
    task_update.set_defaults(handler=command_task_update)
    task_depend = task_commands.add_parser("depend")
    task_depend.add_argument("task_id")
    task_depend.add_argument("--on", required=True)
    task_depend.add_argument("--remove", action="store_true")
    task_depend.add_argument("--expected-revision", type=int)
    task_depend.add_argument("--apply", action="store_true")
    task_depend.set_defaults(handler=command_task_depend)
    return root_parser


def main() -> int:
    args = parser().parse_args()
    try:
        if getattr(args, "apply", False):
            with graph_write_lock(root_path(args)):
                return args.handler(args)
        return args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        if args.json:
            print(
                json.dumps(
                    {"error": str(exc), "command": args.command},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
