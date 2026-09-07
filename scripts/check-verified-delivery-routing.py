#!/usr/bin/env python3
"""Static regression contract for risk-adaptive verified delivery."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILL = (
    ROOT
    / "plugins"
    / "wigtn-plugins-with-codex"
    / "skills"
    / "verified-delivery"
    / "SKILL.md"
)
EVIDENCE = SKILL.parent / "references" / "delivery-evidence.md"
POLICY = SKILL.parent / "agents" / "openai.yaml"


def main() -> int:
    skill = SKILL.read_text(encoding="utf-8")
    evidence = EVIDENCE.read_text(encoding="utf-8")
    policy = POLICY.read_text(encoding="utf-8")
    required = {
        "explicit boundary": "never auto-invoke for ordinary coding",
        "single workflow": "## Workflow",
        "risk gate": "auth, tenancy, secrets, migration, persistence, concurrency",
        "proportional evidence": "only when the request names multiple material requirements",
        "native oracle non-duplication": "Do not duplicate a passing repository oracle",
        "no default state": "Do not create stable IDs, WorkGraph state, or evidence JSON by default",
        "multi-interface census": "Use a compact coverage census",
        "evaluation isolation": "For benchmark or independent evaluation work",
        "leakage invalidates evidence": "A clean evaluator pass does not",
        "matrix suppression": "Do not manufacture a matrix for a one-line fix",
    }
    failures = []
    for label, phrase in required.items():
        corpus = (
            evidence
            if label in {"matrix suppression", "leakage invalidates evidence"}
            else skill
        )
        if phrase not in corpus:
            failures.append(f"{label}: missing {phrase!r}")
    if "allow_implicit_invocation: false" not in policy:
        failures.append("explicit policy: allow_implicit_invocation must be false")
    if "## Fast path" in skill or "## Assurance path" in skill:
        failures.append("legacy route headings must be removed")
    if failures:
        print("Verified-delivery routing: FAIL")
        print("\n".join(failures))
        return 1
    print(f"Verified-delivery routing: PASS ({len(required)} contracts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
