#!/usr/bin/env python3
"""Validate a WIGTN evidence artifact without third-party dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = PLUGIN_ROOT / "schemas" / "evidence-contract.schema.json"
REQUIREMENT_ID = re.compile(r"^[A-Z][A-Z0-9_]*(?:-[A-Z0-9_]+)+$")
CHECK_ID = re.compile(r"^CHK-[0-9]{2,}$")
ARTIFACT_TYPES = {"product-spec", "acceptance", "delivery", "release"}
REQUIREMENT_STATUSES = {
    "verified",
    "implemented-not-executed",
    "partially-verified",
    "not-satisfied",
    "not-verifiable",
    "not-applicable",
}
CHECK_STATUSES = {"passed", "failed", "skipped"}
ACTION_STATUSES = {"performed", "not-performed", "blocked", "failed"}
ACTIONS = {"commit", "push", "pull_request", "deploy"}


class EvidenceValidator:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def require_object(
        self,
        value: Any,
        path: str,
        *,
        required: set[str],
        allowed: set[str],
    ) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            self.error(path, "must be an object")
            return None
        missing = sorted(required - value.keys())
        extra = sorted(value.keys() - allowed)
        if missing:
            self.error(path, "missing keys: " + ", ".join(missing))
        if extra:
            self.error(path, "unknown keys: " + ", ".join(extra))
        return value

    def require_list(self, value: Any, path: str) -> list[Any] | None:
        if not isinstance(value, list):
            self.error(path, "must be an array")
            return None
        return value

    def require_string(
        self, value: Any, path: str, *, allow_empty: bool = False
    ) -> str | None:
        if not isinstance(value, str):
            self.error(path, "must be a string")
            return None
        if not allow_empty and not value.strip():
            self.error(path, "must not be empty")
        return value

    def require_bool(self, value: Any, path: str) -> bool | None:
        if not isinstance(value, bool):
            self.error(path, "must be a boolean")
            return None
        return value

    def repository_path(self, value: Any, path: str) -> str | None:
        text = self.require_string(value, path)
        if text is None:
            return None
        normalized = text.replace("\\", "/")
        candidate = PurePosixPath(normalized)
        if (
            candidate.is_absolute()
            or ".." in candidate.parts
            or re.match(r"^[A-Za-z]:/", normalized)
            or "://" in normalized
        ):
            self.error(path, "must be a repository-relative path without '..'")
        return text

    def validate(self, document: Any) -> list[str]:
        root = self.require_object(
            document,
            "$",
            required={
                "schema_version",
                "artifact_type",
                "source_artifacts",
                "requirements",
                "checks",
                "release_authority",
                "external_actions",
                "limitations",
            },
            allowed={
                "schema_version",
                "artifact_type",
                "source_artifacts",
                "requirements",
                "checks",
                "release_authority",
                "external_actions",
                "limitations",
                "metadata",
            },
        )
        if root is None:
            return self.errors

        if root.get("schema_version") != "1.0":
            self.error("$.schema_version", "must equal '1.0'")
        if root.get("artifact_type") not in ARTIFACT_TYPES:
            self.error(
                "$.artifact_type",
                "must be one of " + ", ".join(sorted(ARTIFACT_TYPES)),
            )

        self.validate_source_artifacts(root.get("source_artifacts"))
        checks = self.validate_checks(root.get("checks"))
        self.validate_requirements(root.get("requirements"), checks)
        authority = self.validate_authority(root.get("release_authority"))
        self.validate_external_actions(root.get("external_actions"), authority)
        self.validate_limitations(root.get("limitations"))

        metadata = root.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            self.error("$.metadata", "must be an object")
        return self.errors

    def validate_source_artifacts(self, value: Any) -> None:
        items = self.require_list(value, "$.source_artifacts")
        if items is None:
            return
        for index, item in enumerate(items):
            path = f"$.source_artifacts[{index}]"
            artifact = self.require_object(
                item,
                path,
                required={"kind", "path"},
                allowed={"kind", "path", "sha256"},
            )
            if artifact is None:
                continue
            self.require_string(artifact.get("kind"), f"{path}.kind")
            self.repository_path(artifact.get("path"), f"{path}.path")
            digest = artifact.get("sha256")
            if digest is not None and (
                not isinstance(digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            ):
                self.error(f"{path}.sha256", "must be a lowercase SHA-256 digest")

    def validate_checks(self, value: Any) -> dict[str, dict[str, Any]]:
        items = self.require_list(value, "$.checks")
        if items is None:
            return {}
        checks: dict[str, dict[str, Any]] = {}
        for index, item in enumerate(items):
            path = f"$.checks[{index}]"
            check = self.require_object(
                item,
                path,
                required={"id", "command", "status", "exit_code", "test_names"},
                allowed={"id", "command", "status", "exit_code", "test_names"},
            )
            if check is None:
                continue
            check_id = self.require_string(check.get("id"), f"{path}.id")
            if check_id is not None:
                if CHECK_ID.fullmatch(check_id) is None:
                    self.error(f"{path}.id", "must match CHK-<number>")
                elif check_id in checks:
                    self.error(f"{path}.id", f"duplicate check id {check_id}")
                else:
                    checks[check_id] = check
            self.require_string(check.get("command"), f"{path}.command")
            status = check.get("status")
            if status not in CHECK_STATUSES:
                self.error(
                    f"{path}.status",
                    "must be one of " + ", ".join(sorted(CHECK_STATUSES)),
                )
            exit_code = check.get("exit_code")
            if status == "passed" and exit_code != 0:
                self.error(f"{path}.exit_code", "passed checks must have exit code 0")
            elif status == "failed" and (
                not isinstance(exit_code, int)
                or isinstance(exit_code, bool)
                or exit_code == 0
            ):
                self.error(
                    f"{path}.exit_code",
                    "failed checks must have a non-zero integer exit code",
                )
            elif status == "skipped" and exit_code is not None:
                self.error(f"{path}.exit_code", "skipped checks must use null")
            names = self.require_list(check.get("test_names"), f"{path}.test_names")
            if names is not None:
                for name_index, name in enumerate(names):
                    self.require_string(
                        name, f"{path}.test_names[{name_index}]"
                    )
        return checks

    def validate_requirements(
        self, value: Any, checks: dict[str, dict[str, Any]]
    ) -> None:
        items = self.require_list(value, "$.requirements")
        if items is None:
            return
        requirement_ids: set[str] = set()
        for index, item in enumerate(items):
            path = f"$.requirements[{index}]"
            requirement = self.require_object(
                item,
                path,
                required={
                    "id",
                    "text",
                    "status",
                    "code_evidence",
                    "check_ids",
                    "gaps",
                },
                allowed={
                    "id",
                    "text",
                    "status",
                    "code_evidence",
                    "check_ids",
                    "gaps",
                },
            )
            if requirement is None:
                continue
            requirement_id = self.require_string(
                requirement.get("id"), f"{path}.id"
            )
            if requirement_id is not None:
                if REQUIREMENT_ID.fullmatch(requirement_id) is None:
                    self.error(
                        f"{path}.id",
                        "must match a stable ID such as FR-01 or AC-01",
                    )
                elif requirement_id in requirement_ids:
                    self.error(
                        f"{path}.id", f"duplicate requirement id {requirement_id}"
                    )
                requirement_ids.add(requirement_id)
            self.require_string(requirement.get("text"), f"{path}.text")
            status = requirement.get("status")
            if status not in REQUIREMENT_STATUSES:
                self.error(
                    f"{path}.status",
                    "must be one of " + ", ".join(sorted(REQUIREMENT_STATUSES)),
                )

            code_evidence = self.validate_code_evidence(
                requirement.get("code_evidence"), f"{path}.code_evidence"
            )
            check_ids = self.validate_check_ids(
                requirement.get("check_ids"), f"{path}.check_ids", checks
            )
            gaps = self.validate_string_list(
                requirement.get("gaps"), f"{path}.gaps"
            )
            passed = any(
                check_id in checks and checks[check_id].get("status") == "passed"
                for check_id in check_ids
            )

            if status == "verified":
                if not code_evidence:
                    self.error(
                        f"{path}.code_evidence",
                        "verified requirements need implementation evidence",
                    )
                if not passed:
                    self.error(
                        f"{path}.check_ids",
                        "verified requirements need a referenced passing check",
                    )
                if gaps:
                    self.error(
                        f"{path}.gaps", "verified requirements cannot retain gaps"
                    )
            elif status == "implemented-not-executed":
                if not code_evidence:
                    self.error(
                        f"{path}.code_evidence",
                        "implemented-not-executed requires implementation evidence",
                    )
                if passed:
                    self.error(
                        f"{path}.status",
                        "use verified when a relevant passing check is referenced",
                    )
            elif status in {
                "partially-verified",
                "not-satisfied",
                "not-verifiable",
            } and not gaps:
                self.error(f"{path}.gaps", f"{status} requires at least one gap")

    def validate_code_evidence(self, value: Any, path: str) -> list[dict[str, Any]]:
        items = self.require_list(value, path)
        if items is None:
            return []
        valid: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            item_path = f"{path}[{index}]"
            evidence = self.require_object(
                item,
                item_path,
                required={"path", "line_start", "line_end"},
                allowed={"path", "line_start", "line_end", "symbol"},
            )
            if evidence is None:
                continue
            self.repository_path(evidence.get("path"), f"{item_path}.path")
            line_start = evidence.get("line_start")
            line_end = evidence.get("line_end")
            if (
                not isinstance(line_start, int)
                or isinstance(line_start, bool)
                or line_start < 1
            ):
                self.error(f"{item_path}.line_start", "must be an integer >= 1")
            if (
                not isinstance(line_end, int)
                or isinstance(line_end, bool)
                or line_end < 1
            ):
                self.error(f"{item_path}.line_end", "must be an integer >= 1")
            if (
                isinstance(line_start, int)
                and not isinstance(line_start, bool)
                and isinstance(line_end, int)
                and not isinstance(line_end, bool)
                and line_end < line_start
            ):
                self.error(
                    f"{item_path}.line_end", "must be >= line_start"
                )
            symbol = evidence.get("symbol")
            if symbol is not None:
                self.require_string(symbol, f"{item_path}.symbol")
            valid.append(evidence)
        return valid

    def validate_check_ids(
        self, value: Any, path: str, checks: dict[str, dict[str, Any]]
    ) -> list[str]:
        items = self.require_list(value, path)
        if items is None:
            return []
        result: list[str] = []
        seen: set[str] = set()
        for index, item in enumerate(items):
            item_path = f"{path}[{index}]"
            check_id = self.require_string(item, item_path)
            if check_id is None:
                continue
            if CHECK_ID.fullmatch(check_id) is None:
                self.error(item_path, "must match CHK-<number>")
            if check_id in seen:
                self.error(item_path, f"duplicate check reference {check_id}")
            if check_id not in checks:
                self.error(item_path, f"unknown check reference {check_id}")
            seen.add(check_id)
            result.append(check_id)
        return result

    def validate_string_list(self, value: Any, path: str) -> list[str]:
        items = self.require_list(value, path)
        if items is None:
            return []
        result: list[str] = []
        for index, item in enumerate(items):
            text = self.require_string(item, f"{path}[{index}]")
            if text is not None and text.strip():
                result.append(text)
        return result

    def validate_authority(self, value: Any) -> dict[str, Any]:
        path = "$.release_authority"
        authority = self.require_object(
            value,
            path,
            required={"source_request", "commit", "push", "pull_request", "deploy"},
            allowed={"source_request", "commit", "push", "pull_request", "deploy"},
        )
        if authority is None:
            return {}
        source_request = self.require_string(
            authority.get("source_request"),
            f"{path}.source_request",
            allow_empty=True,
        )
        has_authority = False
        for action in sorted(ACTIONS):
            allowed = self.require_bool(authority.get(action), f"{path}.{action}")
            has_authority = has_authority or allowed is True
        if has_authority and source_request is not None and not source_request.strip():
            self.error(
                f"{path}.source_request",
                "must quote or summarize the user request granting authority",
            )
        return authority

    def validate_external_actions(
        self, value: Any, authority: dict[str, Any]
    ) -> None:
        items = self.require_list(value, "$.external_actions")
        if items is None:
            return
        for index, item in enumerate(items):
            path = f"$.external_actions[{index}]"
            action_item = self.require_object(
                item,
                path,
                required={"action", "status", "evidence"},
                allowed={"action", "status", "evidence"},
            )
            if action_item is None:
                continue
            action = action_item.get("action")
            status = action_item.get("status")
            if action not in ACTIONS:
                self.error(
                    f"{path}.action",
                    "must be one of " + ", ".join(sorted(ACTIONS)),
                )
            if status not in ACTION_STATUSES:
                self.error(
                    f"{path}.status",
                    "must be one of " + ", ".join(sorted(ACTION_STATUSES)),
                )
            evidence = self.require_string(
                action_item.get("evidence"),
                f"{path}.evidence",
                allow_empty=status == "not-performed",
            )
            if status == "performed" and action in ACTIONS:
                if authority.get(action) is not True:
                    self.error(
                        f"{path}.status",
                        f"performed {action} lacks recorded user authority",
                    )
                if evidence is not None and not evidence.strip():
                    self.error(
                        f"{path}.evidence",
                        "performed actions require a commit, branch, URL, or deployment reference",
                    )

    def validate_limitations(self, value: Any) -> None:
        self.validate_string_list(value, "$.limitations")


def load_document(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def validate_schema_file(path: Path) -> None:
    schema = load_document(path)
    if not isinstance(schema, dict):
        raise ValueError("schema must be a JSON object")
    if schema.get("$id") != "https://wigtn.com/schemas/evidence-contract/1.0":
        raise ValueError("unexpected schema $id")
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("schema must use JSON Schema draft 2020-12")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate WIGTN evidence contract JSON files."
    )
    parser.add_argument("artifacts", nargs="+", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        validate_schema_file(args.schema)
    except ValueError as exc:
        print(f"{args.schema}: invalid schema: {exc}", file=sys.stderr)
        return 2

    failed = False
    for artifact_path in args.artifacts:
        try:
            document = load_document(artifact_path)
        except ValueError as exc:
            print(f"{artifact_path}: invalid JSON: {exc}", file=sys.stderr)
            failed = True
            continue
        errors = EvidenceValidator().validate(document)
        if errors:
            failed = True
            print(f"{artifact_path}: FAIL", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
        else:
            print(f"{artifact_path}: PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
