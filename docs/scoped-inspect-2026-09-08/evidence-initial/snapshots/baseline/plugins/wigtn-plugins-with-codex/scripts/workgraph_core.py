#!/usr/bin/env python3
"""Dependency-free WorkGraph model, validation, planning, and drift logic."""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any, Iterable


SCHEMA_VERSION = "1.0"
REQUIREMENT_ID = re.compile(r"^[A-Z][A-Z0-9_]*(?:-[A-Z0-9_]+)+$")
SOURCE_ID = re.compile(r"^SRC-[A-Z0-9_-]+$")
ARTIFACT_ID = re.compile(r"^ART-[A-Z0-9_-]+$")
TASK_ID = re.compile(r"^TASK-[A-Z0-9_-]+$")
CHECK_ID = re.compile(r"^CHK-[0-9]{2,}$")
GATE_ID = re.compile(r"^GATE-[A-Z0-9_-]+$")
GRAPH_ID = re.compile(r"^WG-[A-Z0-9_-]+$")

REQUIREMENT_STATUSES = {"active", "stale", "retired"}
ARTIFACT_STATUSES = {"draft", "ready", "stale", "retired"}
TASK_STATUSES = {
    "draft",
    "ready",
    "in-progress",
    "blocked",
    "implemented",
    "verified",
    "stale",
    "retired",
}
CHECK_STATUSES = {"pending", "passed", "failed", "skipped", "stale"}
GATE_STATUSES = {"blocked", "ready", "released", "stale"}
RISKS = {"low", "medium", "high", "critical"}
ACTIONS = {"commit", "push", "pull_request", "deploy"}


def digest_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def slug(value: str, *, fallback: str = "PROJECT") -> str:
    normalized = re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")
    return normalized or fallback


def stable_token(prefix: str, value: str, size: int = 12) -> str:
    return f"{prefix}-{sha256(value.encode('utf-8')).hexdigest()[:size].upper()}"


def empty_graph(graph_name: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "graph_id": f"WG-{slug(graph_name)}",
        "revision": 0,
        "sources": [],
        "requirements": [],
        "artifacts": [],
        "tasks": [],
        "checks": [],
        "release_gates": [],
        "metadata": {
            "generator": "wigtn-workgraph/1.0",
            "last_operation": "init",
        },
    }


def repository_relative(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"{path}: path must stay inside repository root") from exc


def safe_repo_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    return not (
        candidate.is_absolute()
        or ".." in candidate.parts
        or re.match(r"^[A-Za-z]:/", normalized)
        or "://" in normalized
    )


def read_json(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path}: JSON root must be an object")
    return document


def atomic_write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.replace(path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


@contextmanager
def graph_write_lock(root: Path):
    """Serialize cooperating CLI transactions, including their initial read.

    Keep the lock inode in place: unlinking it could split waiting writers
    across different locks. OS locks are released if a writer process dies.
    Direct editors do not participate in this advisory lock.
    """
    directory = root / ".wigtn"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".write.lock").open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            if handle.seek(0, os.SEEK_END) == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class WorkGraphValidator:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def object(
        self,
        value: Any,
        path: str,
        required: set[str],
        allowed: set[str] | None = None,
    ) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            self.error(path, "must be an object")
            return None
        missing = sorted(required - set(value))
        extra = sorted(set(value) - (allowed or required))
        if missing:
            self.error(path, "missing keys: " + ", ".join(missing))
        if extra:
            self.error(path, "unknown keys: " + ", ".join(extra))
        return value

    def array(self, value: Any, path: str) -> list[Any]:
        if not isinstance(value, list):
            self.error(path, "must be an array")
            return []
        return value

    def identifier(
        self, value: Any, path: str, pattern: re.Pattern[str], seen: set[str]
    ) -> str | None:
        if not isinstance(value, str) or pattern.fullmatch(value) is None:
            self.error(path, f"invalid identifier {value!r}")
            return None
        if value in seen:
            self.error(path, f"duplicate identifier {value}")
        seen.add(value)
        return value

    def string(self, value: Any, path: str, *, nullable: bool = False) -> None:
        if nullable and value is None:
            return
        if not isinstance(value, str) or not value.strip():
            self.error(path, "must be a non-empty string")

    def path(self, value: Any, path: str, *, nullable: bool = False) -> None:
        if nullable and value is None:
            return
        if not safe_repo_path(value):
            self.error(path, "must be a safe repository-relative path")

    def string_ids(
        self,
        value: Any,
        path: str,
        known: set[str],
        *,
        minimum: int = 0,
    ) -> list[str]:
        items = self.array(value, path)
        if len(items) < minimum:
            self.error(path, f"must contain at least {minimum} item(s)")
        if len(items) != len(set(item for item in items if isinstance(item, str))):
            self.error(path, "must not contain duplicate IDs")
        for index, item in enumerate(items):
            if not isinstance(item, str):
                self.error(f"{path}[{index}]", "must be a string")
            elif item not in known:
                self.error(f"{path}[{index}]", f"unknown reference {item}")
        return [item for item in items if isinstance(item, str)]

    def validate(self, document: Any) -> list[str]:
        required = {
            "schema_version",
            "graph_id",
            "revision",
            "sources",
            "requirements",
            "artifacts",
            "tasks",
            "checks",
            "release_gates",
            "metadata",
        }
        root = self.object(document, "$", required)
        if root is None:
            return self.errors
        if root.get("schema_version") != SCHEMA_VERSION:
            self.error("$.schema_version", "must equal '1.0'")
        if not isinstance(root.get("revision"), int) or isinstance(
            root.get("revision"), bool
        ) or root.get("revision", -1) < 0:
            self.error("$.revision", "must be a non-negative integer")
        if not isinstance(root.get("metadata"), dict):
            self.error("$.metadata", "must be an object")
        graph_seen: set[str] = set()
        self.identifier(root.get("graph_id"), "$.graph_id", GRAPH_ID, graph_seen)

        source_ids = self.validate_sources(root.get("sources"))
        requirement_ids = self.validate_requirements(
            root.get("requirements"), source_ids
        )
        artifact_ids = self.validate_artifacts(
            root.get("artifacts"), requirement_ids
        )
        task_ids = {
            item.get("id")
            for item in self.array(root.get("tasks"), "$.tasks")
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        check_ids = {
            item.get("id")
            for item in self.array(root.get("checks"), "$.checks")
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        tasks = self.validate_tasks(
            root.get("tasks"),
            requirement_ids,
            artifact_ids,
            task_ids,
            check_ids,
        )
        checks = self.validate_checks(
            root.get("checks"), task_ids, requirement_ids
        )
        self.validate_task_semantics(tasks, checks)
        self.validate_gates(
            root.get("release_gates"), task_ids, requirement_ids, tasks
        )
        self.validate_acyclic(tasks)
        return self.errors

    def validate_sources(self, value: Any) -> set[str]:
        seen: set[str] = set()
        paths: set[str] = set()
        for index, item in enumerate(self.array(value, "$.sources")):
            path = f"$.sources[{index}]"
            source = self.object(
                item, path, {"id", "kind", "path", "sha256"}
            )
            if source is None:
                continue
            self.identifier(source.get("id"), f"{path}.id", SOURCE_ID, seen)
            self.string(source.get("kind"), f"{path}.kind")
            self.path(source.get("path"), f"{path}.path")
            source_path = source.get("path")
            if isinstance(source_path, str):
                if source_path in paths:
                    self.error(f"{path}.path", f"duplicate source path {source_path}")
                paths.add(source_path)
            digest = source.get("sha256")
            if not isinstance(digest, str) or re.fullmatch(
                r"[0-9a-f]{64}", digest
            ) is None:
                self.error(f"{path}.sha256", "must be a lowercase SHA-256")
        return seen

    def validate_requirements(
        self, value: Any, source_ids: set[str]
    ) -> set[str]:
        seen: set[str] = set()
        for index, item in enumerate(self.array(value, "$.requirements")):
            path = f"$.requirements[{index}]"
            requirement = self.object(
                item,
                path,
                {"id", "source_id", "text", "source_sha256", "status"},
            )
            if requirement is None:
                continue
            self.identifier(
                requirement.get("id"), f"{path}.id", REQUIREMENT_ID, seen
            )
            source_id = requirement.get("source_id")
            if source_id not in source_ids:
                self.error(f"{path}.source_id", f"unknown source {source_id!r}")
            self.string(requirement.get("text"), f"{path}.text")
            digest = requirement.get("source_sha256")
            if not isinstance(digest, str) or re.fullmatch(
                r"[0-9a-f]{64}", digest
            ) is None:
                self.error(f"{path}.source_sha256", "must be a lowercase SHA-256")
            if requirement.get("status") not in REQUIREMENT_STATUSES:
                self.error(f"{path}.status", "invalid requirement status")
        return seen

    def validate_artifacts(
        self, value: Any, requirement_ids: set[str]
    ) -> set[str]:
        seen: set[str] = set()
        for index, item in enumerate(self.array(value, "$.artifacts")):
            path = f"$.artifacts[{index}]"
            artifact = self.object(
                item,
                path,
                {"id", "kind", "path", "requirement_ids", "status"},
            )
            if artifact is None:
                continue
            self.identifier(artifact.get("id"), f"{path}.id", ARTIFACT_ID, seen)
            self.string(artifact.get("kind"), f"{path}.kind")
            self.path(artifact.get("path"), f"{path}.path")
            self.string_ids(
                artifact.get("requirement_ids"),
                f"{path}.requirement_ids",
                requirement_ids,
            )
            if artifact.get("status") not in ARTIFACT_STATUSES:
                self.error(f"{path}.status", "invalid artifact status")
        return seen

    def validate_tasks(
        self,
        value: Any,
        requirement_ids: set[str],
        artifact_ids: set[str],
        task_ids: set[str],
        check_ids: set[str],
    ) -> dict[str, dict[str, Any]]:
        seen: set[str] = set()
        tasks: dict[str, dict[str, Any]] = {}
        required = {
            "id",
            "title",
            "requirement_ids",
            "artifact_ids",
            "depends_on",
            "intended_paths",
            "protected_paths",
            "risk",
            "status",
            "check_ids",
            "blocker",
            "evidence_refs",
        }
        for index, item in enumerate(self.array(value, "$.tasks")):
            path = f"$.tasks[{index}]"
            task = self.object(item, path, required)
            if task is None:
                continue
            task_id = self.identifier(task.get("id"), f"{path}.id", TASK_ID, seen)
            if task_id:
                tasks[task_id] = task
            self.string(task.get("title"), f"{path}.title")
            self.string_ids(
                task.get("requirement_ids"),
                f"{path}.requirement_ids",
                requirement_ids,
                minimum=1,
            )
            self.string_ids(
                task.get("artifact_ids"),
                f"{path}.artifact_ids",
                artifact_ids,
            )
            dependencies = self.string_ids(
                task.get("depends_on"), f"{path}.depends_on", task_ids
            )
            if task_id in dependencies:
                self.error(f"{path}.depends_on", "task cannot depend on itself")
            self.string_ids(
                task.get("check_ids"), f"{path}.check_ids", check_ids
            )
            for field in ("intended_paths", "protected_paths", "evidence_refs"):
                values = self.array(task.get(field), f"{path}.{field}")
                if len(values) != len(set(v for v in values if isinstance(v, str))):
                    self.error(f"{path}.{field}", "must not contain duplicates")
                for value_index, item_path in enumerate(values):
                    self.path(item_path, f"{path}.{field}[{value_index}]")
            if task.get("risk") not in RISKS:
                self.error(f"{path}.risk", "invalid risk")
            status = task.get("status")
            if status not in TASK_STATUSES:
                self.error(f"{path}.status", "invalid task status")
            blocker = task.get("blocker")
            if blocker is not None and (
                not isinstance(blocker, str) or not blocker.strip()
            ):
                self.error(f"{path}.blocker", "must be null or a non-empty string")
            if status == "blocked" and blocker is None:
                self.error(f"{path}.blocker", "blocked tasks require a blocker")
            if status != "blocked" and blocker is not None:
                self.error(f"{path}.blocker", "only blocked tasks may have a blocker")
        return tasks

    def validate_checks(
        self,
        value: Any,
        task_ids: set[str],
        requirement_ids: set[str],
    ) -> dict[str, dict[str, Any]]:
        seen: set[str] = set()
        checks: dict[str, dict[str, Any]] = {}
        required = {
            "id",
            "task_ids",
            "requirement_ids",
            "command",
            "status",
            "evidence_ref",
        }
        for index, item in enumerate(self.array(value, "$.checks")):
            path = f"$.checks[{index}]"
            check = self.object(item, path, required)
            if check is None:
                continue
            check_id = self.identifier(
                check.get("id"), f"{path}.id", CHECK_ID, seen
            )
            if check_id:
                checks[check_id] = check
            self.string_ids(
                check.get("task_ids"), f"{path}.task_ids", task_ids, minimum=1
            )
            self.string_ids(
                check.get("requirement_ids"),
                f"{path}.requirement_ids",
                requirement_ids,
                minimum=1,
            )
            command = check.get("command")
            if command is not None and (
                not isinstance(command, str) or not command.strip()
            ):
                self.error(f"{path}.command", "must be null or non-empty")
            status = check.get("status")
            if status not in CHECK_STATUSES:
                self.error(f"{path}.status", "invalid check status")
            self.path(
                check.get("evidence_ref"),
                f"{path}.evidence_ref",
                nullable=True,
            )
            if status == "passed" and check.get("evidence_ref") is None:
                self.error(
                    f"{path}.evidence_ref",
                    "passed checks require an evidence reference",
                )
            if status in {"pending", "stale"} and check.get("evidence_ref") is not None:
                self.error(
                    f"{path}.evidence_ref",
                    f"{status} checks cannot retain evidence",
                )
        return checks

    def validate_task_semantics(
        self,
        tasks: dict[str, dict[str, Any]],
        checks: dict[str, dict[str, Any]],
    ) -> None:
        for task_id, task in tasks.items():
            status = task.get("status")
            dependencies = [
                tasks[item]
                for item in task.get("depends_on", [])
                if item in tasks
            ]
            if status in {"ready", "in-progress", "implemented", "verified"} and any(
                dependency.get("status") != "verified"
                for dependency in dependencies
            ):
                self.error(
                    f"$.tasks[{task_id}].depends_on",
                    "active task requires all dependencies to be verified",
                )
            linked_checks = [
                checks[item]
                for item in task.get("check_ids", [])
                if item in checks
            ]
            if status == "verified":
                if not linked_checks or not any(
                    check.get("status") == "passed" for check in linked_checks
                ):
                    self.error(
                        f"$.tasks[{task_id}].check_ids",
                        "verified task needs a linked passing check",
                    )
                if not task.get("evidence_refs"):
                    self.error(
                        f"$.tasks[{task_id}].evidence_refs",
                        "verified task needs evidence",
                    )
            for check in linked_checks:
                if task_id not in check.get("task_ids", []):
                    self.error(
                        f"$.tasks[{task_id}].check_ids",
                        f"check {check.get('id')} does not link back to task",
                    )

    def validate_gates(
        self,
        value: Any,
        task_ids: set[str],
        requirement_ids: set[str],
        tasks: dict[str, dict[str, Any]],
    ) -> None:
        seen: set[str] = set()
        required = {
            "id",
            "requires_task_ids",
            "requires_requirement_ids",
            "status",
            "authority_actions",
        }
        for index, item in enumerate(self.array(value, "$.release_gates")):
            path = f"$.release_gates[{index}]"
            gate = self.object(item, path, required)
            if gate is None:
                continue
            self.identifier(gate.get("id"), f"{path}.id", GATE_ID, seen)
            required_tasks = self.string_ids(
                gate.get("requires_task_ids"),
                f"{path}.requires_task_ids",
                task_ids,
            )
            self.string_ids(
                gate.get("requires_requirement_ids"),
                f"{path}.requires_requirement_ids",
                requirement_ids,
            )
            status = gate.get("status")
            if status not in GATE_STATUSES:
                self.error(f"{path}.status", "invalid gate status")
            actions = self.array(
                gate.get("authority_actions"), f"{path}.authority_actions"
            )
            if len(actions) != len(set(a for a in actions if isinstance(a, str))):
                self.error(f"{path}.authority_actions", "must not contain duplicates")
            for action_index, action in enumerate(actions):
                if action not in ACTIONS:
                    self.error(
                        f"{path}.authority_actions[{action_index}]",
                        f"invalid action {action!r}",
                    )
            if status in {"ready", "released"} and any(
                tasks.get(task_id, {}).get("status") != "verified"
                for task_id in required_tasks
            ):
                self.error(
                    f"{path}.status",
                    "ready or released gate requires verified tasks",
                )
            if status == "released" and not actions:
                self.error(
                    f"{path}.authority_actions",
                    "released gate must record explicit authority actions",
                )

    def validate_acyclic(self, tasks: dict[str, dict[str, Any]]) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                self.error("$.tasks", f"dependency cycle includes {task_id}")
                return
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency in tasks.get(task_id, {}).get("depends_on", []):
                if dependency in tasks:
                    visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in tasks:
            visit(task_id)


def validate_graph(document: Any) -> list[str]:
    return WorkGraphValidator().validate(document)


def source_record(path: Path, root: Path, kind: str) -> dict[str, str]:
    relative = repository_relative(path, root)
    return {
        "id": stable_token("SRC", relative),
        "kind": kind,
        "path": relative,
        "sha256": digest_file(path),
    }


def merge_import(
    graph: dict[str, Any],
    imported: dict[str, Any],
    source_paths: Iterable[Path],
    root: Path,
) -> dict[str, Any]:
    updated = deepcopy(graph)
    before = deepcopy(graph)
    sources_by_path = {
        item["path"]: item for item in updated.get("sources", [])
    }
    source_records: list[dict[str, str]] = []
    source_formats = imported.get("metadata", {}).get("source_formats", [])
    for index, path in enumerate(source_paths):
        kind = (
            str(source_formats[index])
            if index < len(source_formats)
            else "generic"
        )
        record = source_record(path, root, kind)
        sources_by_path[record["path"]] = record
        source_records.append(record)
    updated["sources"] = sorted(sources_by_path.values(), key=lambda item: item["id"])

    old_requirements = {
        item["id"]: item for item in updated.get("requirements", [])
    }
    imported_ids: set[str] = set()
    changed_ids: set[str] = set()
    for item in imported.get("requirements", []):
        requirement_id = item["id"]
        imported_ids.add(requirement_id)
        source = next(
            (
                candidate
                for candidate in source_records
                if requirement_id in _requirements_for_source(
                    imported, candidate["path"]
                )
            ),
            source_records[0],
        )
        previous = old_requirements.get(requirement_id)
        text = item["text"]
        status = "active"
        if previous and (
            previous.get("text") != text
            or previous.get("source_sha256") != source["sha256"]
        ):
            status = "stale"
            changed_ids.add(requirement_id)
        old_requirements[requirement_id] = {
            "id": requirement_id,
            "source_id": source["id"],
            "text": text,
            "source_sha256": source["sha256"],
            "status": status,
        }

    imported_source_ids = {item["id"] for item in source_records}
    for requirement in old_requirements.values():
        if (
            requirement.get("source_id") in imported_source_ids
            and requirement["id"] not in imported_ids
        ):
            requirement["status"] = "retired"
    updated["requirements"] = sorted(
        old_requirements.values(), key=lambda item: item["id"]
    )
    propagate_stale(updated)
    for requirement in updated["requirements"]:
        if requirement["id"] in changed_ids:
            requirement["status"] = "active"
    if _state_payload(updated) != _state_payload(before):
        updated["revision"] = int(graph.get("revision", 0)) + 1
        updated.setdefault("metadata", {})["last_operation"] = "import"
    else:
        updated = before
    return updated


def _requirements_for_source(
    imported: dict[str, Any], source_path: str
) -> set[str]:
    artifacts = imported.get("source_artifacts", [])
    if not any(item.get("path") == source_path for item in artifacts):
        return set()
    if len(artifacts) == 1:
        return {
            item["id"]
            for item in imported.get("requirements", [])
            if isinstance(item, dict) and "id" in item
        }
    return set()


def next_check_id(graph: dict[str, Any]) -> str:
    numbers = [
        int(item["id"].split("-", 1)[1])
        for item in graph.get("checks", [])
        if isinstance(item.get("id"), str) and CHECK_ID.fullmatch(item["id"])
    ]
    return f"CHK-{(max(numbers, default=0) + 1):02d}"


def plan_graph(
    graph: dict[str, Any],
    *,
    verification_commands: list[str],
    protected_paths: list[str],
) -> dict[str, Any]:
    updated = deepcopy(graph)
    before = deepcopy(graph)
    task_requirements = {
        requirement_id
        for task in updated.get("tasks", [])
        for requirement_id in task.get("requirement_ids", [])
        if task.get("status") != "retired"
    }
    command = verification_commands[0] if verification_commands else None
    for requirement in updated.get("requirements", []):
        if requirement["status"] != "active" or requirement["id"] in task_requirements:
            continue
        requirement_id = requirement["id"]
        task_id = stable_token("TASK", requirement_id)
        check_id = next_check_id(updated)
        updated["tasks"].append(
            {
                "id": task_id,
                "title": f"Implement {requirement_id}: {requirement['text']}",
                "requirement_ids": [requirement_id],
                "artifact_ids": [],
                "depends_on": [],
                "intended_paths": [],
                "protected_paths": sorted(set(protected_paths)),
                "risk": "medium",
                "status": "ready",
                "check_ids": [check_id],
                "blocker": None,
                "evidence_refs": [],
            }
        )
        updated["checks"].append(
            {
                "id": check_id,
                "task_ids": [task_id],
                "requirement_ids": [requirement_id],
                "command": command,
                "status": "pending",
                "evidence_ref": None,
            }
        )
    updated["tasks"] = sorted(updated["tasks"], key=lambda item: item["id"])
    updated["checks"] = sorted(updated["checks"], key=lambda item: item["id"])
    if _state_payload(updated) != _state_payload(before):
        updated["revision"] = int(graph.get("revision", 0)) + 1
        updated.setdefault("metadata", {})["last_operation"] = "plan"
    else:
        updated = before
    return updated


def require_revision(graph: dict[str, Any], expected: int | None) -> None:
    if expected is not None and graph.get("revision") != expected:
        raise ValueError(
            f"revision conflict: expected {expected}, "
            f"found {graph.get('revision')}"
        )


def update_task(
    graph: dict[str, Any],
    task_id: str,
    *,
    title: str | None = None,
    risk: str | None = None,
    intended_paths: list[str] | None = None,
    replace_paths: bool = False,
    expected_revision: int | None = None,
) -> dict[str, Any]:
    require_revision(graph, expected_revision)
    updated = deepcopy(graph)
    task = next(
        (item for item in updated.get("tasks", []) if item.get("id") == task_id),
        None,
    )
    if task is None:
        raise ValueError(f"unknown task {task_id}")
    if title is not None:
        if not title.strip():
            raise ValueError("task title must not be empty")
        task["title"] = title.strip()
    if risk is not None:
        if risk not in RISKS:
            raise ValueError(f"invalid task risk {risk!r}")
        task["risk"] = risk
    if intended_paths is not None:
        if any(not safe_repo_path(path) for path in intended_paths):
            raise ValueError("intended paths must be safe repository-relative paths")
        current = [] if replace_paths else list(task.get("intended_paths", []))
        task["intended_paths"] = sorted(set(current + intended_paths))
    if _state_payload(updated) == _state_payload(graph):
        return deepcopy(graph)
    errors = validate_graph(updated)
    if errors:
        raise ValueError("task update is invalid:\n" + "\n".join(errors))
    updated["revision"] = int(graph.get("revision", 0)) + 1
    updated.setdefault("metadata", {})["last_operation"] = "task-update"
    return updated


def set_task_dependency(
    graph: dict[str, Any],
    task_id: str,
    dependency_id: str,
    *,
    remove: bool = False,
    expected_revision: int | None = None,
) -> dict[str, Any]:
    require_revision(graph, expected_revision)
    updated = deepcopy(graph)
    tasks = {item["id"]: item for item in updated.get("tasks", [])}
    if task_id not in tasks:
        raise ValueError(f"unknown task {task_id}")
    if dependency_id not in tasks:
        raise ValueError(f"unknown dependency task {dependency_id}")
    if task_id == dependency_id:
        raise ValueError("task cannot depend on itself")
    task = tasks[task_id]
    dependencies = set(task.get("depends_on", []))
    if remove:
        dependencies.discard(dependency_id)
    else:
        dependencies.add(dependency_id)
        if (
            tasks[dependency_id].get("status") != "verified"
            and task.get("status") == "ready"
        ):
            task["status"] = "draft"
    task["depends_on"] = sorted(dependencies)
    if _state_payload(updated) == _state_payload(graph):
        return deepcopy(graph)
    errors = validate_graph(updated)
    if errors:
        raise ValueError("dependency update is invalid:\n" + "\n".join(errors))
    updated["revision"] = int(graph.get("revision", 0)) + 1
    updated.setdefault("metadata", {})["last_operation"] = (
        "task-dependency-remove" if remove else "task-dependency-add"
    )
    return updated


def propagate_stale(graph: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    stale_requirements = {
        item["id"]
        for item in graph.get("requirements", [])
        if item.get("status") in {"stale", "retired"}
    }
    stale_artifacts: set[str] = set()
    for artifact in graph.get("artifacts", []):
        if any(
            requirement_id in stale_requirements
            for requirement_id in artifact.get("requirement_ids", [])
        ):
            if artifact.get("status") not in {"stale", "retired"}:
                artifact["status"] = "stale"
                changed.append(artifact["id"])
            stale_artifacts.add(artifact["id"])
        elif artifact.get("status") == "stale":
            stale_artifacts.add(artifact["id"])

    stale_tasks: set[str] = set()
    progress = True
    while progress:
        progress = False
        for task in graph.get("tasks", []):
            should_stale = (
                any(
                    requirement_id in stale_requirements
                    for requirement_id in task.get("requirement_ids", [])
                )
                or any(
                    artifact_id in stale_artifacts
                    for artifact_id in task.get("artifact_ids", [])
                )
                or any(
                    dependency_id in stale_tasks
                    for dependency_id in task.get("depends_on", [])
                )
            )
            if should_stale and task.get("status") not in {"stale", "retired"}:
                task["status"] = "stale"
                task["blocker"] = None
                task["evidence_refs"] = []
                stale_tasks.add(task["id"])
                changed.append(task["id"])
                progress = True
            elif task.get("status") == "stale":
                stale_tasks.add(task["id"])

    stale_checks: set[str] = set()
    for check in graph.get("checks", []):
        if (
            any(task_id in stale_tasks for task_id in check.get("task_ids", []))
            or any(
                requirement_id in stale_requirements
                for requirement_id in check.get("requirement_ids", [])
            )
        ):
            if check.get("status") != "stale":
                check["status"] = "stale"
                check["evidence_ref"] = None
                changed.append(check["id"])
            stale_checks.add(check["id"])

    for gate in graph.get("release_gates", []):
        if (
            any(
                requirement_id in stale_requirements
                for requirement_id in gate.get("requires_requirement_ids", [])
            )
            or any(
                task_id in stale_tasks
                for task_id in gate.get("requires_task_ids", [])
            )
        ) and gate.get("status") != "stale":
            gate["status"] = "stale"
            changed.append(gate["id"])
    return sorted(changed)


def inspect_drift(graph: dict[str, Any], root: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    updated = deepcopy(graph)
    drift: list[dict[str, str]] = []
    sources = {item["id"]: item for item in updated.get("sources", [])}
    drifted_sources: set[str] = set()
    for source in sources.values():
        path = root / source["path"]
        if not path.is_file():
            actual = "missing"
        else:
            actual = digest_file(path)
        if actual != source["sha256"]:
            drifted_sources.add(source["id"])
            drift.append(
                {
                    "source_id": source["id"],
                    "path": source["path"],
                    "expected": source["sha256"],
                    "actual": actual,
                }
            )
    for requirement in updated.get("requirements", []):
        if (
            requirement.get("source_id") in drifted_sources
            and requirement.get("status") != "retired"
        ):
            requirement["status"] = "stale"
    changed = propagate_stale(updated)
    if changed:
        updated["revision"] = int(updated.get("revision", 0)) + 1
        updated.setdefault("metadata", {})["last_operation"] = "drift"
        updated["metadata"]["drifted_sources"] = sorted(drifted_sources)
    return updated, drift


def _state_payload(graph: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(graph)
    payload.pop("revision", None)
    payload.pop("metadata", None)
    return payload


def ready_tasks(graph: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = {item["id"]: item for item in graph.get("tasks", [])}
    return [
        task
        for task in graph.get("tasks", [])
        if task.get("status") in {"draft", "ready"}
        and all(
            tasks.get(dependency_id, {}).get("status") == "verified"
            for dependency_id in task.get("depends_on", [])
        )
        and all(
            requirement.get("status") == "active"
            for requirement_id in task.get("requirement_ids", [])
            for requirement in graph.get("requirements", [])
            if requirement.get("id") == requirement_id
        )
    ]


def summary(graph: dict[str, Any]) -> dict[str, Any]:
    def counts(items: list[dict[str, Any]]) -> dict[str, int]:
        result: dict[str, int] = {}
        for item in items:
            status = str(item.get("status", "unknown"))
            result[status] = result.get(status, 0) + 1
        return dict(sorted(result.items()))

    return {
        "graph_id": graph.get("graph_id"),
        "revision": graph.get("revision"),
        "sources": len(graph.get("sources", [])),
        "requirements": counts(graph.get("requirements", [])),
        "artifacts": counts(graph.get("artifacts", [])),
        "tasks": counts(graph.get("tasks", [])),
        "checks": counts(graph.get("checks", [])),
        "release_gates": counts(graph.get("release_gates", [])),
        "next_task_ids": [item["id"] for item in ready_tasks(graph)],
    }


def migrate(document: dict[str, Any], graph_name: str) -> dict[str, Any]:
    if document.get("schema_version") == SCHEMA_VERSION:
        errors = validate_graph(document)
        if errors:
            raise ValueError("current WorkGraph is invalid:\n" + "\n".join(errors))
        return deepcopy(document)
    if document.get("schema_version") != "0.1":
        raise ValueError(
            f"unsupported WorkGraph version {document.get('schema_version')!r}"
        )
    migrated = empty_graph(graph_name)
    legacy_requirements = document.get("requirements", [])
    synthetic_source = {
        "id": "SRC-LEGACY",
        "kind": "legacy-workgraph-0.1",
        "path": ".wigtn/legacy-workgraph.json",
        "sha256": digest_bytes(
            json.dumps(document, sort_keys=True).encode("utf-8")
        ),
    }
    migrated["sources"].append(synthetic_source)
    for index, item in enumerate(legacy_requirements, start=1):
        if isinstance(item, str):
            requirement_id = f"REQ-{index:02d}"
            text = item
        elif isinstance(item, dict):
            requirement_id = str(item.get("id") or f"REQ-{index:02d}").upper()
            text = str(item.get("text") or item.get("title") or "").strip()
        else:
            continue
        if REQUIREMENT_ID.fullmatch(requirement_id) is None or not text:
            raise ValueError(f"legacy requirement {index} cannot be migrated safely")
        migrated["requirements"].append(
            {
                "id": requirement_id,
                "source_id": synthetic_source["id"],
                "text": text,
                "source_sha256": synthetic_source["sha256"],
                "status": "active",
            }
        )
    migrated["metadata"]["migrated_from"] = "0.1"
    migrated["metadata"]["last_operation"] = "migrate"
    return migrated
