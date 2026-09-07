#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
model="${WIGTN_EVAL_MODEL:-gpt-6-astra}"
effort="${WIGTN_EVAL_EFFORT:-medium}"
concurrency="${WIGTN_EVAL_CONCURRENCY:-3}"
run_root="${WIGTN_WORKGRAPH_PILOT_ROOT:-/tmp/wigtn-workgraph-pilot-$model}"
auth_file="${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}"
cases="$repo_root/tests/workgraph/pilot-cases.json"

if [[ -n "${CODEX_BIN:-}" ]]; then
  codex_bin="$CODEX_BIN"
elif [[ -x "/Applications/ChatGPT.app/Contents/Resources/codex" ]]; then
  codex_bin="/Applications/ChatGPT.app/Contents/Resources/codex"
elif command -v codex >/dev/null 2>&1; then
  codex_bin="$(command -v codex)"
else
  codex_bin="codex"
fi

mode="${1:-}"
if [[ "$mode" != "--execute" && "$mode" != "--resume" ]]; then
  cat <<EOF
WorkGraph planning pilot (no model calls made)
  model:  $model
  effort: $effort
  concurrency: $concurrency
  cases:  12 treatment-only capability tasks
  output: $run_root

Run with a fresh output root:
  scripts/run-workgraph-pilot.sh --execute

Retry only missing or infrastructure-failed cases from a preserved run:
  scripts/run-workgraph-pilot.sh --resume
EOF
  exit 0
fi

if [[ "$mode" == "--execute" ]]; then
  [[ ! -e "$run_root" ]] || {
    echo "Choose a fresh WIGTN_WORKGRAPH_PILOT_ROOT: $run_root" >&2
    exit 2
  }
else
  [[ -d "$run_root/home" && -d "$run_root/work" ]] || {
    echo "Cannot resume incomplete pilot root: $run_root" >&2
    exit 2
  }
fi
[[ -x "$codex_bin" && -f "$auth_file" ]] || {
  echo "Codex CLI or auth file unavailable" >&2
  exit 2
}
[[ "$concurrency" =~ ^[1-9][0-9]*$ ]] || {
  echo "WIGTN_EVAL_CONCURRENCY must be a positive integer" >&2
  exit 2
}

if [[ "$mode" == "--execute" ]]; then
  mkdir -p "$run_root/home" "$run_root/runs" "$run_root/prompt-input"
  ln -sf "$auth_file" "$run_root/home/auth.json"
  env PYTHONDONTWRITEBYTECODE=1 python3 \
    "$repo_root/tests/workgraph/setup-pilot.py" "$run_root"

  CODEX_HOME="$run_root/home" "$codex_bin" \
    --disable remote_plugin --disable apps \
    plugin marketplace add "$repo_root" --json \
    >"$run_root/runs/setup-marketplace.json"
  CODEX_HOME="$run_root/home" "$codex_bin" \
    --disable remote_plugin --disable apps \
    plugin add wigtn-plugins-with-codex@wigtn --json \
    >"$run_root/runs/setup-plugin.json"

  probe='Use $wigtn-plugins-with-codex:work-planner to plan this feature.'
  CODEX_HOME="$run_root/home" "$codex_bin" \
    --disable remote_plugin --disable apps \
    -C "$run_root/work/auth-lockout" debug prompt-input "$probe" \
    >"$run_root/prompt-input/work-planner.json"
  grep -q "wigtn-plugins-with-codex:work-planner" \
    "$run_root/prompt-input/work-planner.json" || {
      echo "work-planner is not exposed in prompt input" >&2
      exit 2
    }

  {
  printf 'created_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'codex_cli=%s\nmodel=%s\neffort=%s\nconcurrency=%s\n' \
    "$("$codex_bin" --version)" "$model" "$effort" "$concurrency"
  (
    cd "$repo_root"
    shasum -a 256 \
      scripts/run-workgraph-pilot.sh \
      tests/workgraph/setup-pilot.py \
      tests/workgraph/score-pilot.py \
      tests/workgraph/pilot-cases.json
    while IFS= read -r plugin_file; do
      shasum -a 256 "$plugin_file"
    done < <(
      find plugins/wigtn-plugins-with-codex -type f -print |
        LC_ALL=C sort
    )
  )
  } >"$run_root/MANIFEST.txt"
else
  printf 'resumed_utc=%s\nresume_concurrency=%s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$concurrency" \
    >>"$run_root/MANIFEST.txt"
fi

run_case() {
  local case_id="$1" started rc
  started="$(date +%s)"
  set +e
  CODEX_HOME="$run_root/home" "$codex_bin" \
    --disable remote_plugin --disable apps \
    -a never -m "$model" -c "model_reasoning_effort=\"$effort\"" \
    -s workspace-write -C "$run_root/work/$case_id" \
    exec --ephemeral --ignore-rules --skip-git-repo-check \
    -o "$run_root/runs/$case_id.out.md" - \
    <"$run_root/prompts/$case_id.txt" \
    >"$run_root/runs/$case_id.log" 2>&1
  rc=$?
  set -e
  env PYTHONDONTWRITEBYTECODE=1 python3 - \
    "$run_root/runs/$case_id.meta.json" "$case_id" "$rc" \
    "$(( $(date +%s) - started ))" "$model" "$effort" <<'PY'
import json
from pathlib import Path
import sys
Path(sys.argv[1]).write_text(
    json.dumps(
        {
            "case": sys.argv[2],
            "exit_code": int(sys.argv[3]),
            "duration_seconds": int(sys.argv[4]),
            "model": sys.argv[5],
            "effort": sys.argv[6],
        },
        indent=2,
    ) + "\n"
)
PY
}

all_case_ids=()
while IFS= read -r case_id; do
  all_case_ids+=("$case_id")
done < <(env PYTHONDONTWRITEBYTECODE=1 python3 - "$cases" <<'PY'
import json
from pathlib import Path
import sys
for case in json.loads(Path(sys.argv[1]).read_text()):
    print(case["id"])
PY
)

case_ids=()
if [[ "$mode" == "--execute" ]]; then
  case_ids=("${all_case_ids[@]}")
else
  for case_id in "${all_case_ids[@]}"; do
    meta="$run_root/runs/$case_id.meta.json"
    graph="$run_root/work/$case_id/.wigtn/workgraph.json"
    if [[ -f "$meta" && -f "$graph" ]] && \
      env PYTHONDONTWRITEBYTECODE=1 python3 - "$meta" <<'PY'
import json
from pathlib import Path
import sys
raise SystemExit(0 if json.loads(Path(sys.argv[1]).read_text())["exit_code"] == 0 else 1)
PY
    then
      continue
    fi
    attempt_dir="$run_root/attempts/$case_id/$(date -u +%Y%m%dT%H%M%SZ)"
    mkdir -p "$attempt_dir"
    for suffix in meta.json out.md log; do
      artifact="$run_root/runs/$case_id.$suffix"
      [[ ! -e "$artifact" ]] || mv "$artifact" "$attempt_dir/"
    done
    env PYTHONDONTWRITEBYTECODE=1 python3 \
      "$repo_root/tests/workgraph/setup-pilot.py" "$run_root" \
      --case "$case_id" --archive-dir "$attempt_dir"
    case_ids+=("$case_id")
  done
  [[ "${#case_ids[@]}" -gt 0 ]] || {
    echo "No failed or missing WorkGraph cases to resume."
  }
fi

batch_pids=()
status=0
for case_id in "${case_ids[@]}"; do
  run_case "$case_id" &
  batch_pids+=("$!")
  if [[ "${#batch_pids[@]}" -ge "$concurrency" ]]; then
    for pid in "${batch_pids[@]}"; do
      wait "$pid" || status=1
    done
    batch_pids=()
  fi
done
if [[ "${#batch_pids[@]}" -gt 0 ]]; then
  for pid in "${batch_pids[@]}"; do
    wait "$pid" || status=1
  done
fi
[[ "$status" -eq 0 ]] || exit "$status"

env PYTHONDONTWRITEBYTECODE=1 python3 \
  "$repo_root/tests/workgraph/score-pilot.py" "$run_root"
