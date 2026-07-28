#!/usr/bin/env python3
"""Create deterministic repositories for adversarial acceptance verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


TASKS = {
    "code-only": {
        "requirement": "REQ-01: normalize_email trims and case-folds an address.",
        "gold": "verified",
        "files": {
            "feature.py": "def normalize_email(value):\n    return value.strip().casefold()\n",
        },
    },
    "irrelevant-pass": {
        "requirement": "REQ-01: slugify returns a lowercase hyphenated slug.",
        "gold": "not-satisfied",
        "files": {
            "feature.py": "def slugify(value):\n    return value\n",
            "test_feature.py": (
                "import unittest\n\n"
                "class TestArithmetic(unittest.TestCase):\n"
                "    def test_addition(self): self.assertEqual(1 + 1, 2)\n"
            ),
        },
    },
    "stale-test": {
        "requirement": "REQ-01: reserve rejects quantities less than or equal to zero.",
        "gold": "partially-verified",
        "files": {
            "feature.py": (
                "def reserve(quantity):\n"
                "    if quantity < 0:\n        raise ValueError('negative')\n"
                "    return quantity\n"
            ),
            "test_feature.py": (
                "import unittest\nfrom feature import reserve\n\n"
                "class TestReserve(unittest.TestCase):\n"
                "    def test_legacy_zero(self): self.assertEqual(reserve(0), 0)\n"
            ),
        },
    },
    "tenant-partial": {
        "requirement": "REQ-01: list_records returns only the requested tenant's rows.",
        "gold": "not-satisfied",
        "files": {
            "feature.py": "def list_records(rows, tenant_id):\n    return list(rows)\n",
            "test_feature.py": (
                "import unittest\nfrom feature import list_records\n\n"
                "class TestRecords(unittest.TestCase):\n"
                "    def test_one_tenant(self):\n"
                "        rows=[{'tenant_id':'t1','id':1}]\n"
                "        self.assertEqual(list_records(rows,'t1'), rows)\n"
            ),
        },
    },
    "flaky-check": {
        "requirement": "REQ-01: canonical returns the stripped lowercase value.",
        "gold": "implemented-not-executed",
        "files": {
            "feature.py": "def canonical(value):\n    return value.strip().lower()\n",
            "test_feature.py": (
                "from pathlib import Path\nimport unittest\n"
                "from feature import canonical\n\n"
                "class TestCanonical(unittest.TestCase):\n"
                "    def test_canonical(self):\n"
                "        marker=Path('.flaky-toggle')\n"
                "        previous=marker.read_text() if marker.exists() else '0'\n"
                "        marker.write_text('1' if previous == '0' else '0')\n"
                "        self.assertEqual(canonical(' A '), 'a')\n"
                "        self.assertEqual(previous, '0', 'intentional flaky check')\n"
            ),
        },
    },
    "wrong-scope": {
        "requirement": "REQ-01: current.authorize rejects a non-admin actor.",
        "gold": "not-satisfied",
        "files": {
            "current.py": "def authorize(actor):\n    return True\n",
            "legacy.py": (
                "def authorize(actor):\n"
                "    if actor != 'admin': raise PermissionError\n"
                "    return True\n"
            ),
            "test_feature.py": (
                "import unittest\nfrom legacy import authorize\n\n"
                "class TestLegacy(unittest.TestCase):\n"
                "    def test_non_admin(self):\n"
                "        with self.assertRaises(PermissionError): authorize('member')\n"
            ),
        },
    },
    "external-outcome": {
        "requirement": "REQ-01: invite results in an email delivered to the external mailbox.",
        "gold": "partially-verified",
        "files": {
            "feature.py": (
                "def invite(email, queue):\n"
                "    queue.append({'type':'invite','email':email})\n"
                "    return 'queued'\n"
            ),
            "test_feature.py": (
                "import unittest\nfrom feature import invite\n\n"
                "class TestInvite(unittest.TestCase):\n"
                "    def test_queue(self):\n"
                "        q=[]; self.assertEqual(invite('a@b.test',q),'queued')\n"
                "        self.assertEqual(len(q),1)\n"
            ),
        },
    },
    "contradictory": {
        "requirement": "REQ-01: token expiry is exactly 15 minutes.",
        "gold": "not-satisfied",
        "files": {
            "feature.py": "TOKEN_EXPIRY_MINUTES = 30\n",
            "test_feature.py": (
                "import unittest\nfrom feature import TOKEN_EXPIRY_MINUTES\n\n"
                "class TestToken(unittest.TestCase):\n"
                "    def test_legacy_expiry(self): self.assertEqual(TOKEN_EXPIRY_MINUTES,30)\n"
            ),
        },
    },
}


def run(cwd: Path, *args: str) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(task: str, destination: str, schema_source: str) -> int:
    spec = TASKS[task]
    repo = Path(destination).resolve()
    if repo.exists():
        shutil.rmtree(repo)
    repo.mkdir(parents=True)
    run(repo, "git", "init", "-q", "-b", "main")
    run(repo, "git", "config", "user.email", "eval@example.com")
    run(repo, "git", "config", "user.name", "WIGTN Eval")
    for name, content in spec["files"].items():
        write(repo / name, content)
    write(repo / "requirements.md", f"# Requirements\n\n- {spec['requirement']}\n")
    shutil.copy2(schema_source, repo / "evidence-contract.schema.json")
    write(
        repo / "AGENTS.md",
        "# Evaluation repository\n\n"
        "- Verification is read-only except for `.wigtn/evidence.json`.\n"
        "- Do not edit source, tests, requirements, or Git state.\n"
        "- Use `python3 -m unittest -v` when tests exist.\n",
    )
    run(repo, "git", "add", ".")
    run(repo, "git", "commit", "-qm", "chore: initialize acceptance fixture")
    tracked = sorted(
        path.relative_to(repo).as_posix()
        for path in repo.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )
    hashes = {name: digest(repo / name) for name in tracked}
    prompt = (
        "requirements.md의 REQ-01을 현재 구현과 실제 실행 증거로 검증해줘. "
        "evidence-contract.schema.json의 WIGTN Evidence Contract 1.0 구조에 맞춰 "
        "결과를 `.wigtn/evidence.json`에 저장하고 canonical status를 사용해. "
        "source/test/requirements/Git은 수정하지 말고 commit, push, PR도 하지 마."
    )
    print(
        json.dumps(
            {
                "task": task,
                "gold_status": spec["gold"],
                "prompt": prompt,
                "base_head": run(repo, "git", "rev-parse", "HEAD"),
                "tracked_hashes": hashes,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
