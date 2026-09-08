## 01-01-small-8-candidate

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/01-01-small-8-candidate/work --json inspect --task TASK-005 --task TASK-008'
```

## 02-01-small-8-baseline

```sh
/bin/zsh -lc "pwd; rg --files -g AGENTS.md -g '.wigtn/**' -g '"'!node_modules'"' -g '"'!vendor'"' --hidden"
```

```sh
/bin/zsh -lc 'cat SKILL.md references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 -B ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/02-01-small-8-baseline/work --json inspect'
```

## 03-02-small-16-baseline

```sh
/bin/zsh -lc 'cat skills/work-planner/SKILL.md && cat skills/work-planner/references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 -B ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/03-02-small-16-baseline/work --json inspect'
```

## 04-02-small-16-candidate

```sh
/bin/zsh -lc 'cat skills/work-planner/SKILL.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/04-02-small-16-candidate/work --json inspect --task TASK-009 --task TASK-016'
```

## 05-03-large-40-baseline

```sh
/bin/zsh -lc "pwd; rg --files -g AGENTS.md -g '.wigtn/**' -g '"'!node_modules'"' -g '"'!vendor'"' -g '"'!'"\\.git' .; cat /private/tmp/wigtn-scoped-followup-20260908/homes/baseline/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md; cat /private/tmp/wigtn-scoped-followup-20260908/homes/baseline/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/references/workgraph-contract.md"
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/05-03-large-40-baseline/work --json inspect'
```

```sh
/bin/zsh -lc "rg --files --hidden -g AGENTS.md -g '.wigtn/**' -g '"'!.git/**'"'"
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; p=json.loads(Path(\".wigtn/workgraph.json\").read_text()); checks={c[\"id\"]:c for c in p[\"checks\"]}; print(json.dumps({\"saved_revision\":p[\"revision\"],\"tasks\":[dict(id=t[\"id\"],status=t[\"status\"],dependency_ids=t[\"depends_on\"],requirement_ids=t[\"requirement_ids\"],intended_paths=t[\"intended_paths\"],check_commands=[checks[c][\"command\"] for c in t[\"check_ids\"]]) for t in p[\"tasks\"] if t[\"id\"] in [\"TASK-021\",\"TASK-040\"]]}))'"
```

## 06-03-large-40-candidate

```sh
/bin/zsh -lc 'cat SKILL.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/06-03-large-40-candidate/work --json inspect --task TASK-021 --task TASK-040'
```

## 07-04-large-140-baseline

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-followup-20260908/homes/baseline/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md'
```

```sh
/bin/zsh -lc 'cat references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/07-04-large-140-baseline/work --json inspect'
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; g=json.loads(Path(\".wigtn/workgraph.json\").read_text()); print(json.dumps({\"saved_revision\":g[\"revision\"],\"tasks\":[t for t in g[\"tasks\"] if t[\"id\"] in [\"TASK-071\",\"TASK-140\"]],\"checks\":[c for c in g[\"checks\"] if c[\"id\"] in [\"CHK-071\",\"CHK-140\"]]}))'"
```

## 08-04-large-140-candidate

```sh
/bin/zsh -lc 'cat SKILL.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/08-04-large-140-candidate/work --json inspect --task TASK-071 --task TASK-140'
```

## 09-05-drift-72-candidate

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/09-05-drift-72-candidate/work --json inspect --task TASK-037 --task TASK-072'
```

## 10-05-drift-72-baseline

```sh
/bin/zsh -lc 'cat skills/work-planner/SKILL.md skills/work-planner/references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/10-05-drift-72-baseline/work --json inspect'
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; g=json.loads(Path(\".wigtn/workgraph.json\").read_text()); print(json.dumps({\"saved_revision\":g[\"revision\"],\"tasks\":[t for t in g[\"tasks\"] if t[\"id\"] in [\"TASK-037\",\"TASK-072\"]],\"checks\":[c for c in g[\"checks\"] if c[\"id\"] in [\"CHK-037\",\"CHK-072\"]]},indent=2))'"
```

## 11-06-blocked-90-baseline

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-followup-20260908/homes/baseline/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md'
```

```sh
/bin/zsh -lc "pwd; rg --files -g AGENTS.md -g '.wigtn/**' -g '"'!node_modules'"' --hidden"
```

```sh
/bin/zsh -lc 'cat references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/11-06-blocked-90-baseline/work --json inspect'
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; g=json.loads(Path(\".wigtn/workgraph.json\").read_text()); print(json.dumps({\"revision\":g[\"revision\"],\"tasks\":[t for t in g[\"tasks\"] if t[\"id\"] in [\"TASK-046\",\"TASK-090\"]],\"checks\":[c for c in g[\"checks\"] if set(c[\"task_ids\"]) & {\"TASK-046\",\"TASK-090\"}]},indent=2))'"
```

## 12-06-blocked-90-candidate

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/12-06-blocked-90-candidate/work --json inspect --task TASK-046 --task TASK-090'
```

## 13-07-dense-80-candidate

```sh
/bin/zsh -lc 'cat SKILL.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/13-07-dense-80-candidate/work --json inspect --task TASK-041 --task TASK-080'
```

```sh
/bin/zsh -lc "python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/13-07-dense-80-candidate/work --json inspect --task TASK-041 --task TASK-080 | python3 -c 'import json,sys; d=json.load(sys.stdin); ts={t[\"id\"]:t for t in d[\"tasks\"]}; rs={r[\"id\"]:r for r in d[\"requirements\"]}; cs={c[\"id\"]:c for c in d[\"checks\"]}; out={k:d[k] for k in [\"saved_revision\",\"fresh\",\"valid_artifacts\"]}; out[\"drift_paths\"]=[s[\"path\"] for s in d[\"source_drift\"]]; out[\"tasks\"]=[{\"id\":t[\"id\"],\"status\":t[\"status\"],\"eligible\":d[\"valid_artifacts\"] and t[\"status\"] in [\"draft\",\"ready\"] and all(ts[x][\"status\"]==\"verified\" for x in t[\"depends_on\"]) and all(rs[x][\"status\"]==\"active\" for x in t[\"requirement_ids\"]),\"dependency_ids\":t[\"depends_on\"],\"requirement_ids\":t[\"requirement_ids\"],\"intended_paths\":t[\"intended_paths\"],\"check_commands\":[cs[x][\"command\"] for x in t[\"check_ids\"]]} for t in [ts[\"TASK-041\"],ts[\"TASK-080\"]]]; print(json.dumps(out,indent=2))'"
```

## 14-07-dense-80-baseline

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-followup-20260908/homes/baseline/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/14-07-dense-80-baseline/work --json inspect'
```

```sh
/bin/zsh -lc 'rg --files --hidden .wigtn'
```

```sh
/bin/zsh -lc 'cat references/workgraph-contract.md'
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; p=json.loads(Path(\".wigtn/workgraph.json\").read_text()); print(json.dumps({\"revision\":p[\"revision\"],\"tasks\":[t for t in p[\"tasks\"] if t[\"id\"] in [\"TASK-041\",\"TASK-080\"]],\"checks\":[c for c in p[\"checks\"] if c[\"id\"] in [\"CHK-041\",\"CHK-080\"]]}))'"
```

## 15-08-invalid-80-candidate

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-followup-20260908/homes/candidate/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/15-08-invalid-80-candidate/work --json inspect --task TASK-041 --task TASK-080'
```

## 16-08-invalid-80-baseline

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-followup-20260908/homes/baseline/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md
cat /private/tmp/wigtn-scoped-followup-20260908/homes/baseline/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-followup-20260908/runs/16-08-invalid-80-baseline/work --json inspect'
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; p=json.loads(Path(\".wigtn/workgraph.json\").read_text()); print(json.dumps({\"revision\":p[\"revision\"],\"tasks\":[t for t in p[\"tasks\"] if t[\"id\"] in [\"TASK-041\",\"TASK-080\"]],\"checks\":[c for c in p[\"checks\"] if any(t in [\"TASK-041\",\"TASK-080\"] for t in c[\"task_ids\"])]},indent=2))'"
```
