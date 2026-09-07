#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
model="${WIGTN_EVAL_MODEL:-gpt-6-astra}"
effort="${WIGTN_EVAL_EFFORT:-medium}"
repeat="${WIGTN_EVAL_REPEAT:-2}"
run_root="${WIGTN_ABLATION_ROOT:-/tmp/wigtn-package-ablation-$model}"
seed="${WIGTN_EVAL_SEED:-package-ablation-v1}"
cases_file="$repo_root/tests/behavior/ablation-cases.tsv"
auth_file="${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}"
arms=(bare placebo4 core4 full9)

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
Package ablation plan (no model calls made)
  model:       $model
  effort:      $effort
  repetitions: $repeat
  schedule seed: $seed
  arms:        ${arms[*]}
  cases:       prd-create, ordinary-coding
  output:      $run_root

Run with a fresh output root:
  scripts/run-package-ablation.sh --execute
EOF
  exit 0
fi

[[ "$repeat" =~ ^[1-9][0-9]*$ ]] || {
  echo "WIGTN_EVAL_REPEAT must be a positive integer" >&2
  exit 2
}
[[ -x "$codex_bin" && -f "$auth_file" ]] || {
  echo "Codex CLI or auth file unavailable" >&2
  exit 2
}
if [[ -e "$run_root" ]]; then
  echo "Ablation output already exists; choose a fresh WIGTN_ABLATION_ROOT: $run_root" >&2
  exit 2
fi

mkdir -p "$run_root/staging" "$run_root/runs" "$run_root/prompt-input"
env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/scripts/make-eval-schedule.py" "$cases_file" \
  --arms "${arms[@]}" --repeat "$repeat" --seed "$seed" \
  --output "$run_root/SCHEDULE.tsv"
env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/scripts/build-ablation-marketplace.py" \
  core4 "$run_root/staging/core4" >/dev/null
env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/scripts/build-ablation-marketplace.py" \
  placebo4 "$run_root/staging/placebo4" >/dev/null

marketplace_for() {
  case "$1" in
    core4|placebo4) printf '%s/staging/%s' "$run_root" "$1" ;;
    full9) printf '%s' "$repo_root" ;;
    *) return 1 ;;
  esac
}

for arm in "${arms[@]}"; do
  mkdir -p "$run_root/$arm-home" "$run_root/$arm-work" "$run_root/runs/$arm"
  ln -sf "$auth_file" "$run_root/$arm-home/auth.json"
  if [[ "$arm" != "bare" ]]; then
    CODEX_HOME="$run_root/$arm-home" "$codex_bin" \
      --disable remote_plugin --disable apps \
      plugin marketplace add "$(marketplace_for "$arm")" --json \
      > "$run_root/runs/$arm/setup-marketplace.json"
    CODEX_HOME="$run_root/$arm-home" "$codex_bin" \
      --disable remote_plugin --disable apps \
      plugin add wigtn-plugins-with-codex@wigtn --json \
      > "$run_root/runs/$arm/setup-plugin.json"
  fi
done

probe="간결한 PRD를 작성해줘"
for arm in "${arms[@]}"; do
  CODEX_HOME="$run_root/$arm-home" "$codex_bin" \
    --disable remote_plugin --disable apps \
    -C "$run_root/$arm-work" debug prompt-input "$probe" \
    > "$run_root/prompt-input/$arm.json"
done

env PYTHONDONTWRITEBYTECODE=1 python3 - "$run_root/prompt-input" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
needle = "wigtn-plugins-with-codex:product-spec"
expected = {"bare": False, "placebo4": False, "core4": True, "full9": True}
for arm, should_contain in expected.items():
    contains = needle in (root / f"{arm}.json").read_text(
        encoding="utf-8", errors="ignore"
    )
    if contains != should_contain:
        raise SystemExit(
            f"{arm}: product-spec exposure={contains}, expected={should_contain}"
        )
print("Package ablation isolation: PASS")
PY

{
  printf 'created_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'codex_cli=%s\n' "$("$codex_bin" --version)"
  printf 'model=%s\neffort=%s\nrepetitions=%s\n' "$model" "$effort" "$repeat"
  printf 'schedule_seed=%s\n' "$seed"
  (
    cd "$repo_root"
    shasum -a 256 \
      scripts/build-ablation-marketplace.py \
      scripts/run-package-ablation.sh \
      scripts/make-eval-schedule.py \
      scripts/score-behavior-smoke.py \
      "$run_root/SCHEDULE.tsv" \
      tests/behavior/ablation-cases.tsv \
      tests/behavior/prompts/prd-create.txt \
      tests/behavior/prompts/ordinary-coding.txt
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
    -o "$stem.out.md" - < "$repo_root/$prompt_path" \
    > "$stem.log" 2>&1
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
  run_one "$pair_id" "$order" "$arm" "$case_id" "$prompt_path" "$rep_index"
done < "$run_root/SCHEDULE.tsv"

env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/scripts/score-behavior-smoke.py" "$run_root"
env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/scripts/summarize-package-ablation.py" "$run_root" \
  --output "$run_root/ABLATION-SUMMARY.md"
