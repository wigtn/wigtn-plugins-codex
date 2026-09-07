#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cases_file="$repo_root/tests/behavior/cases.tsv"
model="${WIGTN_EVAL_MODEL:-gpt-6-astra}"
effort="${WIGTN_EVAL_EFFORT:-medium}"
repeat="${WIGTN_EVAL_REPEAT:-1}"
run_root="${WIGTN_EVAL_ROOT:-/tmp/wigtn-codex-behavior-eval-$model}"
seed="${WIGTN_EVAL_SEED:-behavior-smoke-v1}"
input_rate="${WIGTN_INPUT_USD_PER_M:-}"
cached_input_rate="${WIGTN_CACHED_INPUT_USD_PER_M:-}"
cache_write_rate="${WIGTN_CACHE_WRITE_USD_PER_M:-}"
output_rate="${WIGTN_OUTPUT_USD_PER_M:-}"
auth_file="${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}"

if [[ -n "${CODEX_BIN:-}" ]]; then
  codex_bin="$CODEX_BIN"
elif [[ -x "/Applications/ChatGPT.app/Contents/Resources/codex" ]]; then
  codex_bin="/Applications/ChatGPT.app/Contents/Resources/codex"
elif command -v codex >/dev/null 2>&1; then
  codex_bin="$(command -v codex)"
else
  codex_bin="codex"
fi

if [[ "${1:-}" != "--execute" ]]; then
  cat <<EOF
Behavior smoke plan (no model calls made)
  model:       $model
  effort:      $effort
  repetitions: $repeat
  schedule seed: $seed
  arms:        bare, plugin
  cases:       $cases_file
  output:      $run_root

Run with: scripts/run-behavior-evals.sh --execute
EOF
  exit 0
fi

pricing_args=()
if [[ -n "$input_rate$cached_input_rate$cache_write_rate$output_rate" ]]; then
  [[ -n "$input_rate" && -n "$cached_input_rate" && -n "$cache_write_rate" && -n "$output_rate" ]] || {
    echo "Set all four WIGTN pricing rates or leave all unset" >&2
    exit 2
  }
  pricing_args=(--input-per-million "$input_rate" --cached-input-per-million "$cached_input_rate"
    --cache-write-per-million "$cache_write_rate" --output-per-million "$output_rate")
fi

[[ "$repeat" =~ ^[1-9][0-9]*$ ]] || {
  echo "WIGTN_EVAL_REPEAT must be a positive integer" >&2
  exit 2
}
[[ -x "$codex_bin" ]] || {
  echo "Codex CLI not executable: $codex_bin" >&2
  exit 2
}
[[ -f "$auth_file" ]] || {
  echo "Codex auth file not found: $auth_file" >&2
  exit 2
}
[[ -f "$cases_file" ]] || {
  echo "Behavior cases not found: $cases_file" >&2
  exit 2
}
if [[ -e "$run_root" ]]; then
  echo "Behavior output already exists; choose a fresh WIGTN_EVAL_ROOT: $run_root" >&2
  exit 2
fi

mkdir -p "$run_root/runs" "$run_root/prompt-input"
env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/scripts/make-eval-schedule.py" "$cases_file" \
  --arms bare plugin --repeat "$repeat" --seed "$seed" \
  --output "$run_root/SCHEDULE.tsv"
for arm in bare plugin; do
  mkdir -p "$run_root/$arm-home" "$run_root/$arm-work" "$run_root/runs/$arm"
  ln -sf "$auth_file" "$run_root/$arm-home/auth.json"
done

if ! CODEX_HOME="$run_root/plugin-home" "$codex_bin" \
  --disable remote_plugin --disable apps plugin list 2>/dev/null |
  grep -q "wigtn-plugins-with-codex@wigtn.*installed, enabled"; then
  CODEX_HOME="$run_root/plugin-home" "$codex_bin" \
    --disable remote_plugin --disable apps \
    plugin marketplace add "$repo_root" --json \
    > "$run_root/runs/plugin/setup-marketplace.json"
  CODEX_HOME="$run_root/plugin-home" "$codex_bin" \
    --disable remote_plugin --disable apps \
    plugin add wigtn-plugins-with-codex@wigtn --json \
    > "$run_root/runs/plugin/setup-plugin.json"
fi

probe="요구사항이 구현에 반영됐는지 검증해줘"
for arm in bare plugin; do
  CODEX_HOME="$run_root/$arm-home" "$codex_bin" \
    --disable remote_plugin --disable apps \
    -C "$run_root/$arm-work" debug prompt-input "$probe" \
    > "$run_root/prompt-input/$arm.json"
done

env PYTHONDONTWRITEBYTECODE=1 python3 - \
  "$run_root/prompt-input/bare.json" \
  "$run_root/prompt-input/plugin.json" <<'PY'
from pathlib import Path
import sys

needle = "wigtn-plugins-with-codex:acceptance-verifier"
bare = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
plugin = Path(sys.argv[2]).read_text(encoding="utf-8", errors="ignore")
if needle in bare:
    raise SystemExit("bare arm is contaminated by the WIGTN plugin")
if needle not in plugin:
    raise SystemExit("plugin arm does not expose acceptance-verifier")
print("Behavior isolation preflight: PASS")
PY

{
  printf 'created_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'codex_cli=%s\n' "$("$codex_bin" --version)"
  printf 'model=%s\neffort=%s\nrepetitions=%s\n' "$model" "$effort" "$repeat"
  printf 'schedule_seed=%s\n' "$seed"
  printf 'input_usd_per_m=%s\ncached_input_usd_per_m=%s\n' "$input_rate" "$cached_input_rate"
  printf 'cache_write_usd_per_m=%s\noutput_usd_per_m=%s\n' "$cache_write_rate" "$output_rate"
  (
    cd "$repo_root"
    shasum -a 256 \
      scripts/run-behavior-evals.sh \
      scripts/make-eval-schedule.py \
      scripts/codex_usage.py \
      scripts/summarize-token-efficiency.py \
      scripts/score-behavior-smoke.py \
      "$run_root/SCHEDULE.tsv" \
      tests/behavior/cases.tsv \
      tests/behavior/prompts/*.txt
    while IFS= read -r plugin_file; do
      shasum -a 256 "$plugin_file"
    done < <(
      find plugins/wigtn-plugins-with-codex -type f -print |
        LC_ALL=C sort
    )
  )
} > "$run_root/MANIFEST.txt"

run_one() {
  local pair_id="$1" order="$2" arm="$3" case_id="$4" prompt_path="$5" rep="$6"
  local stem="$run_root/runs/$arm/$case_id.$rep"
  local started rc

  started="$(date +%s)"
  set +e
  CODEX_HOME="$run_root/$arm-home" "$codex_bin" \
    --disable remote_plugin --disable apps \
    -a never -m "$model" -c "model_reasoning_effort=\"$effort\"" \
    -s read-only -C "$run_root/$arm-work" \
    exec --ephemeral --ignore-rules --skip-git-repo-check \
    --json -o "$stem.out.md" - < "$repo_root/$prompt_path" \
    > "$stem.events.jsonl" 2> "$stem.log"
  rc=$?
  set -e

  env PYTHONDONTWRITEBYTECODE=1 python3 - \
    "$stem.meta.json" "$pair_id" "$order" "$arm" "$case_id" "$rep" "$rc" \
    "$(( $(date +%s) - started ))" "$model" "$effort" "$seed" <<'PY'
import json
from pathlib import Path
import sys

Path(sys.argv[1]).write_text(
    json.dumps(
        {
            "pair_id": sys.argv[2],
            "schedule_order": int(sys.argv[3]),
            "arm": sys.argv[4],
            "case": sys.argv[5],
            "repeat": int(sys.argv[6]),
            "exit_code": int(sys.argv[7]),
            "duration_seconds": int(sys.argv[8]),
            "model": sys.argv[9],
            "effort": sys.argv[10],
            "schedule_seed": sys.argv[11],
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
PY
}

while IFS=$'\t' read -r pair_id order arm case_id prompt_path rep_index; do
  [[ "$pair_id" != "pair_id" ]] || continue
  [[ -f "$repo_root/$prompt_path" ]] || {
    echo "Missing prompt for $case_id: $prompt_path" >&2
    exit 2
  }
  run_one "$pair_id" "$order" "$arm" "$case_id" "$prompt_path" "$rep_index"
done < "$run_root/SCHEDULE.tsv"

env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/scripts/summarize-token-efficiency.py" "$run_root" \
  "${pricing_args[@]}"
env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/scripts/score-behavior-smoke.py" "$run_root"
