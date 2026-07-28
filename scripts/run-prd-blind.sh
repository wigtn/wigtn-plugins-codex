#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
root55="${WIGTN_ABLATION_55_ROOT:-/tmp/wigtn-package-ablation-v3-m55}"
root56="${WIGTN_ABLATION_56_ROOT:-/tmp/wigtn-package-ablation-v3-m56}"
run_root="${WIGTN_PRD_BLIND_ROOT:-/tmp/wigtn-prd-blind-v03}"
codex_bin="${CODEX_BIN:-/Applications/ChatGPT.app/Contents/Resources/codex}"
auth_file="${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}"
panels=(M55-R1 M55-R2 M56-R1 M56-R2)

if [[ "${1:-}" != "--execute" ]]; then
  echo "PRD blind screen: 4 panels × 2 judge models = 8 calls"
  echo "Output: $run_root"
  exit 0
fi
[[ ! -e "$run_root" ]] || {
  echo "Choose a fresh WIGTN_PRD_BLIND_ROOT: $run_root" >&2
  exit 2
}
python3 "$repo_root/tests/behavior/make-prd-blind.py" \
  "$root55" "$root56" "$run_root"
mkdir -p "$run_root/runs/J56" "$run_root/runs/J55" "$run_root/judge-cwd"
for judge in J56 J55; do
  home="$run_root/$judge-home"
  mkdir -p "$home"
  ln -sf "$auth_file" "$home/auth.json"
done
{
  printf 'created_utc=%s\ncodex_cli=%s\neffort=medium\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$("$codex_bin" --version)"
  shasum -a 256 \
    "$repo_root/tests/behavior/make-prd-blind.py" \
    "$repo_root/tests/behavior/score-prd-blind.py" \
    "$repo_root/scripts/run-prd-blind.sh" "$run_root/prompts/"*
} >"$run_root/MANIFEST.txt"

run_judge() {
  local judge="$1" model panel started rc
  [[ "$judge" == J55 ]] && model="gpt-5.5" || model="gpt-5.6-sol"
  for panel in "${panels[@]}"; do
    started="$(date +%s)"
    set +e
    CODEX_HOME="$run_root/$judge-home" "$codex_bin" \
      --disable remote_plugin --disable apps -a never -m "$model" \
      -c 'model_reasoning_effort="medium"' -s read-only \
      -C "$run_root/judge-cwd" exec --ephemeral --ignore-rules --skip-git-repo-check \
      -o "$run_root/runs/$judge/$panel.json" - \
      <"$run_root/prompts/$panel.txt" \
      >"$run_root/runs/$judge/$panel.log" 2>&1
    rc=$?
    set -e
    python3 -c \
      'import json,sys; from pathlib import Path; Path(sys.argv[1]).write_text(json.dumps({"exit_code":int(sys.argv[2]),"duration_seconds":int(sys.argv[3])},indent=2)+"\n")' \
      "$run_root/runs/$judge/$panel.meta.json" "$rc" \
      "$(( $(date +%s) - started ))"
  done
}

run_judge J56 &
run_judge J55 &
status=0
for pid in $(jobs -p); do wait "$pid" || status=1; done
[[ "$status" -eq 0 ]] || exit "$status"
python3 "$repo_root/tests/behavior/score-prd-blind.py" "$run_root"
