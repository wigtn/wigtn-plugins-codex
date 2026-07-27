#!/usr/bin/env python3
"""Self-contained repository validator for local use and GitHub Actions."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
EXPECTED_SKILLS = {
    "product-spec",
    "screen-spec",
    "acceptance-verifier",
    "design-direction",
    "verified-delivery",
    "release-readiness",
    "handdrawn-diagram",
    "wigtn-presentation",
}
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path.relative_to(ROOT)}: {exc}") from exc


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.relative_to(ROOT)}: missing YAML frontmatter")
    try:
        block = text.split("---\n", 2)[1]
    except IndexError as exc:
        raise ValueError(f"{path.relative_to(ROOT)}: unterminated frontmatter") from exc
    values: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"{path.relative_to(ROOT)}: invalid frontmatter line {line!r}")
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def main() -> int:
    errors: list[str] = []
    try:
        marketplace = load_json(MARKETPLACE)
    except ValueError as exc:
        print(exc)
        return 1

    if marketplace.get("name") != "wigtn":
        errors.append("marketplace name must be 'wigtn'")
    entries = marketplace.get("plugins", [])
    if len(entries) != 1:
        errors.append(f"marketplace must contain exactly one plugin, found {len(entries)}")
        entries = []

    plugin_root: Path | None = None
    if entries:
        entry = entries[0]
        name = entry.get("name")
        source = entry.get("source", {})
        if source.get("source") != "local":
            errors.append("marketplace plugin source must be local")
        source_path = source.get("path", "")
        if not isinstance(source_path, str) or not source_path.startswith("./plugins/"):
            errors.append("marketplace source.path must start with ./plugins/")
        else:
            plugin_root = (ROOT / source_path).resolve()
            if plugin_root.name != name or not plugin_root.is_dir():
                errors.append("marketplace name and source directory must exist and match")
        policy = entry.get("policy", {})
        if policy.get("installation") not in {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}:
            errors.append("invalid marketplace installation policy")
        if policy.get("authentication") not in {"ON_INSTALL", "ON_USE"}:
            errors.append("invalid marketplace authentication policy")
        if not entry.get("category"):
            errors.append("marketplace category is required")

    if plugin_root:
        manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
        try:
            manifest = load_json(manifest_path)
        except ValueError as exc:
            errors.append(str(exc))
            manifest = {}
        if manifest.get("name") != plugin_root.name:
            errors.append("plugin folder and manifest name must match")
        if not SEMVER.fullmatch(str(manifest.get("version", ""))):
            errors.append("plugin version must be SemVer")
        if manifest.get("skills") != "./skills/":
            errors.append("plugin manifest skills path must be ./skills/")
        for unsupported in ("apps", "mcpServers", "hooks"):
            if unsupported in manifest:
                errors.append(f"plugin manifest contains unsupported MVP field: {unsupported}")

        skills_root = plugin_root / "skills"
        skill_names = {path.name for path in skills_root.iterdir() if path.is_dir()}
        if skill_names != EXPECTED_SKILLS:
            errors.append(
                "skill set mismatch: expected "
                + ", ".join(sorted(EXPECTED_SKILLS))
                + "; found "
                + ", ".join(sorted(skill_names))
            )
        description_total = 0
        for name in sorted(skill_names):
            skill = skills_root / name
            skill_md = skill / "SKILL.md"
            agent_yaml = skill / "agents" / "openai.yaml"
            if not skill_md.is_file() or not agent_yaml.is_file():
                errors.append(f"{name}: SKILL.md and agents/openai.yaml are required")
                continue
            try:
                meta = frontmatter(skill_md)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if set(meta) != {"name", "description"}:
                errors.append(f"{name}: frontmatter must contain only name and description")
            if meta.get("name") != name:
                errors.append(f"{name}: frontmatter name mismatch")
            description = meta.get("description", "")
            description_total += len(description)
            if not description:
                errors.append(f"{name}: description is required")
            yaml_text = agent_yaml.read_text(encoding="utf-8")
            qualified_name = f"$wigtn-plugins-with-codex:{name}"
            if f"Use {qualified_name}" not in yaml_text:
                errors.append(
                    f"{name}: default_prompt must explicitly mention {qualified_name}"
                )
            if "allow_implicit_invocation: true" not in yaml_text:
                errors.append(f"{name}: skill must remain discoverable in the catalog")
            if name == "verified-delivery" and "never auto-invoke for ordinary coding" not in description:
                errors.append(
                    "verified-delivery: description must preserve the explicit-only boundary"
                )
        if description_total > 4000:
            errors.append(f"skill description budget exceeded: {description_total}/4000")

    if errors:
        print("Repository validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Repository contract: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
