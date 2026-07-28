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


def main() -> int:
    skill = SKILL.read_text(encoding="utf-8")
    evidence = EVIDENCE.read_text(encoding="utf-8")
    required = {
        "explicit boundary": "never auto-invoke for ordinary coding",
        "fast route": "## Fast path",
        "assurance route": "## Assurance path",
        "risk gate": "auth, tenancy, secret, migration, persistence, concurrency",
        "bounded checks": "at most one relevant repository suite",
        "native oracle non-duplication": "Do not build an alternate harness when native",
        "no fast-path state": "Do not create stable IDs, WorkGraph state, evidence JSON",
        "multi-interface census": "make a compact coverage census",
        "reference isolation": "Do not inspect or copy another checkout",
        "search stop rule": "diagnostic cycles without new evidence",
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
    if failures:
        print("Verified-delivery routing: FAIL")
        print("\n".join(failures))
        return 1
    if skill.index("## Fast path") > skill.index("## Assurance path"):
        print("Verified-delivery routing: FAIL")
        print("fast path must be presented before assurance path")
        return 1
    print(f"Verified-delivery routing: PASS ({len(required)} contracts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
