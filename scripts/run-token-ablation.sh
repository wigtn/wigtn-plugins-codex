#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
model="${WIGTN_EVAL_MODEL:-gpt-5.6-sol}"
effort="${WIGTN_EVAL_EFFORT:-medium}"
repeat="${WIGTN_EVAL_REPEAT:-3}"
run_root="${WIGTN_TOKEN_ABLATION_ROOT:-/tmp/wigtn-token-ablation-$model}"
baseline_ref="${WIGTN_BASELINE_REF:-HEAD}"
seed="${WIGTN_EVAL_SEED:-token-ablation-v1}"
cases_file="$repo_root/tests/behavior/token-efficiency-cases.tsv"
auth_file="${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}"
codex_bin="${CODEX_BIN:-/Applications/ChatGPT.app/Contents/Resources/codex}"
arms=(baseline candidate)

if [[ "${1:-}" != "--execute" ]]; then
  cat <<EOF
Token ablation plan (no model calls made)
  model:        $model
  effort:       $effort
  repetitions:  $repeat
  baseline ref: $baseline_ref
  candidate:    current worktree
  arms:         ${arms[*]}
  cases:        prd-create, acceptance-uncertain
  calls:        $(( repeat * 4 ))
  output:       $run_root
EOF
  exit 0
fi

[[ "$model" == gpt-5.6-sol ]] || { echo "Legacy token ablation prices GPT-5.6 Sol only; use run-model-migration-eval.py for other models" >&2; exit 2; }

[[ "$repeat" =~ ^[1-9][0-9]*$ ]] || { echo "repeat must be positive" >&2; exit 2; }
[[ -x "$codex_bin" && -f "$auth_file" ]] || { echo "Codex CLI or auth unavailable" >&2; exit 2; }
[[ ! -e "$run_root" ]] || { echo "choose a fresh WIGTN_TOKEN_ABLATION_ROOT" >&2; exit 2; }
baseline_commit="$(git -C "$repo_root" rev-parse "$baseline_ref^{commit}")"

mkdir -p "$run_root/staging/baseline" "$run_root/runs" "$run_root/prompt-input"
git -C "$repo_root" archive "$baseline_commit" | tar -x -C "$run_root/staging/baseline"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/make-eval-schedule.py" \
  "$cases_file" --arms "${arms[@]}" --repeat "$repeat" --seed "$seed" \
  --output "$run_root/SCHEDULE.tsv"

marketplace_for() {
  [[ "$1" == baseline ]] && printf '%s' "$run_root/staging/baseline" || printf '%s' "$repo_root"
}

for arm in "${arms[@]}"; do
  mkdir -p "$run_root/$arm-home" "$run_root/$arm-work" "$run_root/runs/$arm"
  ln -s "$auth_file" "$run_root/$arm-home/auth.json"
  CODEX_HOME="$run_root/$arm-home" "$codex_bin" --disable remote_plugin --disable apps \
    plugin marketplace add "$(marketplace_for "$arm")" --json \
    > "$run_root/runs/$arm/setup-marketplace.json"
  CODEX_HOME="$run_root/$arm-home" "$codex_bin" --disable remote_plugin --disable apps \
    plugin add wigtn-plugins-with-codex@wigtn --json \
    > "$run_root/runs/$arm/setup-plugin.json"
  CODEX_HOME="$run_root/$arm-home" "$codex_bin" --disable remote_plugin --disable apps \
    -C "$run_root/$arm-work" debug prompt-input "간결한 PRD를 작성해줘" \
    > "$run_root/prompt-input/$arm.json"
  grep -q 'wigtn-plugins-with-codex:product-spec' "$run_root/prompt-input/$arm.json" || {
    echo "$arm does not expose product-spec" >&2
    exit 2
  }
done

{
  printf 'created_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'codex_cli=%s\nmodel=%s\neffort=%s\nrepeat=%s\n' \
    "$("$codex_bin" --version)" "$model" "$effort" "$repeat"
  printf 'baseline_commit=%s\nschedule_seed=%s\n' "$baseline_commit" "$seed"
  shasum -a 256 "$run_root/SCHEDULE.tsv" "$cases_file" \
    "$repo_root/tests/behavior/prompts/prd-create.txt" \
    "$repo_root/tests/behavior/prompts/acceptance-uncertain.txt"
  find "$repo_root/plugins/wigtn-plugins-with-codex" -type f -print0 | \
    LC_ALL=C sort -z | xargs -0 shasum -a 256
} > "$run_root/MANIFEST.txt"

run_one() {
  local pair_id="$1" order="$2" arm="$3" case_id="$4" prompt_path="$5" rep="$6"
  local stem="$run_root/runs/$arm/$case_id.$rep" started rc
  started="$(date +%s)"
  set +e
  CODEX_HOME="$run_root/$arm-home" "$codex_bin" --disable remote_plugin --disable apps \
    -a never -m "$model" -c "model_reasoning_effort=\"$effort\"" \
    -s read-only -C "$run_root/$arm-work" exec --ephemeral --ignore-rules \
    --skip-git-repo-check --json -o "$stem.out.md" - \
    < "$repo_root/$prompt_path" > "$stem.events.jsonl" 2> "$stem.log"
  rc=$?
  set -e
  env PYTHONDONTWRITEBYTECODE=1 python3 - "$stem.meta.json" "$pair_id" "$order" \
    "$arm" "$case_id" "$rep" "$rc" "$(( $(date +%s) - started ))" <<'PY'
import json
from pathlib import Path
import sys
Path(sys.argv[1]).write_text(json.dumps({
    "pair_id": sys.argv[2], "schedule_order": int(sys.argv[3]),
    "arm": sys.argv[4], "case": sys.argv[5], "repeat": int(sys.argv[6]),
    "exit_code": int(sys.argv[7]), "duration_seconds": int(sys.argv[8]),
}, indent=2) + "\n")
PY
}

while IFS=$'\t' read -r pair_id order arm case_id prompt_path rep_index; do
  [[ "$pair_id" != pair_id ]] || continue
  run_one "$pair_id" "$order" "$arm" "$case_id" "$prompt_path" "$rep_index"
done < "$run_root/SCHEDULE.tsv"

env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/summarize-token-efficiency.py" "$run_root"
env PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/score-token-ablation.py" "$run_root"
