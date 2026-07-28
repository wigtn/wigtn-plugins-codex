#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "run-evals.sh is the compatibility entrypoint for deterministic static contracts."
echo "Use scripts/run-behavior-evals.sh --execute for model behavior smoke runs."
exec "$repo_root/scripts/run-static-contracts.sh"
