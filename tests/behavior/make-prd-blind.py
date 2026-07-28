#!/usr/bin/env python3
"""Create anonymous PRD comparison panels from package-ablation outputs."""

from __future__ import annotations

import hashlib
from pathlib import Path
import random
import sys


ARMS = ("bare", "placebo4", "core4", "full8")


def labels(panel: str) -> dict[str, str]:
    values = list(ARMS)
    random.Random(hashlib.sha256(panel.encode()).digest()).shuffle(values)
    return {chr(65 + index): arm for index, arm in enumerate(values)}


def main(root55_arg: str, root56_arg: str, output_arg: str) -> int:
    roots = {"M55": Path(root55_arg), "M56": Path(root56_arg)}
    output = Path(output_arg)
    output.mkdir(parents=True)
    prompts = output / "prompts"
    prompts.mkdir()
    request = (
        Path(__file__).parent / "prompts" / "prd-create.txt"
    ).read_text()
    human = [
        "# Human PRD blind-review packet",
        "",
        "> Submit two independent reviews before opening scored RESULTS.md.",
        "",
        "## Original request",
        "",
        request,
    ]
    for model, root in roots.items():
        for repeat in (1, 2):
            panel = f"{model}-R{repeat}"
            panel_map = labels(panel)
            candidates = []
            human.extend(["", f"# Panel: {panel}"])
            for label, arm in panel_map.items():
                text = (root / "runs" / arm / f"prd-create.{repeat}.out.md").read_text()
                candidates.extend([f"## Candidate {label}", "", text])
                human.extend(["", f"## Candidate {label}", "", text])
            schema = (
                '{"panel":"' + panel + '","candidates":[{"label":"A",'
                '"completeness":0,"implementability":0,"decision_hygiene":0,'
                '"traceability":0,"concision":0,"material_omissions":[],'
                '"fabricated_policies":[],"summary":"..."}],'
                '"ranking_best_to_worst":["A","B","C","D"]}'
            )
            prompt = "\n".join(
                [
                    "You are an anonymous senior product/engineering reviewer.",
                    "Judge each PRD independently from 0 (unusable) to 4 (strong).",
                    "Completeness means material request coverage, not length.",
                    "Implementability means an engineer can make observable choices.",
                    "Decision hygiene penalizes invented policy, architecture, SLA,",
                    "identity, retry, or route decisions unsupported by the request.",
                    "Traceability values stable requirements and testable acceptance.",
                    "Concision penalizes repetition and low-value bulk.",
                    "Do not infer the producing model or tool. Return JSON only.",
                    "",
                    "# Original request",
                    request,
                    "",
                    *candidates,
                    "",
                    "# Required JSON shape",
                    schema,
                ]
            )
            (prompts / f"{panel}.txt").write_text(prompt)
    (output / "HUMAN-REVIEW-PACKET.md").write_text("\n".join(human) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))
