#!/usr/bin/env python3
"""Self-contained regression checks for the opt-in knowledge-wiki pipeline."""

from __future__ import annotations

import json
import io
import os
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

    print("Knowledge wiki checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
