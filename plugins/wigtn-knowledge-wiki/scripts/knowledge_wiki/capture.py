#!/usr/bin/env python3
"""Fast Stop hook: gate a Codex transcript delta and enqueue background work."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from common import (
    cursor_path,
    load_config,
    read_cursor,
    resolve_tenant,
    scan_input,
    transcript_delta,
    write_json_atomic,
)


def main() -> int:
    try:
        hook = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return 0
    plugin_data = os.environ.get("PLUGIN_DATA")
    if not plugin_data:
        return 0
    conf, config_path = load_config()
    tenant, _ = resolve_tenant(conf, str(hook.get("cwd") or ""))
    if tenant is None or config_path is None:
        return 0
    transcript_path = str(hook.get("transcript_path") or "")
    if not transcript_path:
        return 0

    state = Path(plugin_data) / "knowledge-wiki"
    cursor = cursor_path(state, transcript_path)
    conversation, next_line = transcript_delta(
        transcript_path,
        read_cursor(cursor),
        str(hook.get("last_assistant_message") or ""),
    )
    if not conversation.strip():
        return 0
    hits = scan_input(conversation)
    if hits:
        write_json_atomic(
            state / "events" / f"blocked-{time.time_ns()}.json",
            {"stage": "G1", "hits": hits},
        )
        cursor.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        cursor.write_text(str(next_line), encoding="utf-8")
        cursor.chmod(0o600)
        return 0

    job_id = f"{time.time_ns()}-{os.getpid()}"
    write_json_atomic(
        state / "queue" / f"{job_id}.json",
        {
            "schema_version": 1,
            "config_path": str(config_path),
            "conversation": conversation,
            "repo_root": str(tenant.repo_root),
            "wiki_path": str(tenant.wiki_path),
            "subdir": tenant.subdir,
            "push": tenant.push,
        },
    )
    cursor.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    cursor.write_text(str(next_line), encoding="utf-8")
    cursor.chmod(0o600)

    worker = Path(__file__).with_name("worker.py")
    subprocess.Popen(
        [sys.executable, str(worker), "--state", str(state)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(0)
