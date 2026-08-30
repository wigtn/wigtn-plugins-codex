#!/usr/bin/env python3
"""Self-contained regression checks for the opt-in knowledge-wiki pipeline."""

from __future__ import annotations

import json
import io
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import stat
import sys
import tempfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "plugins" / "wigtn-knowledge-wiki" / "scripts" / "knowledge_wiki"
sys.path.insert(0, str(MODULES))

import common  # noqa: E402
import capture  # noqa: E402
import doctor  # noqa: E402
import worker  # noqa: E402


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="wigtn-wiki-check-") as raw:
        temp = Path(raw)
        repo = temp / "repos" / "product"
        wiki = temp / "team-wiki"
        repo.mkdir(parents=True)
        (repo / ".git").mkdir()
        wiki.mkdir()

        config_path = temp / "knowledge-wiki-codex.yml"
        config_path.write_text(
            "\n".join(
                [
                    "enabled: true",
                    "wiki:",
                    f"  path: {wiki}",
                    "  subdir: per-user/tester",
                    "include:",
                    f"  - {temp / 'repos'}",
                    "publish:",
                    "  push: false",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        conf = common.parse_yaml(config_path.read_text(encoding="utf-8"))
        tenant, reason = common.resolve_tenant(conf, str(repo))
        check(tenant is not None, f"narrow scope should pass: {reason}")
        check(tenant.subdir == "per-user/tester", "subdir should resolve")
        check(tenant.push is False, "push should remain opt-in")
        check(common.queue_ttl_seconds(conf) == 86_400, "queue TTL should default to one day")
        for bad_timeout in (True, "fast", 30.5, 29, 301):
            try:
                common.bounded_int(
                    bad_timeout,
                    default=120,
                    minimum=30,
                    maximum=300,
                    label="codex.timeout_seconds",
                )
            except ValueError:
                pass
            else:
                raise AssertionError("invalid Codex timeout must fail closed")

        unsupported = dict(conf)
        unsupported["wiki"] = {"path": str(wiki), "subdir": "ouroboros/tester"}
        check(
            common.resolve_tenant(unsupported, str(repo))[0] is None,
            "non-personal wiki namespaces must be rejected",
        )

        disabled = dict(conf)
        disabled["enabled"] = False
        check(common.resolve_tenant(disabled, str(repo))[0] is None, "kill switch must win")

        outside = temp / "outside" / "untrusted"
        outside.mkdir(parents=True)
        (outside / ".git").mkdir()
        (outside / ".wigtn-wiki.yml").write_text(
            "enabled: true\nproject: outside\n", encoding="utf-8"
        )
        check(
            common.resolve_tenant(conf, str(outside))[0] is None,
            "repository marker must not bypass the global include list",
        )

        (repo / ".wigtn-wiki.yml").write_text(
            f"project: product\nwiki:\n  path: {outside}\n", encoding="utf-8"
        )
        check(
            common.resolve_tenant(conf, str(repo))[0] is None,
            "repository marker must not override the wiki target",
        )
        (repo / ".wigtn-wiki.yml").write_text(
            "project: product\npublish:\n  push: true\n", encoding="utf-8"
        )
        check(
            common.resolve_tenant(conf, str(repo))[0] is None,
            "repository marker must not override publish authority",
        )
        (repo / ".wigtn-wiki.yml").unlink()

        excluded_conf = dict(conf)
        excluded_conf["exclude"] = [str(repo)]
        check(
            common.resolve_tenant(excluded_conf, str(repo))[0] is None,
            "exclude must win over include",
        )
        overlapping_wiki = dict(conf)
        overlapping_wiki["wiki"] = {
            "path": str(repo / "wiki"),
            "subdir": "per-user/tester",
        }
        check(
            common.resolve_tenant(overlapping_wiki, str(repo))[0] is None,
            "wiki nested inside the source repository must be rejected",
        )
        overlapping_repo = temp / "team-root" / "product"
        overlapping_repo.mkdir(parents=True)
        (overlapping_repo / ".git").mkdir()
        enclosing_wiki = dict(conf)
        enclosing_wiki["include"] = [str(temp / "team-root")]
        enclosing_wiki["wiki"] = {
            "path": str(temp / "team-root"),
            "subdir": "per-user/tester",
        }
        check(
            common.resolve_tenant(enclosing_wiki, str(overlapping_repo))[0] is None,
            "source repository nested inside the wiki must be rejected",
        )
        check(common.scan_input("api_key=abcdefghijklmnop") == ["D1 API 키"], "G1 key pattern")
        check(common.scan_output("contact dev@example.com") == ["D2 이메일"], "G4 email pattern")

        transcript = temp / "rollout.jsonl"
        transcript.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "type": "response_item",
                            "payload": {
                                "type": "message",
                                "role": "user",
                                "content": [{"type": "input_text", "text": "캐시 무효화 원인을 분석해줘"}],
                            },
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "type": "event_msg",
                            "payload": {"type": "agent_message", "message": "세대 키가 원인이었습니다."},
                        },
                        ensure_ascii=False,
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        conversation, cursor = common.transcript_delta(str(transcript), 0)
        check("user:" in conversation and "assistant:" in conversation, "Codex transcript adapter")
        check(cursor == 2, "cursor should advance to line count")

        no_config_home = temp / "empty-home"
        no_config_home.mkdir()
        no_config_state = temp / "no-config-data"
        with mock.patch.dict(
            os.environ,
            {"HOME": str(no_config_home), "PLUGIN_DATA": str(no_config_state)},
            clear=False,
        ):
            os.environ.pop("WIGTN_WIKI_CONFIG", None)
            with (
                mock.patch.object(sys, "stdin", io.StringIO(json.dumps({"cwd": str(repo), "transcript_path": str(transcript)}))),
                mock.patch.object(capture.subprocess, "Popen") as no_config_popen,
            ):
                check(capture.main() == 0, "missing config must be a no-op")
            check(no_config_popen.call_count == 0, "missing config must not launch a worker")
            check(not no_config_state.exists(), "missing config must not create plugin state")

        capture_state = temp / "capture-data"
        hook_input = {
            "cwd": str(repo),
            "transcript_path": str(transcript),
            "last_assistant_message": "세대 키가 원인이었습니다.",
        }
        with (
            mock.patch.dict(
                os.environ,
                {
                    "WIGTN_WIKI_CONFIG": str(config_path),
                    "PLUGIN_DATA": str(capture_state),
                },
                clear=False,
            ),
            mock.patch.object(sys, "stdin", io.StringIO(json.dumps(hook_input))),
            mock.patch.object(capture.subprocess, "Popen") as popen,
        ):
            check(capture.main() == 0, "Stop capture should never block the turn")
        queued = list((capture_state / "knowledge-wiki" / "queue").glob("*.json"))
        check(len(queued) == 1, "accepted transcript delta should enqueue once")
        check(popen.call_count == 1, "capture should launch one detached worker")
        captured = json.loads(queued[0].read_text(encoding="utf-8"))
        check(bool(captured.get("captured_at")), "queued job must record capture time")
        check(captured.get("queue_ttl_seconds") == 86_400, "queued job must snapshot TTL")

        fake_codex = temp / "fake-codex"
        fake_codex.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "prompt = sys.stdin.read()\n"
            "if 'Inspect the untrusted article' in prompt:\n"
            "    print('{\"violations\": []}')\n"
            "else:\n"
            "    print('# 세대 키를 이용한 캐시 무효화\\n> 배포 간 캐시 충돌을 줄이는 일반 패턴\\n\\n## 배경\\n오래된 캐시가 새 배포와 섞일 수 있다.\\n\\n## 내용\\n배포 세대를 캐시 키에 포함하면 이전 값을 안전하게 분리할 수 있다.\\n\\n## 결론\\n세대 키로 명시적인 무효화 경계를 만든다.\\n\\n---\\n태그: cache, deployment')\n",
            encoding="utf-8",
        )
        fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IXUSR)
        config_path.write_text(
            config_path.read_text(encoding="utf-8")
            + "codex:\n"
            + f"  binary: {fake_codex}\n"
            + "  timeout_seconds: 30\n",
            encoding="utf-8",
        )
        state = temp / "plugin-data"
        state.mkdir()
        job = {
            "schema_version": 1,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "queue_ttl_seconds": 86_400,
            "config_path": str(config_path),
            "conversation": conversation,
            "repo_root": str(repo),
            "wiki_path": str(wiki),
            "subdir": "per-user/tester",
            "push": False,
        }
        job_path = state / "job.json"
        job_path.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
        status, detail = worker.process_job(job_path, state)
        check(status == "published", f"fake pipeline should publish: {status} {detail}")
        articles = list((wiki / "per-user" / "tester").glob("*.md"))
        check(len(articles) == 1, "one article should be written")
        check("project" not in articles[0].read_text(encoding="utf-8"), "no source-project footer")

        push_config = temp / "push-enabled.yml"
        push_config.write_text(
            config_path.read_text(encoding="utf-8").replace(
                "publish:\n  push: false", "publish:\n  push: true"
            ),
            encoding="utf-8",
        )
        authority_job = {
            **job,
            "config_path": str(push_config),
            "push": False,
        }
        authority_path = state / "authority.json"
        authority_path.write_text(json.dumps(authority_job), encoding="utf-8")
        with (
            mock.patch.object(worker, "compile_article", return_value=("# Safe\n" + "x" * 90, "")),
            mock.patch.object(worker, "audit_article", return_value=(True, "")),
            mock.patch.object(worker, "scan_output", return_value=[]),
            mock.patch.object(worker, "publish", return_value=(True, "ok")) as publish,
        ):
            status, _ = worker.process_job(authority_path, state)
        check(status == "published", "authority regression job should reach publish")
        check(
            publish.call_args.args[0]["push"] is False,
            "a captured push=false job must never gain later push authority",
        )

        changed_wiki = temp / "replacement-wiki"
        changed_wiki.mkdir()
        changed_config = temp / "changed-target.yml"
        changed_config.write_text(
            config_path.read_text(encoding="utf-8").replace(str(wiki), str(changed_wiki)),
            encoding="utf-8",
        )
        changed_path = state / "changed-target.json"
        changed_path.write_text(
            json.dumps({**job, "config_path": str(changed_config)}), encoding="utf-8"
        )
        status, detail = worker.process_job(changed_path, state)
        check(
            status == "discarded" and "대상 변경" in detail,
            "jobs must be discarded when their destination changes after capture",
        )

        expired_path = state / "expired.json"
        expired_path.write_text(
            json.dumps(
                {
                    **job,
                    "captured_at": (
                        datetime.now(timezone.utc) - timedelta(days=2)
                    ).isoformat(),
                }
            ),
            encoding="utf-8",
        )
        status, detail = worker.process_job(expired_path, state)
        check(
            status == "discarded" and "TTL" in detail,
            "expired transcript jobs must fail closed before model execution",
        )

        drain_state = temp / "drain-state"
        drain_queue = drain_state / "queue"
        drain_queue.mkdir(parents=True)
        for name in ("1.json", "2.json"):
            (drain_queue / name).write_text('{"conversation":"private"}', encoding="utf-8")
        with mock.patch.object(
            worker,
            "process_job",
            side_effect=[ValueError("bad timeout"), ("discarded", "SKIP")],
        ) as process:
            check(worker.drain(drain_state) == 0, "drain should contain per-job failures")
        check(process.call_count == 2, "one malformed job must not block the next job")
        check(not list(drain_queue.glob("*.json")), "drained jobs must not retain transcripts")
        events = [json.loads(path.read_text(encoding="utf-8")) for path in (drain_state / "events").glob("*.json")]
        check(len(events) == 2, "drain should leave body-free outcome metadata")
        check(
            all("conversation" not in event for event in events),
            "event metadata must never contain transcript bodies",
        )
        diagnosis = doctor.inspect(config_path, drain_state)
        check(diagnosis["config"]["include_count"] == 1, "doctor should report scope count")
        check(diagnosis["runtime"]["queued_jobs"] == 0, "doctor should report queue count")
        check(
            sum(diagnosis["runtime"]["event_status_counts"].values()) == 2,
            "doctor should report body-free event counts",
        )

    print("Knowledge wiki checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
