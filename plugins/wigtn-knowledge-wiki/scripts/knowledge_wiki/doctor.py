#!/usr/bin/env python3
"""Report body-free configuration and runtime health for Knowledge Wiki."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import time
from typing import Any

from common import load_config, parse_yaml, queue_ttl_seconds


def configured_binary(conf: dict[str, Any]) -> str:
    codex = conf.get("codex") if isinstance(conf.get("codex"), dict) else {}
    return str(codex.get("binary") or os.environ.get("WIGTN_WIKI_CODEX_BIN") or "codex")


def binary_available(binary: str) -> bool:
    path = Path(binary).expanduser()
    if path.parent != Path("."):
        return path.is_file() and os.access(path, os.X_OK)
    return shutil.which(binary) is not None


def event_counts(state: Path | None) -> dict[str, int]:
    counts: Counter[str] = Counter()
    if state is None:
        return {}
    events = state / "events"
    for path in events.glob("*.json") if events.is_dir() else []:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            counts["malformed"] += 1
            continue
        status = value.get("status") or value.get("stage") or "unknown"
        counts[str(status)] += 1
    return dict(sorted(counts.items()))


def inspect(config_path: Path | None, state: Path | None) -> dict[str, Any]:
    errors: list[str] = []
    conf: dict[str, Any] = {}
    if config_path is None:
        errors.append("config not found")
    else:
        try:
            conf = parse_yaml(config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            errors.append("config is unreadable or invalid")
    try:
        ttl = queue_ttl_seconds(conf)
    except ValueError as exc:
        ttl = None
        errors.append(str(exc))

    wiki = conf.get("wiki") if isinstance(conf.get("wiki"), dict) else {}
    includes = conf.get("include") if isinstance(conf.get("include"), list) else []
    excludes = conf.get("exclude") if isinstance(conf.get("exclude"), list) else []
    if config_path is not None and conf.get("enabled") is True:
        if not includes:
            errors.append("enabled config has no include scope")
        if not str(wiki.get("path") or "").strip():
            errors.append("enabled config has no wiki.path")
        if not str(wiki.get("subdir") or "").strip().startswith("per-user/"):
            errors.append("enabled config has no personal wiki.subdir")

    queue_files = (
        list((state / "queue").glob("*.json"))
        if state is not None and (state / "queue").is_dir()
        else []
    )
    oldest = None
    if queue_files:
        try:
            oldest = round(max(0.0, time.time() - min(path.stat().st_mtime for path in queue_files)))
        except OSError:
            oldest = None
    binary = configured_binary(conf)
    result = {
        "healthy": not errors,
        "errors": errors,
        "config": {
            "path": str(config_path) if config_path else None,
            "enabled": conf.get("enabled") is True,
            "include_count": len(includes),
            "exclude_count": len(excludes),
            "wiki_subdir": str(wiki.get("subdir") or "") or None,
            "push_enabled": (
                conf.get("publish", {}).get("push") is True
                if isinstance(conf.get("publish"), dict)
                else False
            ),
            "queue_ttl_seconds": ttl,
        },
        "runtime": {
            "codex_binary": binary,
            "codex_available": binary_available(binary),
            "state_available": state is not None and state.is_dir(),
            "queued_jobs": len(queue_files),
            "oldest_queued_seconds": oldest,
            "event_status_counts": event_counts(state),
        },
    }
    if not result["runtime"]["codex_available"]:
        result["healthy"] = False
        result["errors"].append("configured Codex binary is unavailable")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.config:
        config_path = args.config.expanduser()
    else:
        _, config_path = load_config()
    state = args.state.expanduser() if args.state else None
    if state is None and os.environ.get("PLUGIN_DATA"):
        state = Path(os.environ["PLUGIN_DATA"]).expanduser() / "knowledge-wiki"
    result = inspect(config_path, state)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Knowledge Wiki doctor: " + ("PASS" if result["healthy"] else "ATTENTION"))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
