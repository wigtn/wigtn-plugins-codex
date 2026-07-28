#!/usr/bin/env python3
"""Regression check for sanitized packet export and tamper detection."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "scripts/export-eval-packet.py"
VERIFY = ROOT / "scripts/verify-eval-packet.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        run = root / "run"
        packet = root / "packet"
        (run / "runs/arm").mkdir(parents=True)
        (run / "homes").mkdir()
        (run / "blind/J56-home").mkdir(parents=True)
        (run / "exploratory").mkdir()
        (run / "runs/arm/sample.log").write_text(
            f"path={run}\nAuthorization: Bearer abcdefghijklmnop\n"
        )
        (run / "homes/auth.json").write_text('{"token":"secret-value"}')
        (run / "blind/J56-home/models_cache.json").write_text(
            '{"possibly_sensitive":"local runtime state"}'
        )
        (run / "exploratory/old.json").write_text('{"excluded":true}')
        subprocess.run(
            [
                sys.executable,
                str(EXPORT),
                "--exclude-prefix",
                "exploratory",
                str(packet),
                str(run),
            ],
            check=True,
            capture_output=True,
        )
        exported = (packet / "study-01/runs/arm/sample.log").read_text()
        assert "<RUN_ROOT>" in exported and "<REDACTED>" in exported
        assert not (packet / "study-01/homes/auth.json").exists()
        assert not (packet / "study-01/blind/J56-home/models_cache.json").exists()
        assert not (packet / "study-01/exploratory/old.json").exists()
        subprocess.run(
            [sys.executable, str(VERIFY), str(packet)],
            check=True,
            capture_output=True,
        )
        (packet / "study-01/runs/arm/sample.log").write_text("tampered")
        failed = subprocess.run(
            [sys.executable, str(VERIFY), str(packet)],
            capture_output=True,
        )
        assert failed.returncode == 1
    print("Eval packet: PASS (sanitize/hash/tamper)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
