#!/usr/bin/env python3
"""Build isolated WIGTN marketplace candidates for component ablation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "wigtn-plugins-with-codex"
PLUGIN = ROOT / "plugins" / PLUGIN_NAME
CORE = (
    "product-spec",
    "acceptance-verifier",
    "verified-delivery",
    "release-readiness",
)
PLACEBO_NAMES = (
    "control-catalog",
    "control-index",
    "control-archive",
    "control-notes",
)


def description(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^description:\s*(.+)$", text, re.M)
    if not match:
        raise ValueError(f"{path}: description not found")
    return match.group(1).strip()


def neutral_description(target_length: int, name: str) -> str:
    base = (
        f"Reserved metadata control for {name}. Use only when explicitly invoked "
        "for the named synthetic evaluation control; never use for product "
        "requirements, verification, coding, review, Git, release, design, "
        "documents, diagrams, presentations, or ordinary user work. "
    )
    padding = (
        "Neutral catalog metadata has no workflow instructions or domain guidance. "
    )
    value = base
    while len(value) < target_length:
        value += padding
    # Preserve the exact metadata-length control. The parser strips surrounding
    # whitespace, so replace a trailing space instead of trimming it.
    result = value[:target_length]
    if result[-1].isspace():
        result = result[:-1] + "."
    return result


def create_placebo(skills: Path) -> None:
    lengths = [
        len(description(PLUGIN / "skills" / name / "SKILL.md"))
        for name in CORE
    ]
    for name, target_length in zip(PLACEBO_NAMES, lengths, strict=True):
        skill = skills / name
        (skill / "agents").mkdir(parents=True)
        desc = neutral_description(target_length, name)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {desc}\n---\n\n"
            f"# {name.replace('-', ' ').title()}\n\n"
            "This is a metadata-only evaluation control. Do not apply it to real work.\n",
            encoding="utf-8",
        )
        (skill / "agents" / "openai.yaml").write_text(
            "interface:\n"
            f'  display_name: "{name.replace("-", " ").title()}"\n'
            '  short_description: "Metadata-only evaluation control"\n'
            f'  default_prompt: "Use ${PLUGIN_NAME}:{name} only for its named '
            'synthetic control."\n'
            "policy:\n"
            "  allow_implicit_invocation: true\n",
            encoding="utf-8",
        )


def build(destination: Path, variant: str) -> None:
    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    marketplace = destination / ".agents" / "plugins"
    target_plugin = destination / "plugins" / PLUGIN_NAME
    marketplace.mkdir(parents=True)
    source_marketplace = json.loads(
        (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
            encoding="utf-8"
        )
    )
    source_marketplace["plugins"] = [
        entry
        for entry in source_marketplace.get("plugins", [])
        if entry.get("name") == PLUGIN_NAME
    ]
    (marketplace / "marketplace.json").write_text(
        json.dumps(source_marketplace, indent=2) + "\n", encoding="utf-8"
    )
    shutil.copytree(PLUGIN, target_plugin)

    skills = target_plugin / "skills"
    if variant == "core4":
        for path in skills.iterdir():
            if path.is_dir() and path.name not in CORE:
                shutil.rmtree(path)
    elif variant == "placebo4":
        shutil.rmtree(skills)
        skills.mkdir()
        create_placebo(skills)
    elif variant == "full8":
        shutil.rmtree(skills / "work-planner")
        # Historical evaluation shape: the current core nine minus work-planner.
    elif variant == "full9":
        # Current core-nine catalog without the separately installed Wiki plugin.
        pass
    else:
        raise ValueError(f"unsupported variant: {variant}")

    names = sorted(path.name for path in skills.iterdir() if path.is_dir())
    (destination / "ABLATION.json").write_text(
        json.dumps(
            {
                "variant": variant,
                "plugin": PLUGIN_NAME,
                "skills": names,
                "description_characters": sum(
                    len(description(skills / name / "SKILL.md")) for name in names
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "variant", choices=("core4", "placebo4", "full8", "full9")
    )
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        build(args.destination, args.variant)
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
