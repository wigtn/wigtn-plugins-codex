#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-triggers.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-plugin-resources.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-visual-contracts.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-evidence-contract.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-evidence-inspector.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-project-context.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-prd-contract.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-screen-contract.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-release-state.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-requirement-import.py"
python3 "$repo_root/scripts/check-symbolic-requirement-ids.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-workgraph-contract.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-eval-schedule.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-ablation-builder.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-ordinary-corpus.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-ordinary-scorer.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-codex-usage.py"
python3 "$repo_root/scripts/check-codex-usage-missing.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-token-ablation.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-eval-packet.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-research-harness.py"
env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/scripts/summarize-package-ablation.py" --help >/dev/null

env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-model-migration-eval.py"

env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-workgraph-inspect.py"

env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-workgraph-import-root.py"


env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-workgraph-concurrency.py"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/check-workgraph-project-guard.py"
echo "Static contracts: PASS"
