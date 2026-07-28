#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture_root="${WIGTN_ACTUAL_FIXTURES:-$repo_root/../wigtn-plugins-with-claude-code/.github/evals/plugin-function-audit-2026/actual-repos}"
run_root="${WIGTN_ACTUAL_ROOT:-/tmp/wigtn-actual-v03-pilot}"
codex_bin="${CODEX_BIN:-/Applications/ChatGPT.app/Contents/Resources/codex}"
auth_file="${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}"
arms=(AR-M56-BARE AR-M56-VERIFIED AR-M55-VERIFIED)
tasks=(game-timeline game-path home-youtube home-usage-url)

model_for() {
  [[ "$1" == AR-M55-VERIFIED ]] && printf 'gpt-5.5' || printf 'gpt-5.6-sol'
}

if [[ "${1:-}" != "--execute" ]]; then
  echo "External repository pilot: 4 tasks × 3 arms = 12 calls"
  echo "Source repositories are copied; originals are never mutated."
  echo "Output: $run_root"
  exit 0
fi
[[ -f "$fixture_root/setup_repo.py" ]] || {
  echo "Actual-repository fixtures unavailable: $fixture_root" >&2
  exit 2
}
[[ ! -e "$run_root" ]] || {
  echo "Choose a fresh WIGTN_ACTUAL_ROOT: $run_root" >&2
  exit 2
}
mkdir -p "$run_root/runs" "$run_root/work" "$run_root/homes"
for arm in "${arms[@]}"; do
  mkdir -p "$run_root/runs/$arm" "$run_root/work/$arm" "$run_root/homes/$arm"
  ln -sf "$auth_file" "$run_root/homes/$arm/auth.json"
  if [[ "$arm" != AR-M56-BARE ]]; then
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
    "$fixture_root/setup_repo.py" "$fixture_root/collect_state.py" \
    "$fixture_root/visible/"*/* "$fixture_root/hidden/"* \
    "$repo_root/tests/behavior/score-actual-repo-pilot.py" \
    "$repo_root/scripts/run-actual-repo-pilot.sh"
  (
    cd "$repo_root"
    find plugins/wigtn-plugins-with-codex -type f -print |
      LC_ALL=C sort |
      while IFS= read -r path; do shasum -a 256 "$path"; done
  )
} >"$run_root/MANIFEST.txt"

run_visible() {
  python3 - "$1" "$2" "$3" <<'PY'
import json,subprocess,sys
from pathlib import Path
repo=Path(sys.argv[1]); setup=json.loads(Path(sys.argv[2]).read_text()); log=Path(sys.argv[3])
rc=0
with log.open("w") as out:
    for command in setup["visible_commands"]:
        result=subprocess.run(command,cwd=repo,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        out.write(f"$ {command}\n{result.stdout}\nexit={result.returncode}\n")
        rc=max(rc, int(result.returncode != 0))
print(rc)
PY
}

run_hidden() {
  local task="$1" repo="$2" log="$3" rc=0
  mkdir -p "$repo/eval-hidden"
  case "$task" in
    game-timeline|game-path)
      cp "$fixture_root/hidden/$task.test.ts" "$repo/eval-hidden/$task.test.ts"
      (cd "$repo" && npm test -- --run "eval-hidden/$task.test.ts") >"$log" 2>&1 || rc=$?
      ;;
    home-youtube|home-usage-url)
      cp "$fixture_root/hidden/$task.test.mts" "$repo/eval-hidden/$task.test.mts"
      (cd "$repo" && node --experimental-strip-types --test "eval-hidden/$task.test.mts") >"$log" 2>&1 || rc=$?
      ;;
  esac
  rm -rf "$repo/eval-hidden"
  printf '%s' "$rc"
}

run_arm() {
  local arm="$1" task stem repo prompt started rc visible hidden patch_lines
  for task in "${tasks[@]}"; do
    stem="$run_root/runs/$arm/$task"
    repo="$run_root/work/$arm/$task"
    python3 "$fixture_root/setup_repo.py" "$task" "$repo" >"$stem.setup.json"
    prompt="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["prompt"])' "$stem.setup.json")"
    if [[ "$arm" != AR-M56-BARE ]]; then
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
    visible="$(run_visible "$repo" "$stem.setup.json" "$stem.visible.log")"
    hidden="$(run_hidden "$task" "$repo" "$stem.hidden.log")"
    set -e
    git -C "$repo" diff -- . ':(exclude)notes/eval-user-draft.txt' >"$stem.patch"
    patch_lines="$(wc -l <"$stem.patch" | tr -d ' ')"
    python3 "$fixture_root/collect_state.py" \
      "$repo" "$stem.setup.json" >"$stem.state.json"
    python3 -c \
      'import json,sys; from pathlib import Path; Path(sys.argv[1]).write_text(json.dumps({"exit_code":int(sys.argv[2]),"visible_exit":int(sys.argv[3]),"hidden_exit":int(sys.argv[4]),"duration_seconds":int(sys.argv[5]),"patch_lines":int(sys.argv[6])},indent=2)+"\n")' \
      "$stem.meta.json" "$rc" "$visible" "$hidden" \
      "$(( $(date +%s) - started ))" "$patch_lines"
  done
}

for arm in "${arms[@]}"; do run_arm "$arm" & done
status=0
for pid in $(jobs -p); do wait "$pid" || status=1; done
[[ "$status" -eq 0 ]] || exit "$status"
python3 "$repo_root/tests/behavior/score-actual-repo-pilot.py" "$run_root"
