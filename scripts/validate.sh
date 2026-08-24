#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
plugin="$repo_root/plugins/wigtn-plugins-with-codex"
wiki_plugin="$repo_root/plugins/wigtn-knowledge-wiki"
codex_home="${CODEX_HOME:-$HOME/.codex}"
plugin_validator="$codex_home/skills/.system/plugin-creator/scripts/validate_plugin.py"
skill_validator="$codex_home/skills/.system/skill-creator/scripts/quick_validate.py"

python3 "$repo_root/.github/scripts/validate_repository.py"

if test -f "$plugin_validator" && test -f "$skill_validator"; then
  python3 "$plugin_validator" "$plugin"
  python3 "$plugin_validator" "$wiki_plugin"
  skill_count=0
  for skill in "$plugin"/skills/*; do
    test -d "$skill" || continue
    python3 "$skill_validator" "$skill"
    skill_count=$((skill_count + 1))
  done
  test "$skill_count" -eq 9 || { echo "Expected 9 core skills, found $skill_count"; exit 1; }
  python3 "$skill_validator" "$wiki_plugin/skills/knowledge-wiki"
else
  echo "Codex system validators unavailable; repository contract validation used."
fi
grep -q 'allow_implicit_invocation: false' "$plugin/skills/verified-delivery/agents/openai.yaml"
grep -q 'never auto-invoke for ordinary coding' "$plugin/skills/verified-delivery/SKILL.md"
grep -q '\$wigtn-plugins-with-codex:verified-delivery' "$plugin/skills/verified-delivery/agents/openai.yaml"
grep -q '커밋해줘' "$plugin/skills/release-readiness/SKILL.md"
grep -q 'PRD 디깅해줘' "$plugin/skills/product-spec/SKILL.md"
python3 "$repo_root/scripts/check-verified-delivery-routing.py"
python3 "$repo_root/scripts/check-external-results.py"
python3 "$repo_root/scripts/check-featurebench-selection.py"
python3 "$repo_root/scripts/check-featurebench-results.py"
python3 "$repo_root/scripts/check-knowledge-wiki.py"
for config in "$plugin"/skills/*/agents/openai.yaml; do
  grep -q '\$wigtn-plugins-with-codex:' "$config" || {
    echo "Unqualified installed-plugin skill prompt: $config"
    exit 1
  }
done
grep -q '\$wigtn-knowledge-wiki:knowledge-wiki' \
  "$wiki_plugin/skills/knowledge-wiki/agents/openai.yaml"

"$repo_root/scripts/run-evals.sh"
echo "Static validation: PASS"
