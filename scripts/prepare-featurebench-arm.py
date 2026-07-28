#!/usr/bin/env python3
"""Prepare a host-editable FeatureBench arm without exposing gold/F2P tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def safe_relative(root: Path, raw: str) -> Path:
    relative = Path(raw.removeprefix("/testbed/"))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe task path: {raw}")
    target = (root / relative).resolve()
    if root not in target.parents:
        raise ValueError(f"task path escapes workspace: {raw}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance-json", required=True, type=Path)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--container-name", required=True)
    parser.add_argument("--plugin-root", type=Path)
    args = parser.parse_args()

    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing workspace: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    instance = json.loads(args.instance_json.read_text(encoding="utf-8"))
    corruption_patch = instance["patch"]
    fail_to_pass = instance["FAIL_TO_PASS"]
    if not corruption_patch or not fail_to_pass:
        raise SystemExit("instance must contain patch and FAIL_TO_PASS")

    source_container = run(
        "docker",
        "create",
        "--entrypoint",
        "sleep",
        args.image,
        "infinity",
        capture=True,
    )
    try:
        output.mkdir()
        run("docker", "cp", f"{source_container}:/root/my_repo/.", str(output))
    finally:
        run("docker", "rm", source_container)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".patch", encoding="utf-8", delete=False
    ) as patch_file:
        patch_file.write(corruption_patch)
        patch_path = Path(patch_file.name)
    try:
        run(
            "git",
            "-C",
            str(output),
            "apply",
            "--whitespace=fix",
            str(patch_path),
        )
    finally:
        patch_path.unlink(missing_ok=True)

    for raw_path in fail_to_pass:
        target = safe_relative(output, raw_path)
        if target.is_dir():
            raise SystemExit(f"FAIL_TO_PASS path unexpectedly points to directory: {raw_path}")
        target.unlink(missing_ok=True)

    git_dir = output / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)
    run("git", "-C", str(output), "init")
    run("git", "-C", str(output), "config", "user.email", "eval@wigtn.local")
    run("git", "-C", str(output), "config", "user.name", "WIGTN Eval")
    run("git", "-C", str(output), "add", "-A")
    run(
        "git",
        "-C",
        str(output),
        "commit",
        "-m",
        "frozen FeatureBench arm baseline",
        "--quiet",
    )

    if args.plugin_root:
        plugin_root = args.plugin_root.resolve()
        destination = output / ".wigtn-eval" / "plugin"
        shutil.copytree(plugin_root, destination)

    hidden_mask = output.parent / f"{output.name}-hidden-mask"
    hidden_mask.mkdir()
    run(
        "docker",
        "run",
        "-d",
        "--name",
        args.container_name,
        "--network",
        "none",
        "--entrypoint",
        "sleep",
        "--mount",
        f"type=bind,source={output},target=/testbed",
        "--mount",
        f"type=bind,source={hidden_mask},target=/root/my_repo,readonly",
        args.image,
        "infinity",
    )
    print(
        json.dumps(
            {
                "workspace": str(output),
                "container": args.container_name,
                "hidden_source_mask": str(hidden_mask),
                "plugin": bool(args.plugin_root),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
