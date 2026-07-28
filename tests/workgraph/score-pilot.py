#!/usr/bin/env python3
"""Score WorkGraph pilot artifacts using deterministic lifecycle endpoints."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SCRIPTS = ROOT / "plugins" / "wigtn-plugins-with-codex" / "scripts"
sys.path.insert(0, str(PLUGIN_SCRIPTS))

from workgraph_core import validate_graph  # noqa: E402


CASES = ROOT / "tests" / "workgraph" / "pilot-cases.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    rows = []
    for case in cases:
        work = args.run_root / "work" / case["id"]
        graph_path = work / ".wigtn" / "workgraph.json"
        endpoints: dict[str, bool] = {
            "artifact_exists": graph_path.is_file(),
            "contract_valid": False,
            "source_integrity": False,
            "requirement_fidelity": False,
            "task_coverage": False,
            "checks_linked": False,
            "paths_specific": False,
            "dependencies": False,
            "risk_calibrated": False,
            "no_overclaim": False,
            "protected_preserved": False,
            "sentinel_preserved": (
                work / "USER-DRAFT.txt"
            ).read_text(encoding="utf-8") == f"sentinel:{case['id']}\n",
        }
        diagnostics: list[str] = []
        if graph_path.is_file():
            try:
                graph = json.loads(graph_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                diagnostics.append(f"invalid JSON: {exc}")
            else:
                errors = validate_graph(graph)
                endpoints["contract_valid"] = not errors
                diagnostics.extend(errors)
                source_path = work / "docs" / "PRD.md"
                expected_digest = sha256(source_path.read_bytes()).hexdigest()
                endpoints["source_integrity"] = any(
                    item.get("path") == "docs/PRD.md"
                    and item.get("sha256") == expected_digest
                    for item in graph.get("sources", [])
                )
                expected_ids = {
                    requirement_id
                    for requirement_id, _ in case["requirements"]
                }
                actual_ids = {
                    item.get("id") for item in graph.get("requirements", [])
                }
                endpoints["requirement_fidelity"] = (
                    actual_ids == expected_ids
                    and all(
                        item.get("status") == "active"
                        for item in graph.get("requirements", [])
                    )
                )
                covered = {
                    requirement_id
                    for task in graph.get("tasks", [])
                    for requirement_id in task.get("requirement_ids", [])
                }
                endpoints["task_coverage"] = expected_ids <= covered
                checks = {item["id"]: item for item in graph.get("checks", [])}
                tasks = graph.get("tasks", [])
                endpoints["checks_linked"] = bool(tasks) and all(
                    task.get("check_ids")
                    and all(
                        check_id in checks
                        and task["id"] in checks[check_id].get("task_ids", [])
                        and checks[check_id].get("command") == case["verification"]
                        for check_id in task["check_ids"]
                    )
                    for task in tasks
                )
                expected_paths = set(case["paths"])
                intended = {
                    path
                    for task in tasks
                    for path in task.get("intended_paths", [])
                }
                endpoints["paths_specific"] = bool(
                    intended & expected_paths
                ) and all(task.get("intended_paths") for task in tasks)
                endpoints["dependencies"] = (
                    not case["dependency_required"]
                    or any(task.get("depends_on") for task in tasks)
                )
                endpoints["risk_calibrated"] = (
                    not case["high_risk_required"]
                    or any(
                        task.get("risk") in {"high", "critical"}
                        for task in tasks
                    )
                )
                endpoints["no_overclaim"] = all(
                    task.get("status")
                    not in {"implemented", "verified", "retired", "stale"}
                    and not task.get("evidence_refs")
                    for task in tasks
                ) and all(
                    check.get("status") == "pending"
                    and check.get("evidence_ref") is None
                    for check in checks.values()
                )
                endpoints["protected_preserved"] = all(
                    {".git", ".env", "USER-DRAFT.txt"}
                    <= set(task.get("protected_paths", []))
                    for task in tasks
                )
        rows.append(
            {
                "case": case["id"],
                "passed": sum(endpoints.values()),
                "total": len(endpoints),
                "all_passed": all(endpoints.values()),
                "endpoints": endpoints,
                "diagnostics": diagnostics,
            }
        )

    report = [
        "# WorkGraph planning pilot",
        "",
        "Treatment-only capability pilot. This validates saved lifecycle behavior; "
        "it does not estimate quality lift over bare Codex.",
        "",
        "| Case | Endpoints | Contract | Fidelity | Coverage | Checks | Paths | Dependency | Risk | No overclaim | Sentinel |",
        "|---|---:|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        endpoint = row["endpoints"]
        mark = lambda key: "PASS" if endpoint[key] else "FAIL"
        report.append(
            f"| {row['case']} | {row['passed']}/{row['total']} | "
            f"{mark('contract_valid')} | {mark('requirement_fidelity')} | "
            f"{mark('task_coverage')} | {mark('checks_linked')} | "
            f"{mark('paths_specific')} | {mark('dependencies')} | "
            f"{mark('risk_calibrated')} | {mark('no_overclaim')} | "
            f"{mark('sentinel_preserved')} |"
        )
    result = {
        "cases": rows,
        "all_passed": all(row["all_passed"] for row in rows),
        "case_pass_rate": (
            sum(row["all_passed"] for row in rows) / len(rows)
            if rows
            else 0
        ),
    }
    (args.run_root / "RESULTS.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.run_root / "RESULTS.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print(
        f"WorkGraph pilot: "
        f"{sum(row['all_passed'] for row in rows)}/{len(rows)} cases"
    )
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
