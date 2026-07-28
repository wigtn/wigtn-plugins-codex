#!/usr/bin/env python3
"""Validate the frozen FeatureBench lift-pilot selection manifest."""

from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "external" / "featurebench" / "selection-2026-07-28.json"


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    candidates = data["candidate_order"]
    salt = data["selection_salt"]
    selected = data["selected_instances"]

    if data["pilot_size"] != 4:
        failures.append("pilot_size must remain frozen at four")
    if len(candidates) < data["pilot_size"]:
        failures.append("candidate list is smaller than pilot size")
    if len(selected) != data["pilot_size"] or len(set(selected)) != len(selected):
        failures.append("selected_instances must contain four unique tasks")
    repositories = [item["repository"] for item in candidates]
    if len(repositories) != len(set(repositories)):
        failures.append("candidate repositories must be unique")
    ranks = [item["rank"] for item in candidates]
    if ranks != list(range(1, len(candidates) + 1)):
        failures.append("candidate ranks must be contiguous and ordered")

    computed_digests = []
    for item in candidates:
        digest = sha256(f"{salt}:{item['instance_id']}".encode()).hexdigest()
        computed_digests.append(digest)
        if digest != item["rank_digest"]:
            failures.append(f"{item['instance_id']}: rank digest mismatch")
    if computed_digests != sorted(computed_digests):
        failures.append("candidate order is not digest-sorted")

    candidate_by_id = {item["instance_id"]: item for item in candidates}
    for instance_id in selected:
        item = candidate_by_id.get(instance_id)
        if item is None:
            failures.append(f"{instance_id}: selected task missing from candidates")
            continue
        if item.get("oracle_precheck") != "pass":
            failures.append(f"{instance_id}: selected task did not pass oracle precheck")
        if item.get("gold_resolved") is not True:
            failures.append(f"{instance_id}: selected task gold is not resolved")
        if item.get("clean_base_resolved") is not False:
            failures.append(f"{instance_id}: selected task clean base is not unresolved")

    if failures:
        print("FeatureBench selection: FAIL")
        print("\n".join(failures))
        return 1
    print(
        "FeatureBench selection: PASS "
        f"({data['pilot_size']} pilot, {len(candidates)} frozen candidates)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
