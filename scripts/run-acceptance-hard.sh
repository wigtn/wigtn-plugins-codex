#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture_dir="$repo_root/tests/behavior"
codex_bin="${CODEX_BIN:-/Applications/ChatGPT.app/Contents/Resources/codex}"
auth_file="${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}"
run_root="${WIGTN_ACCEPTANCE_ROOT:-/tmp/wigtn-acceptance-hard-v7}"
model56="${WIGTN_MODEL_56:-gpt-5.6-sol}"
arms=(AV-M56-BARE AV-M56-PLUGIN AV-M55-PLUGIN)
tasks=(code-only irrelevant-pass stale-test tenant-partial flaky-check wrong-scope external-outcome contradictory)
schema="$repo_root/plugins/wigtn-plugins-with-codex/schemas/evidence-contract.schema.json"
validator="$repo_root/plugins/wigtn-plugins-with-codex/scripts/validate-evidence.py"

model_for() {
  [[ "$1" == AV-M55-PLUGIN ]] && printf 'gpt-5.5' || printf '%s' "$model56"
}

if [[ "${1:-}" != "--execute" ]]; then
  echo "Acceptance Hard plan: 8 tasks × 3 arms × 2 trials = 48 model calls"
  echo "Output: $run_root"
  exit 0
fi
[[ ! -e "$run_root" ]] || {
  echo "Choose a fresh WIGTN_ACCEPTANCE_ROOT: $run_root" >&2
  exit 2
}
mkdir -p "$run_root/runs" "$run_root/work" "$run_root/homes"

for arm in "${arms[@]}"; do
  mkdir -p "$run_root/runs/$arm" "$run_root/work/$arm" "$run_root/homes/$arm"
  ln -sf "$auth_file" "$run_root/homes/$arm/auth.json"
  if [[ "$arm" != AV-M56-BARE ]]; then
    CODEX_HOME="$run_root/homes/$arm" "$codex_bin" \
      --disable remote_plugin --disable apps \
      plugin marketplace add "$repo_root" --json \
      >"$run_root/runs/$arm/setup-marketplace.json"
    CODEX_HOME="$run_root/homes/$arm" "$codex_bin" \
      --disable remote_plugin --disable apps \
      plugin add wigtn-plugins-with-codex@wigtn --json \
      >"$run_root/runs/$arm/setup-plugin.json"
  fi
done

{
  printf 'created_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'codex_cli=%s\ntrials=2\neffort=medium\n' "$("$codex_bin" --version)"
  (
    cd "$repo_root"
    shasum -a 256 \
      "$fixture_dir/acceptance-hard-protocol.md" \
      "$fixture_dir/acceptance-hard-errata.md" \
      "$fixture_dir/setup-acceptance-hard.py" \
      "$fixture_dir/score-acceptance-hard.py" \
      scripts/run-acceptance-hard.sh "$schema" "$validator"
    find plugins/wigtn-plugins-with-codex -type f -print |
      LC_ALL=C sort |
      while IFS= read -r path; do shasum -a 256 "$path"; done
  )
} >"$run_root/MANIFEST.txt"

run_one() {
  local arm="$1" task="$2" repeat="$3" stem repo prompt started rc
  stem="$run_root/runs/$arm/$task.$repeat"
  repo="$run_root/work/$arm/$task-$repeat"
  env PYTHONDONTWRITEBYTECODE=1 python3 \
    "$fixture_dir/setup-acceptance-hard.py" \
    "$task" "$repo" "$schema" >"$stem.setup.json"
  prompt="$(env PYTHONDONTWRITEBYTECODE=1 python3 -c \
    'import json,sys; print(json.load(open(sys.argv[1]))["prompt"])' \
    "$stem.setup.json")"
  if [[ "$arm" != AV-M56-BARE ]]; then
    prompt="\$wigtn-plugins-with-codex:acceptance-verifier $prompt"
  fi
  started="$(date +%s)"
  set +e
  CODEX_HOME="$run_root/homes/$arm" "$codex_bin" \
    --disable remote_plugin --disable apps \
    -a never -m "$(model_for "$arm")" \
    -c 'model_reasoning_effort="medium"' \
    -s workspace-write -C "$repo" \
    exec --ephemeral --ignore-rules -o "$stem.out.md" "$prompt" \
    >"$stem.log" 2>&1
  rc=$?
  set -e
  env PYTHONDONTWRITEBYTECODE=1 python3 -c \
    'import json,sys; from pathlib import Path; Path(sys.argv[1]).write_text(json.dumps({"repo":sys.argv[2],"exit_code":int(sys.argv[3]),"duration_seconds":int(sys.argv[4])},indent=2)+"\n")' \
    "$stem.meta.json" "$repo" "$rc" "$(( $(date +%s) - started ))"
}

run_worker() {
  local arm="$1" repeat="$2" task
  for task in "${tasks[@]}"; do run_one "$arm" "$task" "$repeat"; done
}

for arm in "${arms[@]}"; do
  for repeat in 1 2; do run_worker "$arm" "$repeat" & done
done
status=0
for pid in $(jobs -p); do wait "$pid" || status=1; done
[[ "$status" -eq 0 ]] || exit "$status"

env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$fixture_dir/score-acceptance-hard.py" "$run_root" "$validator"
