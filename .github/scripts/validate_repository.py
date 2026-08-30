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
    "work-planner",
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
    if len(entries) != 2:
        errors.append(f"marketplace must contain exactly two plugins, found {len(entries)}")
        entries = []

    plugin_roots: dict[str, Path] = {}
    if entries:
        names = [entry.get("name") for entry in entries]
        string_names = {name for name in names if isinstance(name, str)}
        if string_names != {"wigtn-plugins-with-codex", "wigtn-knowledge-wiki"}:
            errors.append("marketplace must list the core and knowledge-wiki plugins")
        if len(names) != len(string_names):
            errors.append("marketplace plugin names must be unique")
        for entry in entries:
            name = entry.get("name")
            source = entry.get("source", {})
            if source.get("source") != "local":
                errors.append(f"{name}: marketplace plugin source must be local")
            source_path = source.get("path", "")
            expected_path = f"./plugins/{name}" if isinstance(name, str) else ""
            if not isinstance(source_path, str) or source_path != expected_path:
                errors.append(
                    f"{name}: marketplace source.path must exactly match its plugin directory"
                )
            else:
                root = (ROOT / source_path).resolve()
                if root.name != name or not root.is_dir():
                    errors.append(
                        f"{name}: marketplace name and source directory must exist and match"
                    )
                elif isinstance(name, str):
                    plugin_roots[name] = root
            policy = entry.get("policy", {})
            if policy.get("installation") not in {
                "AVAILABLE",
                "INSTALLED_BY_DEFAULT",
                "NOT_AVAILABLE",
            }:
                errors.append(f"{name}: invalid marketplace installation policy")
            if policy.get("authentication") not in {"ON_INSTALL", "ON_USE"}:
                errors.append(f"{name}: invalid marketplace authentication policy")
            if not entry.get("category"):
                errors.append(f"{name}: marketplace category is required")

    plugin_root = plugin_roots.get("wigtn-plugins-with-codex")
    core_version = ""

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
        else:
            core_version = str(manifest["version"])
        if manifest.get("skills") != "./skills/":
            errors.append("plugin manifest skills path must be ./skills/")
        default_prompts = manifest.get("interface", {}).get("defaultPrompt", [])
        if not isinstance(default_prompts, list) or not 1 <= len(default_prompts) <= 3:
            errors.append("plugin interface.defaultPrompt must contain 1 to 3 prompts")
        for unsupported in ("apps", "mcpServers", "hooks"):
            if unsupported in manifest:
                errors.append(f"plugin manifest contains unsupported MVP field: {unsupported}")

        skills_root = plugin_root / "skills"
        if not skills_root.is_dir():
            errors.append("core plugin skills directory is missing")
            skill_names: set[str] = set()
        else:
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
            expected_policy = (
                "allow_implicit_invocation: false"
                if name == "verified-delivery"
                else "allow_implicit_invocation: true"
            )
            if expected_policy not in yaml_text:
                errors.append(f"{name}: invocation policy mismatch")
            if name == "verified-delivery" and "never auto-invoke for ordinary coding" not in description:
                errors.append(
                    "verified-delivery: description must preserve the explicit-only boundary"
                )
        if description_total > 3200:
            errors.append(f"core skill description budget exceeded: {description_total}/3200")

        evidence_paths = [
            plugin_root / "schemas" / "evidence-contract.schema.json",
            plugin_root / "scripts" / "validate-evidence.py",
            plugin_root / "scripts" / "import-requirements.py",
            plugin_root / "scripts" / "inspect-evidence.py",
            plugin_root / "scripts" / "validate-project-context.py",
            plugin_root / "scripts" / "validate-screen-spec.py",
            plugin_root / "scripts" / "inspect-release-state.py",
            plugin_root / "schemas" / "workgraph.schema.json",
            plugin_root / "scripts" / "workgraph_core.py",
            plugin_root / "scripts" / "validate-workgraph.py",
            plugin_root / "scripts" / "migrate-workgraph.py",
            plugin_root / "scripts" / "wigtn.py",
            plugin_root / "references" / "evidence-contract.md",
            plugin_root / "schemas" / "project-context.schema.json",
        ]
        for path in evidence_paths:
            if not path.is_file():
                errors.append(
                    f"missing Evidence Contract component: {path.relative_to(ROOT)}"
                )
        if evidence_paths[0].is_file():
            try:
                evidence_schema = load_json(evidence_paths[0])
            except ValueError as exc:
                errors.append(str(exc))
            else:
                if evidence_schema.get("$id") != (
                    "https://wigtn.com/schemas/evidence-contract/1.0"
                ):
                    errors.append("Evidence Contract schema $id must identify version 1.0")
                schema_version = (
                    evidence_schema.get("properties", {})
                    .get("schema_version", {})
                    .get("const")
                )
                if schema_version != "1.0":
                    errors.append("Evidence Contract schema_version must be 1.0")
        workgraph_schema_path = plugin_root / "schemas" / "workgraph.schema.json"
        if workgraph_schema_path.is_file():
            try:
                workgraph_schema = load_json(workgraph_schema_path)
            except ValueError as exc:
                errors.append(str(exc))
            else:
                if workgraph_schema.get("$id") != (
                    "https://wigtn.com/schemas/workgraph/1.0"
                ):
                    errors.append("WorkGraph schema $id must identify version 1.0")
                workgraph_version = (
                    workgraph_schema.get("properties", {})
                    .get("schema_version", {})
                    .get("const")
                )
                if workgraph_version != "1.0":
                    errors.append("WorkGraph schema_version must be 1.0")

    if entries:
        wiki_entries = [
            entry for entry in entries
            if entry.get("name") == "wigtn-knowledge-wiki"
        ]
        if len(wiki_entries) != 1:
            errors.append("marketplace must contain wigtn-knowledge-wiki exactly once")
        else:
            wiki_root = plugin_roots.get("wigtn-knowledge-wiki")
            if wiki_root is None:
                errors.append("knowledge-wiki source directory must exist and match")
                wiki_root = ROOT / "plugins" / "wigtn-knowledge-wiki"
            try:
                wiki_manifest = load_json(wiki_root / ".codex-plugin" / "plugin.json")
            except ValueError as exc:
                errors.append(str(exc))
                wiki_manifest = {}
            if wiki_root.name != "wigtn-knowledge-wiki" or not wiki_root.is_dir():
                errors.append("knowledge-wiki source directory must exist and match")
            if wiki_manifest.get("name") != "wigtn-knowledge-wiki":
                errors.append("knowledge-wiki manifest name mismatch")
            wiki_version = str(wiki_manifest.get("version", ""))
            if not SEMVER.fullmatch(wiki_version):
                errors.append("knowledge-wiki version must be SemVer")
            elif core_version and wiki_version != core_version:
                errors.append(
                    "core and knowledge-wiki plugin versions must remain lockstep"
                )
            if wiki_manifest.get("skills") != "./skills/":
                errors.append("knowledge-wiki manifest skills path must be ./skills/")
            for unsupported in ("apps", "mcpServers", "hooks"):
                if unsupported in wiki_manifest:
                    errors.append(
                        f"knowledge-wiki manifest contains unsupported MVP field: {unsupported}"
                    )
            default_prompts = wiki_manifest.get("interface", {}).get("defaultPrompt", [])
            if not isinstance(default_prompts, list) or not 1 <= len(default_prompts) <= 3:
                errors.append(
                    "knowledge-wiki interface.defaultPrompt must contain 1 to 3 prompts"
                )
            wiki_skills = wiki_root / "skills"
            if not wiki_skills.is_dir():
                errors.append("knowledge-wiki skills directory is missing")
                wiki_names: set[str] = set()
            else:
                wiki_names = {
                    path.name for path in wiki_skills.iterdir() if path.is_dir()
                }
            if wiki_names != {"knowledge-wiki"}:
                errors.append("knowledge-wiki plugin must contain exactly one skill")
            wiki_yaml = wiki_skills / "knowledge-wiki" / "agents" / "openai.yaml"
            wiki_skill = wiki_skills / "knowledge-wiki" / "SKILL.md"
            try:
                wiki_meta = frontmatter(wiki_skill)
            except (OSError, ValueError) as exc:
                errors.append(str(exc))
            else:
                if set(wiki_meta) != {"name", "description"}:
                    errors.append(
                        "knowledge-wiki frontmatter must contain only name and description"
                    )
                if wiki_meta.get("name") != "knowledge-wiki":
                    errors.append("knowledge-wiki frontmatter name mismatch")
            if not wiki_yaml.is_file() or (
                "Use $wigtn-knowledge-wiki:knowledge-wiki"
                not in wiki_yaml.read_text(encoding="utf-8")
            ):
                errors.append("knowledge-wiki default prompt must use its qualified name")
            elif "allow_implicit_invocation: true" not in wiki_yaml.read_text(
                encoding="utf-8"
            ):
                errors.append("knowledge-wiki invocation policy mismatch")
            if not (wiki_root / "hooks" / "hooks.json").is_file():
                errors.append("knowledge-wiki plugin must contain its Stop hook")
            if not (wiki_root / "scripts" / "knowledge_wiki" / "capture.py").is_file():
                errors.append("knowledge-wiki capture script is missing")
            if not (wiki_root / "scripts" / "knowledge_wiki" / "doctor.py").is_file():
                errors.append("knowledge-wiki doctor script is missing")
            if (ROOT / "plugins" / "wigtn-plugins-with-codex" / "hooks").exists():
                errors.append("core plugin must not contain hooks")

    if errors:
        print("Repository validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Repository contract: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
