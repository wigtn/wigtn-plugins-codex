#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
run_root="${WIGTN_DELIVERY_RECHECK_ROOT:-/tmp/wigtn-delivery-v03-recheck}"
blind_root="${WIGTN_DELIVERY_BLIND_ROOT:-$run_root/blind-v2}"
codex_bin="${CODEX_BIN:-/Applications/ChatGPT.app/Contents/Resources/codex}"
auth_file="${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}"
tasks=(expense-approval webhook-delivery tenant-search config-migration)

if [[ "${1:-}" != "--execute" ]]; then
  echo "Delivery blind screen: 4 tasks × 2 judge models = 8 calls"
  echo "Input: $run_root"
  echo "Output: $blind_root"
  exit 0
fi
[[ -f "$run_root/RESULTS.md" ]] || {
  echo "Run delivery recheck first: $run_root" >&2
  exit 2
}
[[ ! -e "$blind_root" ]] || {
  echo "Choose a fresh WIGTN_DELIVERY_BLIND_ROOT: $blind_root" >&2
  exit 2
}
python3 "$repo_root/tests/behavior/make-delivery-blind.py" "$run_root" "$blind_root"
mkdir -p "$blind_root/runs/J56" "$blind_root/runs/J55" "$blind_root/judge-cwd"
for judge in J56 J55; do
  home="$blind_root/$judge-home"
  mkdir -p "$home"
  ln -sf "$auth_file" "$home/auth.json"
done

run_judge() {
  local judge="$1" model task prompt started rc
  [[ "$judge" == J55 ]] && model="gpt-5.5" || model="gpt-5.6-sol"
  for task in "${tasks[@]}"; do
    prompt="$blind_root/prompts/$task.txt"
    started="$(date +%s)"
    set +e
    CODEX_HOME="$blind_root/$judge-home" "$codex_bin" \
      --disable remote_plugin --disable apps -a never -m "$model" \
      -c 'model_reasoning_effort="medium"' -s read-only \
      -C "$blind_root/judge-cwd" exec --ephemeral --ignore-rules \
      --skip-git-repo-check -o "$blind_root/runs/$judge/$task.json" - \
      <"$prompt" >"$blind_root/runs/$judge/$task.log" 2>&1
    rc=$?
    set -e
    python3 -c \
      'import json,sys; from pathlib import Path; Path(sys.argv[1]).write_text(json.dumps({"exit_code":int(sys.argv[2]),"duration_seconds":int(sys.argv[3])},indent=2)+"\n")' \
      "$blind_root/runs/$judge/$task.meta.json" "$rc" \
      "$(( $(date +%s) - started ))"
  done
}

run_judge J56 &
run_judge J55 &
status=0
for pid in $(jobs -p); do wait "$pid" || status=1; done
[[ "$status" -eq 0 ]] || exit "$status"
python3 "$repo_root/tests/behavior/score-delivery-blind.py" "$blind_root"
