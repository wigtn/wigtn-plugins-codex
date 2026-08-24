"""Configuration, scope, transcript, and deterministic safety primitives."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIG_NAME = "knowledge-wiki-codex.yml"
MARKER_NAME = ".wigtn-wiki.yml"
MAX_CONVERSATION_CHARS = 15_000


def parse_yaml(text: str) -> dict[str, Any]:
    """Parse the small supported config shape without requiring PyYAML."""
    try:
        import yaml  # type: ignore[import-untyped]

        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except ImportError:
        pass

    result: dict[str, Any] = {}
    section: str | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line and not line.strip().startswith("- "):
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            if section is None:
                continue
            bucket = result.get(section)
            if not isinstance(bucket, list):
                bucket = []
                result[section] = bucket
            bucket.append(stripped[2:].strip().strip("'\""))
            continue
        key, _, value = stripped.partition(":")
        key, value = key.strip(), value.strip().strip("'\"")
        if not line.startswith(" "):
            result[key] = _scalar(value) if value else {}
            section = None if value else key
        elif section is not None:
            bucket = result.get(section)
            if not isinstance(bucket, dict):
                bucket = {}
                result[section] = bucket
            bucket[key] = _scalar(value)
    return result


def _scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if lowered in {"null", "none", "~"}:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def config_candidates() -> list[Path]:
    paths: list[Path] = []
    if override := os.environ.get("WIGTN_WIKI_CONFIG"):
        paths.append(Path(override).expanduser())
    if xdg := os.environ.get("XDG_CONFIG_HOME"):
        paths.append(Path(xdg).expanduser() / "wigtn" / CONFIG_NAME)
    paths.extend(
        [
            Path.home() / ".config" / "wigtn" / CONFIG_NAME,
            Path.home() / ".wigtn" / CONFIG_NAME,
        ]
    )
    return paths


def load_config() -> tuple[dict[str, Any], Path | None]:
    for path in config_candidates():
        try:
            if path.is_file():
                return parse_yaml(path.read_text(encoding="utf-8")), path
        except (OSError, ValueError):
            continue
    return {}, None


def enabled(conf: dict[str, Any]) -> bool:
    """Codex capture is deliberately opt-in."""
    return conf.get("enabled") is True


def _paths(value: Any) -> list[Path]:
    items = value if isinstance(value, list) else [value] if value else []
    result: list[Path] = []
    for item in items:
        try:
            result.append(Path(str(item)).expanduser().resolve())
        except (OSError, RuntimeError, ValueError):
            continue
    return result


def _under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _locate_repo(start: Path) -> tuple[Path, Path | None]:
    current = start.resolve()
    marker: Path | None = None
    for candidate in (current, *current.parents):
        if marker is None and (candidate / MARKER_NAME).is_file():
            marker = candidate / MARKER_NAME
        if (candidate / ".git").exists():
            return candidate, marker
    return (marker.parent if marker else current), marker


@dataclass(frozen=True)
class Tenant:
    repo_root: Path
    wiki_path: Path
    subdir: str
    project: str
    push: bool


def resolve_tenant(conf: dict[str, Any], cwd: str) -> tuple[Tenant | None, str]:
    if not enabled(conf):
        return None, "Codex 위키가 비활성"
    try:
        start = Path(cwd).resolve() if cwd else Path.cwd().resolve()
    except (OSError, RuntimeError, ValueError):
        return None, "cwd 해석 실패"
    rendered = f"/{start.as_posix().strip('/')}/"
    if any(part in rendered for part in ("/node_modules/", "/.venv/", "/vendor/", "/site-packages/")):
        return None, "deny 경로"

    repo_root, marker_path = _locate_repo(start)
    marker: dict[str, Any] = {}
    if marker_path:
        try:
            marker = parse_yaml(marker_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None, "마커 파싱 실패"
        unknown = set(marker) - {"enabled", "project"}
        if unknown:
            return None, "마커에 허용되지 않은 키"
        if marker.get("enabled") is False:
            return None, "repo 마커에서 비활성"

    excluded = _paths(conf.get("exclude"))
    if any(repo_root == path or _under(repo_root, path) for path in excluded):
        return None, "exclude 매칭"
    included = _paths(conf.get("include"))
    if not included:
        return None, "include 미설정"
    if not any(repo_root == path or _under(repo_root, path) for path in included):
        return None, "include 범위 밖"

    global_wiki = conf.get("wiki") if isinstance(conf.get("wiki"), dict) else {}
    raw_path = str(global_wiki.get("path") or "").strip()
    subdir = str(global_wiki.get("subdir") or "").strip("/")
    if not raw_path or not subdir:
        return None, "wiki.path 또는 wiki.subdir 미설정"
    if ".." in Path(subdir).parts or not subdir.startswith("per-user/"):
        return None, "자동 발행은 per-user/만 허용"

    wiki_path = Path(raw_path).expanduser()
    try:
        wiki_resolved = wiki_path.resolve()
        root_resolved = repo_root.resolve()
        if wiki_resolved == root_resolved or _under(wiki_resolved, root_resolved):
            return None, "위키가 작업 repo 안에 있음"
    except (OSError, RuntimeError):
        return None, "위키 경로 해석 실패"

    publish = conf.get("publish") if isinstance(conf.get("publish"), dict) else {}
    push = publish.get("push") is True
    if push:
        try:
            home = Path.home().resolve()
            if any(path == home or path == Path(path.anchor) for path in _paths(conf.get("include"))):
                push = False
        except (OSError, RuntimeError):
            push = False
    project = str(marker.get("project") or conf.get("project") or repo_root.name)
    return Tenant(repo_root, wiki_path, subdir, project, push), ""


_INPUT_PATTERNS = [
    (r"(?:api[_-]?key|apikey|access[_-]?token|secret[_-]?key)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}", "D1 API 키"),
    (r"AKIA[0-9A-Z]{16}", "D1 AWS 액세스 키"),
    (r"(?:sk|pk)-[A-Za-z0-9]{20,}", "D1 provider 키"),
    (r"gh[pousr]_[A-Za-z0-9]{20,}", "D1 GitHub 토큰"),
    (r"Bearer\s+[A-Za-z0-9_\-.]{20,}", "D1 Bearer 토큰"),
    (r"-----BEGIN\s+[A-Z ]*PRIVATE KEY-----", "D1 개인키"),
    (r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:/@]+:[^\s@]{4,}@", "D1 접속 문자열"),
    (r"\b\d{6}\s*-\s*[1-4]\d{6}\b", "D2 주민등록번호"),
]
_OUTPUT_ONLY_PATTERNS = [
    (r"(?<![\w.+\-])(?!(?:git|noreply|no-reply|admin|root)@)[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", "D2 이메일"),
    (r"\b01[016-9]-?\d{3,4}-?\d{4}\b", "D2 휴대전화"),
    (r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b", "D4 사설 IP"),
    (r"https?://(?:localhost|127\.0\.0\.1|[\w\-]+\.(?:internal|local|corp|intra|lan))\b", "D4 내부 URL"),
    (r"\b[\w\-]+\.(?:internal|local|corp|intra|lan)\b", "D4 내부 호스트명"),
    (r"/(?:Users|home)/[A-Za-z0-9._\-]+/", "D6 사용자 홈 절대경로"),
    (r"[A-Z]:\\\\?Users\\\\?[A-Za-z0-9._\-]+", "D6 Windows 사용자 경로"),
]


def _scan(text: str, patterns: list[tuple[str, str]]) -> list[str]:
    return list(dict.fromkeys(label for pattern, label in patterns if re.search(pattern, text, re.I)))


def scan_input(text: str) -> list[str]:
    return _scan(text, _INPUT_PATTERNS)


def scan_output(text: str) -> list[str]:
    return _scan(text, _INPUT_PATTERNS + _OUTPUT_ONLY_PATTERNS)


def transcript_delta(path: str, start_line: int, last_assistant: str = "") -> tuple[str, int]:
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return "", start_line
    if start_line < 0 or start_line > len(lines):
        start_line = 0
    chunks: list[str] = []
    seen: set[tuple[str, str]] = set()

    def add(role: Any, value: Any) -> None:
        if role not in {"user", "assistant"} or not isinstance(value, str):
            return
        cleaned = value.strip()
        key = (str(role), cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            chunks.append(f"{role}: {cleaned}")

    for raw in lines[start_line:]:
        try:
            event = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else event
        kind = payload.get("type")
        if event.get("type") == "response_item" and kind == "message":
            role = payload.get("role")
            content = payload.get("content")
            if isinstance(content, str):
                add(role, content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        add(role, block.get("text"))
        elif event.get("type") == "event_msg" and kind in {"user_message", "agent_message"}:
            add("user" if kind == "user_message" else "assistant", payload.get("message"))
        elif isinstance(payload.get("message"), dict):
            message = payload["message"]
            content = message.get("content")
            if isinstance(content, str):
                add(message.get("role"), content)
    add("assistant", last_assistant)
    conversation = "\n".join(chunks)
    return conversation[-MAX_CONVERSATION_CHARS:], len(lines)


def cursor_path(state_root: Path, transcript_path: str) -> Path:
    digest = hashlib.sha256(transcript_path.encode("utf-8")).hexdigest()[:24]
    return state_root / "cursors" / digest


def read_cursor(path: Path) -> int:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    temp.chmod(0o600)
    temp.replace(path)
