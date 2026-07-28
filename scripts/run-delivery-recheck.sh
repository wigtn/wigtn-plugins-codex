#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_study="${WIGTN_DELIVERY_FIXTURES:-$repo_root/../wigtn-plugins-with-claude-code/.github/evals/delivery-workflows-2026}"
run_root="${WIGTN_DELIVERY_RECHECK_ROOT:-/tmp/wigtn-delivery-v03-recheck}"
codex_bin="${CODEX_BIN:-/Applications/ChatGPT.app/Contents/Resources/codex}"
auth_file="${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}"
im_arms=(IM-M56-BARE IM-M56-ORDINARY IM-M56-VERIFIED IM-M55-VERIFIED)
im_tasks=(expense-approval webhook-delivery tenant-search config-migration)
ac_arms=(AC-M56-BARE AC-M56-PLUGIN AC-M55-PLUGIN)
ac_tasks=(commit-scoped secret-untracked prepare-only review-only no-changes failing-check detached-head commit-push push-only vague-complete)

model_for() {
  [[ "$1" == *M55* ]] && printf 'gpt-5.5' || printf 'gpt-5.6-sol'
}

if [[ "${1:-}" != "--execute" ]]; then
  echo "Delivery recheck: 16 implement + 30 release = 46 model calls"
  echo "Frozen fixture source: $source_study"
  echo "Output: $run_root"
  exit 0
fi
[[ -f "$source_study/implement/setup_repo.py" ]] || {
  echo "Frozen delivery fixtures unavailable: $source_study" >&2
  exit 2
}
[[ ! -e "$run_root" ]] || {
  echo "Choose a fresh WIGTN_DELIVERY_RECHECK_ROOT: $run_root" >&2
  exit 2
}
mkdir -p "$run_root/implement" "$run_root/release" "$run_root/homes" "$run_root/work"

all_arms=("${im_arms[@]}" "${ac_arms[@]}")
for arm in "${all_arms[@]}"; do
  mkdir -p "$run_root/homes/$arm" "$run_root/work/$arm"
  ln -sf "$auth_file" "$run_root/homes/$arm/auth.json"
  if [[ "$arm" != *BARE ]]; then
    CODEX_HOME="$run_root/homes/$arm" "$codex_bin" \
      --disable remote_plugin --disable apps \
      plugin marketplace add "$repo_root" --json >/dev/null
    CODEX_HOME="$run_root/homes/$arm" "$codex_bin" \
      --disable remote_plugin --disable apps \
      plugin add wigtn-plugins-with-codex@wigtn --json >/dev/null
  fi
done

{
  printf 'created_utc=%s\ncodex_cli=%s\neffort=medium\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$("$codex_bin" --version)"
  shasum -a 256 \
    "$source_study/PROTOCOL.md" \
    "$source_study/implement/setup_repo.py" \
    "$source_study/implement/collect_state.py" \
    "$source_study/implement/hidden/"*.py \
    "$source_study/autocommit/setup_repo.py" \
    "$source_study/autocommit/collect_state.py" \
    "$repo_root/tests/behavior/score-delivery-recheck.py" \
    "$repo_root/scripts/run-delivery-recheck.sh"
  (
    cd "$repo_root"
    find plugins/wigtn-plugins-with-codex -type f -print |
      LC_ALL=C sort |
      while IFS= read -r path; do shasum -a 256 "$path"; done
  )
} >"$run_root/MANIFEST.txt"

run_implement() {
  local arm="$1" task stem repo prompt started rc visible hidden patch_lines
  for task in "${im_tasks[@]}"; do
    stem="$run_root/implement/$arm/$task"
    repo="$run_root/work/$arm/im-$task"
    mkdir -p "$(dirname "$stem")"
    python3 "$source_study/implement/setup_repo.py" "$task" "$repo" >"$stem.setup.json"
    prompt="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["prompt"])' "$stem.setup.json")"
    if [[ "$arm" == *VERIFIED ]]; then
      prompt="\$wigtn-plugins-with-codex:verified-delivery"$'\n\n'"$prompt"
    fi
    started="$(date +%s)"
    set +e
    CODEX_HOME="$run_root/homes/$arm" "$codex_bin" \
      --disable remote_plugin --disable apps -a never \
      -m "$(model_for "$arm")" -c 'model_reasoning_effort="medium"' \
      -s workspace-write -C "$repo" exec --ephemeral --ignore-rules \
      -o "$stem.out.md" "$prompt" >"$stem.log" 2>&1
    rc=$?
    (cd "$repo" && python3 -m unittest -v) >"$stem.visible.log" 2>&1
    visible=$?
    PYTHONPATH="$repo" python3 "$source_study/implement/hidden/$task.py" \
      >"$stem.hidden.log" 2>&1
    hidden=$?
    set -e
    git -C "$repo" diff -- . ':(exclude)notes/user-draft.txt' >"$stem.patch"
    patch_lines="$(wc -l <"$stem.patch" | tr -d ' ')"
    python3 "$source_study/implement/collect_state.py" \
      "$repo" "$stem.setup.json" >"$stem.state.json"
    python3 -c \
      'import json,sys; from pathlib import Path; Path(sys.argv[1]).write_text(json.dumps({"exit_code":int(sys.argv[2]),"visible_exit":int(sys.argv[3]),"hidden_exit":int(sys.argv[4]),"duration_seconds":int(sys.argv[5]),"patch_lines":int(sys.argv[6])},indent=2)+"\n")' \
      "$stem.meta.json" "$rc" "$visible" "$hidden" \
      "$(( $(date +%s) - started ))" "$patch_lines"
  done
}

run_release() {
  local arm="$1" task stem repo prompt started rc
  for task in "${ac_tasks[@]}"; do
    stem="$run_root/release/$arm/$task"
    repo="$run_root/work/$arm/ac-$task"
    mkdir -p "$(dirname "$stem")"
    python3 "$source_study/autocommit/setup_repo.py" "$task" "$repo" >"$stem.setup.json"
    prompt="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["prompt"])' "$stem.setup.json")"
    started="$(date +%s)"
    set +e
    CODEX_HOME="$run_root/homes/$arm" "$codex_bin" \
      --disable remote_plugin --disable apps -a never \
      -m "$(model_for "$arm")" -c 'model_reasoning_effort="medium"' \
      -s danger-full-access -C "$repo" exec --ephemeral --ignore-rules \
      -o "$stem.out.md" "$prompt" >"$stem.log" 2>&1
    rc=$?
    set -e
    python3 "$source_study/autocommit/collect_state.py" \
      "$repo" "$stem.setup.json" >"$stem.state.json"
    python3 -c \
      'import json,sys; from pathlib import Path; Path(sys.argv[1]).write_text(json.dumps({"exit_code":int(sys.argv[2]),"duration_seconds":int(sys.argv[3])},indent=2)+"\n")' \
      "$stem.meta.json" "$rc" "$(( $(date +%s) - started ))"
  done
}

for arm in "${im_arms[@]}"; do run_implement "$arm" & done
for arm in "${ac_arms[@]}"; do run_release "$arm" & done
status=0
for pid in $(jobs -p); do wait "$pid" || status=1; done
[[ "$status" -eq 0 ]] || exit "$status"
python3 "$repo_root/tests/behavior/score-delivery-recheck.py" "$run_root"
