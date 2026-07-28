#!/usr/bin/env python3
"""Validate the deterministic structure of a WIGTN PRD."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.I | re.M | re.S) is not None


def heading(pattern: str, text: str) -> bool:
    return has(rf"^#{{1,4}}\s+[^\n]*(?:{pattern})", text)


def section_body(pattern: str, text: str) -> str:
    match = re.search(
        rf"^#{{1,4}}\s+[^\n]*(?:{pattern})[^\n]*\n"
        r"(?P<body>.*?)(?=^#{1,4}\s+|\Z)",
        text,
        re.I | re.M | re.S,
    )
    return match.group("body") if match else ""


def stable_table_ids(body: str) -> set[str]:
    ids: set[str] = set()
    for line in body.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        first_cell = (
            line.strip().strip("|").split("|", 1)[0].strip().strip("`")
        )
        if re.fullmatch(r"[A-Z][A-Z0-9_-]*-[0-9]{2,}", first_cell, re.I):
            ids.add(first_cell.upper())
    return ids


def applicability(text: str) -> dict[str, tuple[str, str]]:
    match = re.search(
        r"^#{1,4}\s+[^\n]*(?:Applicability|적용성|적용\s*범위)[^\n]*\n"
        r"(?P<body>.*?)(?=^#{1,4}\s+|\Z)",
        text,
        re.I | re.M | re.S,
    )
    if not match:
        return {}
    rows: dict[str, tuple[str, str]] = {}
    for line in match.group("body").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or set(cells[0]) <= {"-", ":"}:
            continue
        key = cells[0].casefold()
        if key not in {"contract", "계약"}:
            rows[key] = (cells[1].casefold(), cells[2])
    return rows


def find_row(
    rows: dict[str, tuple[str, str]], *terms: str
) -> tuple[str, str] | None:
    for key, value in rows.items():
        if any(term.casefold() in key for term in terms):
            return value
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("prd", type=Path)
    parser.add_argument(
        "--profile",
        choices=("auto", "compact", "full"),
        default="auto",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    text = args.prd.read_text(encoding="utf-8", errors="ignore")
    failures: list[dict[str, str]] = []

    def require(code: str, ok: bool, message: str) -> None:
        if not ok:
            failures.append({"code": code, "message": message})

    marker = re.search(
        r"<!--\s*wigtn-prd-profile:\s*(compact|full)\s*-->",
        text,
        re.I,
    )
    declared_profile = marker.group(1).casefold() if marker else None
    profile = (
        args.profile
        if args.profile != "auto"
        else declared_profile or "full"
    )
    if args.profile != "auto" and declared_profile is not None:
        require(
            "profile-mismatch",
            declared_profile == args.profile,
            f"Document declares {declared_profile}, not {args.profile}.",
        )
    if profile == "compact":
        require(
            "profile-marker",
            declared_profile == "compact",
            "Compact PRDs must declare <!-- wigtn-prd-profile: compact -->.",
        )

    rows = applicability(text)
    require("problem", heading(r"context|problem|배경|문제", text), "Problem section is missing.")
    require("goals", heading(r"goals?|목표", text), "Goals section is missing.")
    require("non-goals", heading(r"non[- ]?goals?|비목표|제외", text), "Non-goals section is missing.")
    require("roles", heading(r"users?|roles?|사용자|역할|권한", text), "Roles section is missing.")
    functional_body = section_body(
        r"functional\s+requirements?|기능\s*요구사항",
        text,
    )
    acceptance_body = section_body(
        r"acceptance(?:\s+criteria)?|수용(?:\s+기준)?|인수(?:\s+기준)?",
        text,
    )
    fr_ids = stable_table_ids(functional_body)
    ac_ids = stable_table_ids(acceptance_body)
    require(
        "fr",
        len(fr_ids) >= 1,
        "No stable material requirement ID in the functional-requirements table.",
    )
    require(
        "authorization",
        heading(r"authorization|data boundaries|인가|데이터 경계|권한", text),
        "Authorization/data-boundary section is missing.",
    )
    require("acceptance", heading(r"acceptance|수용|인수", text), "Acceptance section is missing.")
    require(
        "acceptance-shape",
        has(r"^\|[^\n]*(?:Given|전제)[^\n]*(?:When|행동)[^\n]*(?:Then|결과)", text),
        "Acceptance criteria need precondition/action/result columns.",
    )
    delivery_heading = heading(
        r"delivery|release condition|구현\s*단계|출시\s*단계|"
        r"전달\s*계획|출시\s*계획|구현\s*계획|릴리스\s*조건",
        text,
    )
    delivery_body = section_body(
        r"delivery|release condition|구현\s*단계|출시\s*단계|"
        r"전달\s*계획|출시\s*계획|구현\s*계획|릴리스\s*조건",
        text,
    )
    mapped_requirement = any(
        re.search(rf"\b{re.escape(requirement_id)}\b", delivery_body, re.I)
        for requirement_id in fr_ids
    )
    delivery_mapping = (
        has(r"(?:Phase|단계|주\s*차)", delivery_body)
        and mapped_requirement
        if profile == "full"
        else has(r"(?:Requirement\s*IDs?|요구사항\s*ID)", delivery_body)
        and mapped_requirement
    )
    require(
        "delivery",
        delivery_heading
        and delivery_mapping
        and has(r"(?:exit|종료|완료|검증|통과|pass)", text),
        "Delivery needs requirement IDs and verifiable exit conditions.",
    )

    if profile == "compact":
        require(
            "compact-fr-budget",
            len(fr_ids) <= 8,
            "Compact PRDs allow at most 8 material requirement IDs.",
        )
        require(
            "compact-ac-budget",
            1 <= len(ac_ids) <= 10,
            "Compact PRDs need 1–10 stable AC IDs.",
        )

    conditional = (
        (
            ("pages", "routes", "screen", "페이지", "화면", "경로"),
            r"pages?|screens?|페이지|화면",
            "Pages/routes",
        ),
        (("state", "상태"), r"state matrix|상태 매트릭스", "State matrix"),
        (("flow", "흐름"), r"user.*flow|system.*flow|사용자.*흐름|시스템.*흐름", "Mermaid flow"),
    )
    if profile == "full":
        require("applicability", bool(rows), "Applicability ledger is missing.")

    for terms, section_pattern, label in conditional:
        if profile != "full":
            break
        row = find_row(rows, *terms)
        require(
            f"{terms[0]}-applicability",
            row is not None,
            f"{label} applicability row is missing.",
        )
        if row is None:
            continue
        status, evidence = row
        is_required = any(term in status for term in ("required", "필수", "적용"))
        is_na = any(term in status for term in ("n/a", "na", "해당 없음", "비해당"))
        require(
            f"{terms[0]}-status",
            is_required or is_na,
            f"{label} status must be Required or N/A.",
        )
        if is_na:
            require(
                f"{terms[0]}-evidence",
                len(evidence.strip()) >= 5,
                f"{label} N/A needs evidence.",
            )
        if not is_required:
            continue
        require(
            f"{terms[0]}-section",
            heading(section_pattern, text),
            f"{label} is Required but missing.",
        )
        if terms[0] == "pages":
            require(
                "route-columns",
                has(
                    r"^\|[^\n]*(?:Page|Screen|페이지|화면)[^\n]*"
                    r"(?:Route|경로|Deep\s*link|딥링크|Screen\s*ID|화면\s*ID)[^\n]*"
                    r"(?:Role|역할|접근)",
                    text,
                ),
                "Pages need a route, deep link, or stable screen ID plus roles.",
            )
        elif terms[0] == "state":
            require(
                "state-columns",
                has(
                    r"^\|[^\n]*(?:Empty|빈)[^\n]*(?:Loading|로딩)[^\n]*"
                    r"(?:Error|오류|에러)[^\n]*(?:Success|성공)[^\n]*"
                    r"(?:Recovery|복구|재시도)",
                    text,
                ),
                "State matrix needs empty/loading/error/success/recovery.",
            )
        elif terms[0] == "flow":
            require(
                "mermaid",
                has(r"```mermaid\s+(?:flowchart|graph)\b", text),
                "Required flow must be Mermaid.",
            )

    result = {
        "valid": not failures,
        "profile": profile,
        "failures": failures,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif failures:
        print("PRD contract: FAIL")
        for failure in failures:
            print(f"- {failure['code']}: {failure['message']}")
    else:
        print("PRD contract: PASS")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
