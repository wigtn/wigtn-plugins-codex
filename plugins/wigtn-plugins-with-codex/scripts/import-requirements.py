#!/usr/bin/env python3
"""Normalize Markdown requirements into a WIGTN Evidence Contract stub."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from typing import Iterable


FORMATS = {"auto", "wigtn", "spec-kit", "openspec", "bmad", "generic"}
STABLE_ID = re.compile(r"^[A-Z][A-Z0-9_-]*-[0-9]{2,}$", re.I)
INLINE_ID = re.compile(
    r"(?:\*\*|`)?(?P<id>[A-Z][A-Z0-9_-]*-[0-9]{2,})(?:\*\*|`)?"
    r"\s*(?::|[-–—])?\s*(?P<text>.+)",
    re.I,
)


def detect_format(path: Path, text: str) -> str:
    lowered_path = path.as_posix().casefold()
    if re.search(r"^###\s+Requirement:", text, re.I | re.M):
        return "openspec"
    if ".specify/" in lowered_path or re.search(
        r"^##\s+(?:User Scenarios|Functional Requirements)", text, re.I | re.M
    ):
        return "spec-kit"
    if "_bmad/" in lowered_path or re.search(
        r"^##\s+(?:Story|Acceptance Criteria|Dev Notes)", text, re.I | re.M
    ):
        return "bmad"
    if "wigtn-prd-profile:" in text or re.search(
        r"^##\s+(?:Functional requirements|기능 요구사항)", text, re.I | re.M
    ):
        return "wigtn"
    return "generic"


def clean_text(value: str) -> str:
    value = re.sub(r"[*_`]+", "", value)
    return re.sub(r"\s+", " ", value).strip(" |:-")


def derived_id(prefix: str, source: str, used: set[str]) -> str:
    number = int(sha256(source.encode("utf-8")).hexdigest()[:12], 16) % 100_000_000
    while True:
        candidate = f"{prefix}-{number:08d}"
        if candidate not in used:
            return candidate
        number = (number + 1) % 100_000_000


def explicit_requirements(text: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = [clean_text(cell) for cell in stripped.strip("|").split("|")]
            if len(cells) >= 2 and STABLE_ID.fullmatch(cells[0]):
                results.append((cells[0].upper(), cells[1]))
                continue
        match = INLINE_ID.search(stripped.lstrip("#-+ 0123456789."))
        if match:
            results.append(
                (match.group("id").upper(), clean_text(match.group("text")))
            )
    return results


def openspec_requirements(
    text: str, source_key: str, used: set[str]
) -> list[tuple[str, str]]:
    pattern = re.compile(
        r"^###\s+Requirement:\s*(?P<title>[^\n]+)\n"
        r"(?P<body>.*?)(?=^###\s+Requirement:|^##\s+|\Z)",
        re.I | re.M | re.S,
    )
    results: list[tuple[str, str]] = []
    reserved = set(used)
    for match in pattern.finditer(text):
        title = clean_text(match.group("title"))
        body_lines = [
            clean_text(line)
            for line in match.group("body").splitlines()
            if clean_text(line)
        ]
        behavior = next(
            (
                line
                for line in body_lines
                if re.search(r"\b(?:SHALL|MUST|WHEN|THEN)\b", line, re.I)
            ),
            "",
        )
        requirement_id = derived_id(
            "OS", f"{source_key}\n{title}\n{behavior}", reserved
        )
        reserved.add(requirement_id)
        results.append(
            (requirement_id, f"{title}: {behavior}" if behavior else title)
        )
    return results


def acceptance_section(text: str) -> str:
    match = re.search(
        r"^#{1,4}\s+(?:Acceptance Criteria|인수 조건|수용 기준)[^\n]*\n"
        r"(?P<body>.*?)(?=^#{1,4}\s+|\Z)",
        text,
        re.I | re.M | re.S,
    )
    return match.group("body") if match else ""


def derived_acceptance(
    text: str, prefix: str, source_key: str, used: set[str]
) -> list[tuple[str, str]]:
    section = acceptance_section(text)
    if not section:
        return []
    results: list[tuple[str, str]] = []
    reserved = set(used)
    for line in section.splitlines():
        match = re.match(r"^\s*(?:[-*+]|\d+[.)])\s+(.+)", line)
        if not match:
            continue
        requirement = clean_text(match.group(1))
        if not requirement or set(requirement) <= {"-", ":"}:
            continue
        explicit = INLINE_ID.search(requirement)
        if explicit:
            requirement_id = explicit.group("id").upper()
            requirement = clean_text(explicit.group("text"))
        else:
            requirement_id = derived_id(
                prefix, f"{source_key}\n{requirement}", reserved
            )
        if requirement_id in reserved:
            continue
        reserved.add(requirement_id)
        results.append((requirement_id, requirement))
    return results


def normalize(
    sources: Iterable[tuple[Path, str, str]]
) -> dict[str, object]:
    source_artifacts: list[dict[str, str]] = []
    requirements: list[dict[str, object]] = []
    formats: list[str] = []
    used_ids: set[str] = set()
    seen_text: set[str] = set()

    for path, text, source_format in sources:
        source_key = path.as_posix()
        formats.append(source_format)
        source_artifacts.append(
            {"kind": f"{source_format}-requirements", "path": source_key}
        )

        extracted = explicit_requirements(text)
        if source_format == "openspec":
            extracted.extend(
                openspec_requirements(text, source_key, used_ids)
            )
        elif source_format == "bmad":
            extracted.extend(
                derived_acceptance(text, "BM", source_key, used_ids)
            )
        elif not extracted:
            extracted.extend(
                derived_acceptance(text, "REQ", source_key, used_ids)
            )

        for requirement_id, requirement_text in extracted:
            normalized_text = clean_text(requirement_text)
            if (
                not normalized_text
                or requirement_id in used_ids
                or normalized_text.casefold() in seen_text
            ):
                continue
            used_ids.add(requirement_id)
            seen_text.add(normalized_text.casefold())
            requirements.append(
                {
                    "id": requirement_id,
                    "text": normalized_text,
                    "status": "not-verifiable",
                    "code_evidence": [],
                    "check_ids": [],
                    "gaps": [
                        "Implementation evidence was not inspected during artifact import."
                    ],
                }
            )

    return {
        "schema_version": "1.0",
        "artifact_type": "acceptance",
        "source_artifacts": source_artifacts,
        "requirements": requirements,
        "checks": [],
        "release_authority": {
            "source_request": "",
            "commit": False,
            "push": False,
            "pull_request": False,
            "deploy": False,
        },
        "external_actions": [],
        "limitations": [
            "Imported Markdown was normalized without inspecting implementation or executing checks."
        ],
        "metadata": {
            "importer": "wigtn-requirements/1.0",
            "source_formats": formats,
        },
    }


def resume(document: dict[str, object], existing: dict[str, object]) -> None:
    existing_requirements = {
        item.get("id"): item
        for item in existing.get("requirements", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    preserved: list[str] = []
    invalidated: list[str] = []
    current_ids: set[str] = set()
    referenced_checks: set[str] = set()
    for item in document["requirements"]:
        requirement_id = item["id"]
        current_ids.add(requirement_id)
        previous = existing_requirements.get(requirement_id)
        if previous is None:
            continue
        if clean_text(str(previous.get("text", ""))) == clean_text(item["text"]):
            item.clear()
            item.update(previous)
            preserved.append(requirement_id)
            referenced_checks.update(item.get("check_ids", []))
        else:
            item["gaps"] = [
                "Requirement text changed; prior implementation and check evidence was invalidated."
            ]
            invalidated.append(requirement_id)
    existing_checks = existing.get("checks", [])
    document["checks"] = [
        check
        for check in existing_checks
        if isinstance(check, dict) and check.get("id") in referenced_checks
    ]
    metadata = document.setdefault("metadata", {})
    metadata.update(
        {
            "resume": {
                "preserved_requirement_ids": sorted(preserved),
                "invalidated_requirement_ids": sorted(invalidated),
                "removed_requirement_ids": sorted(
                    set(existing_requirements) - current_ids
                ),
            }
        }
    )


def repository_path(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{path}: source must be inside repository root") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Markdown requirements into a WIGTN Evidence Contract."
    )
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--format", choices=sorted(FORMATS), default="auto")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--existing",
        type=Path,
        help="Conservatively resume unchanged evidence from an existing contract.",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inputs: list[tuple[Path, str, str]] = []
    try:
        for source in args.sources:
            relative = repository_path(source, args.root)
            text = source.read_text(encoding="utf-8", errors="ignore")
            source_format = (
                detect_format(relative, text)
                if args.format == "auto"
                else args.format
            )
            inputs.append((relative, text, source_format))
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2

    document = normalize(inputs)
    if not document["requirements"]:
        print("No supported requirements found.", file=sys.stderr)
        return 1
    if args.existing is not None:
        try:
            repository_path(args.existing, args.root)
            existing = json.loads(args.existing.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                raise ValueError("existing evidence must be a JSON object")
            resume(document, existing)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(exc, file=sys.stderr)
            return 2

    output = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(output, end="")
    else:
        try:
            repository_path(args.output.parent, args.root)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        except (OSError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
