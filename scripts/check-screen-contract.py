#!/usr/bin/env python3
"""Regression checks for selected and bundled screen artifacts."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "plugins/wigtn-plugins-with-codex/scripts/validate-screen-spec.py"


VALID = {
    "01-IA.md": "# Information Architecture\n\n| Page | FR |\n|---|---|\n| /x | FR-001 |\n",
    "02-USER-FLOW.md": (
        "# User Flow\n\n```mermaid\nflowchart LR\nA --> B\n```\n\n"
        "## Flow Coverage\n\n| AC | Flow |\n|---|---|\n| AC-001 | A |\n"
    ),
    "03-SCREEN-SPEC.md": (
        "# Screen Specifications\n\n## Screen: /x\n\n"
        "| Linked FRs | FR-001 |\n|---|---|\n"
        "\n### Wireframe Anchor\n\n→ `04-WIREFRAME.html#screen-x`\n"
    ),
    "04-WIREFRAME.html": (
        '<!doctype html><html><head><meta name="viewport" '
        'content="width=device-width"></head><body>'
        '<section id="screen-x">X</section>'
        "</body></html>\n"
    ),
    "05-DEV-HANDOFF.md": (
        "# Dev Handoff\n\n| FR | Screen |\n|---|---|\n| FR-001 | /x |\n\n"
        "## Suggested Implementation Order\n\n1. X\n"
    ),
}

KOREAN_IA = """# 조직 관리자 팀원 초대 기능 IA

## 페이지 및 경로

| ID | 정보 단위 | 권장 경로 | 접근 권한 |
|---|---|---|---|
| IA-ORG-01 | 팀원 관리 | `/organizations/:orgId/members` | 관리자 |
"""


def run(directory: Path, artifacts: str = "all") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            str(directory),
            "--artifacts",
            artifacts,
            "--json",
        ],
        text=True,
        capture_output=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        valid = root / "valid"
        valid.mkdir()
        for name, text in VALID.items():
            (valid / name).write_text(text, encoding="utf-8")
        passed = run(valid)
        assert passed.returncode == 0 and '"valid": true' in passed.stdout

        ia_only = root / "ia-only"
        ia_only.mkdir()
        (ia_only / "01-IA.md").write_text(VALID["01-IA.md"], encoding="utf-8")
        passed = run(ia_only, "ia")
        assert passed.returncode == 0 and '"valid": true' in passed.stdout

        korean_ia = root / "korean-ia"
        korean_ia.mkdir()
        (korean_ia / "01-IA.md").write_text(KOREAN_IA, encoding="utf-8")
        passed = run(korean_ia, "ia")
        assert passed.returncode == 0 and '"valid": true' in passed.stdout

        prose_only = root / "prose-only-ia"
        prose_only.mkdir()
        (prose_only / "01-IA.md").write_text(
            "# IA\n\n페이지와 경로를 나중에 정합니다.\n", encoding="utf-8"
        )
        failed = run(prose_only, "ia")
        assert failed.returncode == 1
        assert "missing structured page map" in failed.stdout

        flow_only = root / "flow-only"
        flow_only.mkdir()
        (flow_only / "02-USER-FLOW.md").write_text(
            VALID["02-USER-FLOW.md"], encoding="utf-8"
        )
        passed = run(flow_only, "flow")
        assert passed.returncode == 0 and '"valid": true' in passed.stdout

        wireframe = root / "wireframe"
        wireframe.mkdir()
        for name in ("01-IA.md", "03-SCREEN-SPEC.md", "04-WIREFRAME.html"):
            (wireframe / name).write_text(VALID[name], encoding="utf-8")
        passed = run(wireframe, "wireframe")
        assert passed.returncode == 0 and '"valid": true' in passed.stdout

        missing_closure = root / "missing-closure"
        missing_closure.mkdir()
        (missing_closure / "04-WIREFRAME.html").write_text(
            VALID["04-WIREFRAME.html"], encoding="utf-8"
        )
        failed = run(missing_closure, "wireframe")
        assert failed.returncode == 1 and "missing artifact" in failed.stdout

        broken = root / "broken"
        broken.mkdir()
        for name, text in VALID.items():
            (broken / name).write_text(text, encoding="utf-8")
        (broken / "04-WIREFRAME.html").write_text(
            '<section id="screen-other">{feature-name}</section>\n',
            encoding="utf-8",
        )
        failed = run(broken)
        assert failed.returncode == 1
        assert "unresolved template placeholders" in failed.stdout
        assert "missing referenced anchor #screen-x" in failed.stdout

        remote = root / "remote-wireframe"
        remote.mkdir()
        for name in ("01-IA.md", "03-SCREEN-SPEC.md"):
            (remote / name).write_text(VALID[name], encoding="utf-8")
        (remote / "04-WIREFRAME.html").write_text(
            '<!doctype html><html><head><meta name="viewport" content="width=device-width">'
            '<script src="https://cdn.example.test/ui.js"></script></head>'
            '<body><section id="screen-x">X</section></body></html>\n',
            encoding="utf-8",
        )
        failed = run(remote, "wireframe")
        assert failed.returncode == 1
        assert "external network resource" in failed.stdout

        broken_link = root / "broken-link"
        broken_link.mkdir()
        for name in ("01-IA.md", "03-SCREEN-SPEC.md"):
            (broken_link / name).write_text(VALID[name], encoding="utf-8")
        (broken_link / "04-WIREFRAME.html").write_text(
            '<!doctype html><html><head><meta name="viewport" '
            'content="width=device-width"></head><body>'
            '<a href="#screen-missing">Missing</a>'
            '<section id="screen-x">X</section></body></html>\n',
            encoding="utf-8",
        )
        failed = run(broken_link, "wireframe")
        assert failed.returncode == 1
        assert "broken internal link #screen-missing" in failed.stdout
    print(
        "Screen contract: PASS "
        "(selected/closure/multilingual-ia/bundle/anchor/requirement)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
