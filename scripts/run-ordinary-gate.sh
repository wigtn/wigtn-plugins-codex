#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
model="${WIGTN_EVAL_MODEL:-gpt-6-astra}"
effort="${WIGTN_EVAL_EFFORT:-medium}"
repeat="${WIGTN_EVAL_REPEAT:-1}"
concurrency="${WIGTN_EVAL_CONCURRENCY:-2}"
seed="${WIGTN_EVAL_SEED:-ordinary-gate-v1}"
run_root="${WIGTN_ORDINARY_GATE_ROOT:-/tmp/wigtn-ordinary-gate-$model}"
auth_file="${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}"
arms=(bare core4 full8 full9)

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
Ordinary-coding non-interference gate (no model calls made)
  model:       $model
  effort:      $effort
  repetitions: $repeat
  concurrency: $concurrency
  schedule:    $seed
  arms:        ${arms[*]}
  corpus:      12 tasks (Python, JavaScript, Ruby)
  output:      $run_root

Run with a fresh output root:
  scripts/run-ordinary-gate.sh --execute
EOF
  exit 0
fi

[[ "$repeat" =~ ^[1-9][0-9]*$ && "$concurrency" =~ ^[1-9][0-9]*$ ]] || {
  echo "repeat and concurrency must be positive integers" >&2
  exit 2
}
[[ -x "$codex_bin" && -f "$auth_file" ]] || {
  echo "Codex CLI or auth file unavailable" >&2
  exit 2
}
[[ ! -e "$run_root" ]] || {
  echo "Choose a fresh WIGTN_ORDINARY_GATE_ROOT: $run_root" >&2
  exit 2
}

mkdir -p "$run_root/staging" "$run_root/runs" "$run_root/prompt-input"
env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/tests/ordinary/setup-gate.py" "$run_root" \
  --arms "${arms[@]}" --repeat "$repeat"
env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/scripts/make-eval-schedule.py" "$run_root/CASES.tsv" \
  --arms "${arms[@]}" --repeat "$repeat" --seed "$seed" \
  --output "$run_root/SCHEDULE.tsv"

for arm in core4 full8 full9; do
  env PYTHONDONTWRITEBYTECODE=1 python3 \
    "$repo_root/scripts/build-ablation-marketplace.py" \
    "$arm" "$run_root/staging/$arm" >/dev/null
done

for arm in "${arms[@]}"; do
  mkdir -p "$run_root/home/$arm" "$run_root/runs/$arm"
  ln -sf "$auth_file" "$run_root/home/$arm/auth.json"
  if [[ "$arm" != "bare" ]]; then
    CODEX_HOME="$run_root/home/$arm" "$codex_bin" \
      --disable remote_plugin --disable apps \
      plugin marketplace add "$run_root/staging/$arm" --json \
      >"$run_root/runs/$arm/setup-marketplace.json"
    CODEX_HOME="$run_root/home/$arm" "$codex_bin" \
      --disable remote_plugin --disable apps \
      plugin add wigtn-plugins-with-codex@wigtn --json \
      >"$run_root/runs/$arm/setup-plugin.json"
  fi
done

probe_case="py-nonmutating-sort"
probe="Fix sorted_scores without mutating the caller's list. Run tests."
for arm in "${arms[@]}"; do
  CODEX_HOME="$run_root/home/$arm" "$codex_bin" \
    --disable remote_plugin --disable apps \
    -C "$run_root/work/$arm/$probe_case/1" \
    debug prompt-input "$probe" >"$run_root/prompt-input/$arm.json"
done

env PYTHONDONTWRITEBYTECODE=1 python3 - "$run_root/prompt-input" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
for arm in ("bare", "core4", "full8", "full9"):
    text = (root / f"{arm}.json").read_text(encoding="utf-8", errors="ignore")
    product = "wigtn-plugins-with-codex:product-spec" in text
    planner = "wigtn-plugins-with-codex:work-planner" in text
    expected_product = arm != "bare"
    expected_planner = arm == "full9"
    if product != expected_product or planner != expected_planner:
        raise SystemExit(
            f"{arm}: product={product}/{expected_product}, "
            f"planner={planner}/{expected_planner}"
        )
print("Ordinary gate isolation: PASS")
PY

{
  printf 'created_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'codex_cli=%s\n' "$("$codex_bin" --version)"
  printf 'model=%s\neffort=%s\nrepeat=%s\nconcurrency=%s\nseed=%s\n' \
    "$model" "$effort" "$repeat" "$concurrency" "$seed"
  printf 'arms=%s\n' "${arms[*]}"
  (
    cd "$repo_root"
    shasum -a 256 \
      scripts/run-ordinary-gate.sh \
      scripts/build-ablation-marketplace.py \
      scripts/make-eval-schedule.py \
      tests/ordinary/task_bank.py \
      tests/ordinary/setup-gate.py \
      tests/ordinary/reset-case.py \
      tests/ordinary/score-gate.py \
      "$run_root/SCHEDULE.tsv" \
      "$run_root/BASELINE.json"
    while IFS= read -r plugin_file; do
      shasum -a 256 "$plugin_file"
    done < <(
      find plugins/wigtn-plugins-with-codex -type f -print |
        LC_ALL=C sort
    )
  )
} >"$run_root/MANIFEST.txt"

run_one() {
  local pair_id="$1" order="$2" arm="$3" case_id="$4" prompt_path="$5" rep="$6"
  local stem="$run_root/runs/$arm/$case_id.$rep"
  local started rc attempt=1 archive
  while true; do
    started="$(date +%s)"
    set +e
    CODEX_HOME="$run_root/home/$arm" "$codex_bin" \
      --disable remote_plugin --disable apps \
      -a never -m "$model" -c "model_reasoning_effort=\"$effort\"" \
      -s workspace-write -C "$run_root/work/$arm/$case_id/$rep" \
      exec --ephemeral --ignore-rules --skip-git-repo-check \
      -o "$stem.out.md" - <"$run_root/$prompt_path" \
      >"$stem.log" 2>&1
    rc=$?
    set -e
    if [[ "$rc" -eq 0 || "$attempt" -ge 2 ]] || ! \
      grep -Eiq \
        'model.*capacity|capacity.*model|timed out|timeout|connection|stream disconnected|dns|network' \
        "$stem.log"; then
      break
    fi
    archive="$run_root/attempts/$arm/$case_id/$rep/infra-attempt-$attempt"
    mkdir -p "$archive"
    for suffix in log out.md; do
      [[ ! -e "$stem.$suffix" ]] || mv "$stem.$suffix" "$archive/"
    done
    env PYTHONDONTWRITEBYTECODE=1 python3 \
      "$repo_root/tests/ordinary/reset-case.py" \
      "$run_root" "$arm" "$case_id" "$rep" "$archive/work"
    attempt=$((attempt + 1))
  done

  env PYTHONDONTWRITEBYTECODE=1 python3 - \
    "$stem.meta.json" "$pair_id" "$order" "$arm" "$case_id" "$rep" "$rc" \
    "$(( $(date +%s) - started ))" "$model" "$effort" "$seed" "$attempt" <<'PY'
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
            "attempt": int(sys.argv[12]),
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
PY
}

batch_pids=()
status=0
while IFS=$'\t' read -r pair_id order arm case_id prompt_path rep_index; do
  [[ "$pair_id" != "pair_id" ]] || continue
  run_one "$pair_id" "$order" "$arm" "$case_id" "$prompt_path" "$rep_index" &
  batch_pids+=("$!")
  if [[ "${#batch_pids[@]}" -ge "$concurrency" ]]; then
    for pid in "${batch_pids[@]}"; do
      wait "$pid" || status=1
    done
    batch_pids=()
  fi
done <"$run_root/SCHEDULE.tsv"
if [[ "${#batch_pids[@]}" -gt 0 ]]; then
  for pid in "${batch_pids[@]}"; do
    wait "$pid" || status=1
  done
fi
[[ "$status" -eq 0 ]] || exit "$status"

env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/tests/ordinary/score-gate.py" "$run_root"
