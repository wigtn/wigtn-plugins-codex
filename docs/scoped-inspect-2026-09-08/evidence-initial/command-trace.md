## 01-01-small-6-candidate

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-study-20260908/homes/candidate/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md'
```

```sh
/bin/zsh -lc 'cat references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 -B ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/01-01-small-6-candidate/work --json inspect --task TASK-004 --task TASK-006'
```

## 02-01-small-6-baseline

```sh
/bin/zsh -lc 'cat skills/work-planner/SKILL.md skills/work-planner/references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 -B ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/02-01-small-6-baseline/work --json inspect'
```

## 03-01-small-6-bare

```sh
/bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '.wigtn/**' -g '"'!.git/**'"' --hidden"
```

```sh
/bin/zsh -lc 'cat .wigtn/project.json .wigtn/workgraph.json .wigtn/evidence.json .wigtn/history.txt'
```

```sh
/bin/zsh -lc "python3 -B -c 'import json,hashlib
from pathlib import Path
g=json.loads(Path(\".wigtn/workgraph.json\").read_text())
p=json.loads(Path(\".wigtn/project.json\").read_text())
e=json.loads(Path(\".wigtn/evidence.json\").read_text())
errors=[]
ix={}
for k in (\"sources\",\"requirements\",\"artifacts\",\"tasks\",\"checks\",\"release_gates\"):
 ix[k]={r[\"id\"]:r for r in g[k]}
 if len(ix[k])"'!=len(g[k]): errors.append("duplicate IDs")
drift=[s["path"] for s in g["sources"] if not Path(s["path"]).is_file() or hashlib.sha256(Path(s["path"]).read_bytes()).hexdigest()!=s["sha256"]]
for r in g["requirements"]:
 if r["source_id"] not in ix["sources"] or r["source_sha256"]!=ix["sources"][r["source_id"]]["sha256"]: errors.append("source link")
for kind,links in [("tasks",{"depends_on":"tasks","requirement_ids":"requirements","artifact_ids":"artifacts","check_ids":"checks"}),("checks",{"task_ids":"tasks","requirement_ids":"requirements"}),("release_gates",{"requires_task_ids":"tasks","requires_requirement_ids":"requirements"})]:
 for r in g[kind]:
  for key,target in links.items():
   if any(v not in ix[target] for v in r[key]): errors.append("bad reference")
for t in g["tasks"]:
 for c in t["check_ids"]:
  if t["id"] not in ix["checks"][c]["task_ids"]: errors.append("check backlink")
 for f in t["evidence_refs"]:
  if not Path(f).is_file(): errors.append("missing evidence")
for c in g["checks"]:
 if c["evidence_ref"] and not Path(c["evidence_ref"]).is_file(): errors.append("missing evidence")
seen=set()
visiting=set()
def visit(i):
 if i in visiting: errors.append("cycle"); return
 if i in seen: return
 visiting.add(i)
 for d in ix["tasks"][i]["depends_on"]: visit(d)
 visiting.remove(i)
 seen.add(i)
for i in ix["tasks"]: visit(i)
if p["schema_version"]!="1.0" or e["schema_version"]!="1.0" or g["schema_version"]!="1.0": errors.append("version")
if set(p["requirement_sources"])!=set(s["path"] for s in g["sources"]): errors.append("sources")
if not isinstance(e["requirements"],list) or not isinstance(e["checks"],list) or not isinstance(e["source_artifacts"],list) or not isinstance(e["external_actions"],list) or not isinstance(e["limitations"],list): errors.append("evidence structure")
if any(type(e["release_authority"][k]) is not bool for k in ("commit","push","pull_request","deploy")): errors.append("authority")
stale={r["id"] for r in g["requirements"] if ix["sources"][r["source_id"]]["path"] in drift}
status={t["id"]:("stale" if stale.intersection(t["requirement_ids"]) else t["status"]) for t in g["tasks"]}
out=dict(saved_revision=g["revision"],fresh=not drift,valid_artifacts=not errors,drift_paths=drift,tasks=[])
for i in ("TASK-004","TASK-006"):
 t=ix["tasks"][i]
 eligible=not errors and status[i] in ("draft","ready") and all(status[d]=="verified" for d in t["depends_on"]) and all(r not in stale and ix["requirements"][r]["status"]=="active" for r in t["requirement_ids"])
 out["tasks"].append(dict(id=i,status=status[i],eligible=eligible,dependency_ids=t["depends_on"],requirement_ids=t["requirement_ids"],intended_paths=t["intended_paths"],check_commands=[ix["checks"][c]["command"] for c in t["check_ids"]]))
print(json.dumps(dict(errors=errors,result=out),indent=2))
'"'"
```

## 04-02-small-12-bare

```sh
/bin/zsh -lc "pwd; rg --files --hidden -g '"'!.git'"' -g 'AGENTS.md' -g '.wigtn/**'"
```

```sh
/bin/zsh -lc 'cat .wigtn/project.json .wigtn/workgraph.json .wigtn/evidence.json .wigtn/history.txt'
```

```sh
/bin/zsh -lc "python3 -B -c 'import json,hashlib,pathlib
root=pathlib.Path.cwd()
g=json.loads(pathlib.Path(\".wigtn/workgraph.json\").read_text())
p=json.loads(pathlib.Path(\".wigtn/project.json\").read_text())
e=json.loads(pathlib.Path(p[\"evidence_path\"]).read_text())
m={k:{r[\"id\"]:r for r in g[k]} for k in (\"sources\",\"requirements\",\"artifacts\",\"tasks\",\"checks\",\"release_gates\")}
assert all(len(m[k])==len(g[k]) for k in m)
assert all(x[\"schema_version\"]==\"1.0\" for x in (g,p,e))
assert isinstance(g[\"revision\"],int)
assert set(p[\"requirement_sources\"])=={s[\"path\"] for s in g[\"sources\"]}
for r in g[\"requirements\"]:
 assert r[\"source_id\"] in m[\"sources\"]
 assert r[\"source_sha256\"]==m[\"sources\"][r[\"source_id\"]][\"sha256\"]
 assert r[\"status\"] in (\"active\",\"stale\",\"retired\")
for t in g[\"tasks\"]:
 for field,key in ((\"depends_on\",\"tasks\"),(\"requirement_ids\",\"requirements\"),(\"artifact_ids\",\"artifacts\"),(\"check_ids\",\"checks\")):
  assert isinstance(t[field],list) and all(v in m[key] for v in t[field])
 assert t[\"status\"] in (\"draft\",\"ready\",\"in_progress\",\"blocked\",\"verified\",\"stale\",\"done\")
 assert all(pathlib.Path(v).is_file() for v in t[\"evidence_refs\"])
 for c in t[\"check_ids\"]: assert t[\"id\"] in m[\"checks\"][c][\"task_ids\"]
for c in g[\"checks\"]:
 assert all(v in m[\"tasks\"] for v in c[\"task_ids\"])
 assert all(v in m[\"requirements\"] for v in c[\"requirement_ids\"])
 assert isinstance(c[\"command\"],str)
 assert c[\"evidence_ref\"] is None or pathlib.Path(c[\"evidence_ref\"]).is_file()
for gate in g[\"release_gates\"]:
 assert all(v in m[\"tasks\"] for v in gate[\"requires_task_ids\"])
 assert all(v in m[\"requirements\"] for v in gate[\"requires_requirement_ids\"])
def visit(tid,ancestors):
 assert tid not in ancestors
 for dep in m[\"tasks\"][tid][\"depends_on\"]: visit(dep,ancestors|{tid})
for tid in m[\"tasks\"]:visit(tid,set())
assert e[\"artifact_type\"]==\"acceptance\"
assert all(isinstance(e[k],list) for k in (\"source_artifacts\",\"requirements\",\"checks\",\"external_actions\",\"limitations\"))
assert all(isinstance(e[\"release_authority\"][k],bool) for k in (\"commit\",\"push\",\"pull_request\",\"deploy\"))
drift=[]; stale=set()
for s in g[\"sources\"]:
 f=root/s[\"path\"]
 assert f.resolve().is_relative_to(root)
 assert len(s[\"sha256\"])==64 and all(c in \"0123456789abcdef\" for c in s[\"sha256\"])
 if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()"'!=s["sha256"]: drift.append(s["path"]); stale.add(s["id"])
rs={r["id"]:("stale" if r["source_id"] in stale else r["status"]) for r in g["requirements"]}
ts={t["id"]:("stale" if any(rs[r]=="stale" for r in t["requirement_ids"]) else t["status"]) for t in g["tasks"]}
out=[]
for tid in ("TASK-007","TASK-012"):
 t=m["tasks"][tid]
 out.append(dict(id=tid,status=ts[tid],eligible=ts[tid] in ("draft","ready") and all(ts[d]=="verified" for d in t["depends_on"]) and all(rs[r]=="active" for r in t["requirement_ids"]),dependency_ids=t["depends_on"],requirement_ids=t["requirement_ids"],intended_paths=t["intended_paths"],check_commands=[m["checks"][c]["command"] for c in t["check_ids"]]))
print(json.dumps(dict(saved_revision=g["revision"],fresh=not drift,valid_artifacts=True,drift_paths=drift,tasks=out),indent=2))'"'"
```

## 05-02-small-12-candidate

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-study-20260908/homes/candidate/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md'
```

```sh
/bin/zsh -lc 'cat references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 -B ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/05-02-small-12-candidate/work --json inspect --task TASK-007 --task TASK-012'
```

## 06-02-small-12-baseline

```sh
/bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '.wigtn/**' -g '"'!node_modules'"' --hidden"
```

```sh
/bin/zsh -lc 'cat SKILL.md references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/06-02-small-12-baseline/work --json inspect'
```

## 07-03-large-80-baseline

```sh
/bin/zsh -lc 'cat SKILL.md references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/07-03-large-80-baseline/work --json inspect'
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; p=json.loads(Path(\".wigtn/workgraph.json\").read_text()); checks={c[\"id\"]:c for c in p[\"checks\"]}; print(json.dumps({\"saved_revision\":p[\"revision\"],\"tasks\":[{**t,\"check_commands\":[checks[c][\"command\"] for c in t[\"check_ids\"]]} for t in p[\"tasks\"] if t[\"id\"] in [\"TASK-041\",\"TASK-080\"]]},indent=2))'"
```

## 08-03-large-80-bare

```sh
/bin/zsh -lc 'pwd; rg --files --hidden .wigtn'
```

```sh
/bin/zsh -lc 'cat .wigtn/project.json .wigtn/workgraph.json .wigtn/evidence.json .wigtn/history.txt'
```

```sh
/bin/zsh -lc "python3 -c 'import json,pathlib,hashlib,collections
p=pathlib.Path(\".\");g=json.loads((p/\".wigtn/workgraph.json\").read_text())
print(\"keys\",list(g))
for k,v in g.items():
 if isinstance(v,list): print(k,len(v),\"shapes\",dict(collections.Counter(tuple(sorted(x)) for x in v if isinstance(x,dict))))
for t in g[\"tasks\"]:
 if t[\"id\"] in [\"TASK-041\",\"TASK-080\"]: print(\"selected\",json.dumps(t))
print(\"sample task\",json.dumps(g[\"tasks\"][0]))
drift=[]
for s in g[\"sources\"]:
 q=p/s[\"path\"]
 assert q.resolve().is_relative_to(p.resolve())
 if not q.is_file() or hashlib.sha256(q.read_bytes()).hexdigest()"'!=s["sha256"]: drift.append(s)
print("drift",json.dumps(drift))
print("statuses",{k:dict(collections.Counter(x.get("status") for x in g[k])) for k in ["requirements","tasks","checks"]})'"'"
```

```sh
/bin/zsh -lc "python3 -c 'import json,pathlib,re
root=pathlib.Path.cwd();errors=[]
def pairs(items):
 d={}
 for k,v in items:
  if k in d: errors.append(\"duplicate key \"+k)
  d[k]=v
 return d
g=json.loads((root/\".wigtn/workgraph.json\").read_text(),object_pairs_hook=pairs)
p=json.loads((root/\".wigtn/project.json\").read_text(),object_pairs_hook=pairs)
e=json.loads((root/\".wigtn/evidence.json\").read_text(),object_pairs_hook=pairs)
def check(ok,msg):
 if not ok: errors.append(msg)
indices={}
for group in [\"sources\",\"requirements\",\"artifacts\",\"tasks\",\"checks\",\"release_gates\"]:
 rows=g[group];indices[group]={x[\"id\"]:x for x in rows};check(len(indices[group])==len(rows),\"duplicate ids \"+group)
def refs(row,key,group):
 check(isinstance(row[key],list),key)
 for ident in row[key]: check(ident in indices[group],row[\"id\"]+\" dangling \"+ident)
for s in g[\"sources\"]: check(bool(re.fullmatch(\"[0-9a-f]{64}\",s[\"sha256\"])),\"hash format\")
for r in g[\"requirements\"]:
 check(r[\"source_id\"] in indices[\"sources\"],\"source reference\")
 check(r[\"source_sha256\"]==indices[\"sources\"].get(r[\"source_id\"],{}).get(\"sha256\"),\"source hash link\")
 check(r[\"status\"] in [\"active\",\"stale\",\"retired\",\"superseded\"],\"requirement status\")
for t in g[\"tasks\"]:
 for key,group in [(\"depends_on\",\"tasks\"),(\"requirement_ids\",\"requirements\"),(\"artifact_ids\",\"artifacts\"),(\"check_ids\",\"checks\")]: refs(t,key,group)
 check(t[\"status\"] in [\"draft\",\"ready\",\"in_progress\",\"blocked\",\"verified\",\"stale\",\"done\",\"cancelled\"],\"task status\")
 for c in t[\"check_ids\"]: check(t[\"id\"] in indices[\"checks\"][c][\"task_ids\"],\"check task reciprocity\")
 for path in t[\"evidence_refs\"]: check((root/path).is_file(),\"missing evidence\")
for c in g[\"checks\"]:
 refs(c,\"task_ids\",\"tasks\");refs(c,\"requirement_ids\",\"requirements\")
 check(isinstance(c[\"command\"],str) and bool(c[\"command\"]),\"command type\")
 check(c[\"status\"] in [\"pending\",\"passed\",\"failed\",\"stale\",\"skipped\"],\"check status\")
 if c[\"evidence_ref\"]: check((root/c[\"evidence_ref\"]).is_file(),\"missing evidence\")
for gate in g[\"release_gates\"]:
 refs(gate,\"requires_task_ids\",\"tasks\");refs(gate,\"requires_requirement_ids\",\"requirements\")
visiting=set();done=set()
def visit(i):
 if i in visiting: errors.append(\"dependency cycle\");return
 if i in done:return
 visiting.add(i)
 for d in indices[\"tasks\"][i][\"depends_on\"]:
  if d in indices[\"tasks\"]:visit(d)
 visiting.remove(i);done.add(i)
for i in indices[\"tasks\"]:visit(i)
check(set(p[\"requirement_sources\"])=={s[\"path\"] for s in g[\"sources\"]},\"project source coverage\")
check(all(x[\"schema_version\"]==\"1.0\" for x in [g,p,e]),\"schema version\")
check(isinstance(g[\"revision\"],int) and g[\"revision\"]>=0,\"revision\")
check(e[\"artifact_type\"]==\"acceptance\" and all(isinstance(e[k],list) for k in [\"source_artifacts\",\"requirements\",\"checks\",\"external_actions\",\"limitations\"]),\"evidence structure\")
check(all(isinstance(e[\"release_authority\"][k],bool) for k in [\"commit\",\"push\",\"pull_request\",\"deploy\"]),\"authority structure\")
print(json.dumps({\"structural_errors\":errors,\"dependencies\":[indices[\"tasks\"][i] for i in [\"TASK-001\",\"TASK-002\"]]}))'"
```

## 09-03-large-80-candidate

```sh
/bin/zsh -lc 'cat skills/work-planner/SKILL.md skills/work-planner/references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 -B ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/09-03-large-80-candidate/work --json inspect --task TASK-041 --task TASK-080'
```

## 10-04-large-120-bare

```sh
/bin/zsh -lc 'ls -a .wigtn'
```

```sh
/bin/zsh -lc 'cat .wigtn/project.json .wigtn/workgraph.json .wigtn/evidence.json .wigtn/history.txt'
```

```sh
/bin/zsh -lc "python3 -c 'import json,pathlib,hashlib,collections; p=pathlib.Path(\".\"); g=json.loads((p/\".wigtn/workgraph.json\").read_text()); print(\"keys\",list(g)); print(\"samples\",{k:[len(v),v[:1]] for k,v in g.items() if isinstance(v,list)}); print(\"selected\",[t for t in g[\"tasks\"] if t[\"id\"] in [\"TASK-061\",\"TASK-120\"]]); print(\"drift\",[s for s in g[\"sources\"] if not (p/s[\"path\"]).is_file() or hashlib.sha256((p/s[\"path\"]).read_bytes()).hexdigest()"'!=s["sha256"]]); print("statuses",{k:dict(collections.Counter(x.get("status") for x in v)) for k,v in g.items() if isinstance(v,list)})'"'"
```

```sh
/bin/zsh -lc "python3 -c 'import json,pathlib,re; g=json.loads(pathlib.Path(\".wigtn/workgraph.json\").read_text()); p=json.loads(pathlib.Path(\".wigtn/project.json\").read_text()); e=json.loads(pathlib.Path(\".wigtn/evidence.json\").read_text()); errors=[]; groups=[\"sources\",\"requirements\",\"artifacts\",\"tasks\",\"checks\",\"release_gates\"]; maps={k:{x[\"id\"]:x for x in g[k]} for k in groups};
for k in groups:
 if len(maps[k])"'!=len(g[k]): errors.append("duplicate "+k)
 if g[k] and any(set(x)!=set(g[k][0]) for x in g[k]): errors.append("inconsistent fields "+k)
for s in g["sources"]:
 if not re.fullmatch("[0-9a-f]{64}",s["sha256"]): errors.append("hash "+s["id"])
for r in g["requirements"]:
 if r["source_id"] not in maps["sources"] or r["source_sha256"]!=maps["sources"][r["source_id"]]["sha256"]: errors.append("source ref "+r["id"])
for collection,fields in [("tasks",{"requirement_ids":"requirements","artifact_ids":"artifacts","depends_on":"tasks","check_ids":"checks"}),("checks",{"task_ids":"tasks","requirement_ids":"requirements"}),("release_gates",{"requires_task_ids":"tasks","requires_requirement_ids":"requirements"})]:
 for x in g[collection]:
  for field,target in fields.items():
   if not isinstance(x[field],list) or any(i not in maps[target] for i in x[field]): errors.append("bad ref "+x["id"]+" "+field)
seen=set(); visiting=set()
def visit(i):
 if i in visiting: errors.append("cycle "+i); return
 if i in seen: return
 visiting.add(i)
 for d in maps["tasks"][i]["depends_on"]:
  if d in maps["tasks"]: visit(d)
 visiting.remove(i); seen.add(i)
for i in maps["tasks"]: visit(i)
for t in g["tasks"]:
 for c in t["check_ids"]:
  if c in maps["checks"] and t["id"] not in maps["checks"][c]["task_ids"]: errors.append("check mismatch "+t["id"])
 for ref in t["evidence_refs"]:
  if not pathlib.Path(ref).is_file(): errors.append("missing evidence "+ref)
if set(p["requirement_sources"])!=set(s["path"] for s in g["sources"]): errors.append("project sources mismatch")
if not all(x["schema_version"]=="1.0" for x in [p,g,e]): errors.append("schema version")
print(json.dumps({"structural_errors":errors,"revision":g["revision"],"evidence":e,"requested_requirements":[maps["requirements"][i] for i in ["FR-061","FR-120"]],"dependencies":[maps["tasks"][i] for i in ["TASK-001","TASK-002"]],"checks":[maps["checks"][i] for i in ["CHK-061","CHK-120"]]}))'"'"
```

## 11-04-large-120-baseline

```sh
/bin/zsh -lc pwd
```

```sh
/bin/zsh -lc 'cat SKILL.md references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/11-04-large-120-baseline/work --json inspect'
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; p=json.loads(Path(\".wigtn/workgraph.json\").read_text()); checks={c[\"id\"]:c for c in p[\"checks\"]}; print(json.dumps({\"saved_revision\":p[\"revision\"],\"tasks\":[dict(id=t[\"id\"],status=t[\"status\"],dependency_ids=t[\"depends_on\"],requirement_ids=t[\"requirement_ids\"],intended_paths=t[\"intended_paths\"],check_commands=[checks[c][\"command\"] for c in t[\"check_ids\"]]) for t in p[\"tasks\"] if t[\"id\"] in [\"TASK-061\",\"TASK-120\"]]},indent=2))'"
```

## 12-04-large-120-candidate

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-study-20260908/homes/candidate/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/12-04-large-120-candidate/work --json inspect'
```

```sh
/bin/zsh -lc 'rg --files .wigtn'
```

```sh
/bin/zsh -lc 'cat references/workgraph-contract.md'
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; p=json.loads(Path(\".wigtn/workgraph.json\").read_text()); print(json.dumps([{\"task\":t,\"checks\":[c for c in p[\"checks\"] if c[\"id\"] in t[\"check_ids\"]]} for t in p[\"tasks\"] if t[\"id\"] in [\"TASK-061\",\"TASK-120\"]]))'"
```

## 13-05-drift-60-baseline

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-study-20260908/homes/baseline/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md'
```

```sh
/bin/zsh -lc "pwd; rg --files -g AGENTS.md -g '.wigtn/**' -g '"'!node_modules'"' --hidden"
```

```sh
/bin/zsh -lc 'cat references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/13-05-drift-60-baseline/work --json inspect'
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; g=json.loads(Path(\".wigtn/workgraph.json\").read_text()); print(json.dumps({\"saved_revision\":g[\"revision\"],\"tasks\":[t for t in g[\"tasks\"] if t[\"id\"] in [\"TASK-031\",\"TASK-060\"]],\"checks\":[c for c in g[\"checks\"] if c[\"id\"] in [\"CHK-031\",\"CHK-060\"]]}))'"
```

## 14-05-drift-60-candidate

```sh
/bin/zsh -lc 'cat skills/work-planner/SKILL.md skills/work-planner/references/workgraph-contract.md'
```

```sh
/bin/zsh -lc "rg --files --hidden -g AGENTS.md -g '.wigtn/**' -g '"'!.git/**'"'"
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/14-05-drift-60-candidate/work --json inspect --task TASK-031 --task TASK-060'
```

## 15-05-drift-60-bare

```sh
/bin/zsh -lc "pwd; rg --files -g 'AGENTS.md' -g '.wigtn/**' -g '"'!node_modules'"' -g '"'! .git'"' --hidden"
```

```sh
/bin/zsh -lc 'cat .wigtn/project.json .wigtn/workgraph.json .wigtn/evidence.json .wigtn/history.txt'
```

```sh
/bin/zsh -lc "python3 -B -c 'import json, hashlib, pathlib, re
root=pathlib.Path.cwd()
g=json.loads((root/'\\''.wigtn/workgraph.json'\\'').read_text())
p=json.loads((root/'\\''.wigtn/project.json'\\'').read_text())
e=json.loads((root/'\\''.wigtn/evidence.json'\\'').read_text())
errors=[]
indexes={}
for k in ['\\''sources'\\'','\\''requirements'\\'','\\''artifacts'\\'','\\''tasks'\\'','\\''checks'\\'','\\''release_gates'\\'']:
 rows=g.get(k,[])
 indexes[k]={x['\\''id'\\'']:x for x in rows}
 if len(indexes[k])"'!=len(rows): errors.append('"'\\''duplicate '\\''+k)
print('\\''graph fields'\\'',list(g))
print('\\''artifacts'\\'',g.get('\\''artifacts'\\''))
for kind, links in {'\\''requirements'\\'':{'\\''source_id'\\'':'\\''sources'\\''},'\\''tasks'\\'':{'\\''depends_on'\\'':'\\''tasks'\\'','\\''requirement_ids'\\'':'\\''requirements'\\'','\\''artifact_ids'\\'':'\\''artifacts'\\'','\\''check_ids'\\'':'\\''checks'\\''},'\\''checks'\\'':{'\\''task_ids'\\'':'\\''tasks'\\'','\\''requirement_ids'\\'':'\\''requirements'\\''},'\\''release_gates'\\'':{'\\''requires_task_ids'\\'':'\\''tasks'\\'','\\''requires_requirement_ids'\\'':'\\''requirements'\\''}}.items():
 for row in g.get(kind,[]):
  for field,target in links.items():
   vals=row.get(field,[])
   if isinstance(vals,str): vals=[vals]
   for v in vals:
    if v not in indexes[target]: errors.append('\\''dangling '\\''+row['\\''id'\\'']+'\\'' '\\''+field+'\\'' '\\''+v)
visiting=set(); done=set()
def visit(t):
 if t in visiting: errors.append('\\''cycle '\\''+t); return
 if t in done or t not in indexes['\\''tasks'\\'']: return
 visiting.add(t)
 for d in indexes['\\''tasks'\\''][t]['\\''depends_on'\\'']: visit(d)
 visiting.remove(t); done.add(t)
for t in indexes['\\''tasks'\\'']: visit(t)
drift=[]; stale_sources=set()
for s in g['\\''sources'\\'']:
 path=(root/s['\\''path'\\'']).resolve()
 assert path.is_relative_to(root)
 if not re.fullmatch('\\''[0-9a-f]{64}'\\'',s['\\''sha256'\\'']): errors.append('\\''bad hash '\\''+s['\\''id'\\''])
 if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()"'!=s['"'\\''sha256'\\'']:
  drift.append(s['\\''path'\\'']); stale_sources.add(s['\\''id'\\''])
for r in g['\\''requirements'\\'']:
 if r['\\''source_id'\\''] in indexes['\\''sources'\\''] and r['\\''source_sha256'\\'']"'!=indexes['"'\\''sources'\\''][r['\\''source_id'\\'']]['\\''sha256'\\'']: errors.append('\\''inconsistent source hash '\\''+r['\\''id'\\''])
for t in g['\\''tasks'\\'']:
 for c in t['\\''check_ids'\\'']:
  if c in indexes['\\''checks'\\''] and t['\\''id'\\''] not in indexes['\\''checks'\\''][c]['\\''task_ids'\\'']: errors.append('\\''check backlink '\\''+t['\\''id'\\''])
 for path in t['\\''evidence_refs'\\'']:
  full=(root/path).resolve(); assert full.is_relative_to(root)
  if not full.is_file(): errors.append('\\''missing evidence '\\''+path)
for c in g['\\''checks'\\'']:
 if c.get('\\''evidence_ref'\\''):
  full=(root/c['\\''evidence_ref'\\'']).resolve(); assert full.is_relative_to(root)
  if not full.is_file(): errors.append('\\''missing evidence '\\''+c['\\''id'\\''])
assert g['\\''schema_version'\\'']==p['\\''schema_version'\\'']==e['\\''schema_version'\\'']=='\\''1.0'\\''
assert isinstance(g['\\''revision'\\''],int)
assert set(p['\\''requirement_sources'\\''])=={s['\\''path'\\''] for s in g['\\''sources'\\'']}
print('\\''shapes'\\'',{k:sorted({tuple(sorted(x)) for x in g[k]}) for k in indexes if k in g})
print('\\''statuses'\\'',{k:sorted({x.get('\\''status'\\'','\\'''\\'') for x in g[k]}) for k in indexes if k in g})
print('\\''errors'\\'',errors)
stale_reqs={r['\\''id'\\''] for r in g['\\''requirements'\\''] if r['\\''source_id'\\''] in stale_sources}
rs={r['\\''id'\\'']:('\\''stale'\\'' if r['\\''id'\\''] in stale_reqs else r['\\''status'\\'']) for r in g['\\''requirements'\\'']}
ts={t['\\''id'\\'']:('\\''stale'\\'' if any(r in stale_reqs for r in t['\\''requirement_ids'\\'']) else t['\\''status'\\'']) for t in g['\\''tasks'\\'']}
out=[]
for id in ['\\''TASK-031'\\'','\\''TASK-060'\\'']:
 t=indexes['\\''tasks'\\''][id]
 out.append(dict(id=id,status=ts[id],eligible=not errors and ts[id] in ['\\''draft'\\'','\\''ready'\\''] and all(ts[d]=='\\''verified'\\'' for d in t['\\''depends_on'\\'']) and all(rs[r]=='\\''active'\\'' for r in t['\\''requirement_ids'\\'']),dependency_ids=t['\\''depends_on'\\''],requirement_ids=t['\\''requirement_ids'\\''],intended_paths=t['\\''intended_paths'\\''],check_commands=[indexes['\\''checks'\\''][c]['\\''command'\\''] for c in t['\\''check_ids'\\'']]))
print(json.dumps(dict(saved_revision=g['\\''revision'\\''],fresh=not drift,valid_artifacts=not errors,drift_paths=drift,tasks=out),indent=2))
'"
```

## 16-06-drift-100-baseline

```sh
/bin/zsh -lc 'cat skills/work-planner/SKILL.md skills/work-planner/references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/16-06-drift-100-baseline/work --json inspect'
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; p=json.loads(Path(\".wigtn/workgraph.json\").read_text()); print(json.dumps({\"revision\":p[\"revision\"],\"tasks\":[t for t in p[\"tasks\"] if t[\"id\"] in [\"TASK-051\",\"TASK-100\"]],\"checks\":[c for c in p[\"checks\"] if c[\"id\"] in [\"CHK-051\",\"CHK-100\"]]}))'"
```

## 17-06-drift-100-bare

```sh
/bin/zsh -lc "pwd; rg --files --hidden -g '"'!.git'"' -g 'AGENTS.md' -g '.wigtn/**'"
```

```sh
/bin/zsh -lc 'cat .wigtn/project.json .wigtn/workgraph.json .wigtn/evidence.json .wigtn/history.txt'
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; from collections import Counter; g=json.loads(Path(\".wigtn/workgraph.json\").read_text()); print(json.dumps({k: {\"count\":len(v),\"keys\":str(Counter(tuple(x.keys()) for x in v if isinstance(x,dict))),\"sample\":v[:1]} if isinstance(v,list) else v for k,v in g.items()},indent=2)); print(json.dumps([t for t in g[\"tasks\"] if t[\"id\"] in [\"TASK-051\",\"TASK-100\"]],indent=2)); print([str(p) for p in Path(\".\").iterdir()])'"
```

```sh
/bin/zsh -lc "python3 -c '
import json,hashlib,re
from pathlib import Path
root=Path.cwd()
def read(p):
 return json.loads(Path(p).read_text())
g=read(\".wigtn/workgraph.json\"); p=read(\".wigtn/project.json\"); e=read(\".wigtn/evidence.json\")
errors=[]
def require(ok,msg):
 if not ok: errors.append(msg)
for obj in (g,p,e): require(obj.get(\"schema_version\")==\"1.0\",\"schema version\")
require(type(g[\"revision\"]) is int and g[\"revision\"]>=0,\"revision\")
indices={}
for name in (\"sources\",\"requirements\",\"artifacts\",\"tasks\",\"checks\",\"release_gates\"):
 rows=g[name]; require(isinstance(rows,list),name)
 indices[name]={r[\"id\"]:r for r in rows}
 require(len(indices[name])==len(rows),\"duplicate \"+name)
 for r in rows: require(isinstance(r[\"id\"],str) and bool(r[\"id\"]),\"id\")
def refs(row,key,target):
 vals=row[key]; require(isinstance(vals,list) and all(isinstance(x,str) for x in vals),key)
 require(len(vals)==len(set(vals)),\"duplicate links \"+key)
 for v in vals: require(v in indices[target],\"dangling \"+key+\":\"+v)
sources=indices[\"sources\"]; reqs=indices[\"requirements\"]; tasks=indices[\"tasks\"]; checks=indices[\"checks\"]
drift=[]; stale_sources=set()
for s in sources.values():
 require(bool(re.fullmatch(\"[a-fA-F0-9]{64}\",s[\"sha256\"])),\"hash\")
 path=root/s[\"path\"]; require(path.resolve().is_relative_to(root),\"source outside workspace\")
 if path.resolve().is_relative_to(root) and (not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()"'!=s["sha256"]):
  drift.append(s["path"]); stale_sources.add(s["id"])
for r in reqs.values():
 require(r["source_id"] in sources,"source reference")
 require(r["source_sha256"]==sources[r["source_id"]]["sha256"],"saved source consistency")
 require(r["status"] in ("active","stale","retired"),"requirement status")
 require(isinstance(r["text"],str) and bool(r["text"]),"requirement text")
for t in tasks.values():
 for key,target in (("requirement_ids","requirements"),("artifact_ids","artifacts"),("depends_on","tasks"),("check_ids","checks")): refs(t,key,target)
 require(t["status"] in ("draft","ready","in_progress","blocked","implemented","verified","stale","cancelled"),"task status")
 for key in ("intended_paths","protected_paths","evidence_refs"):
  require(isinstance(t[key],list) and all(isinstance(x,str) for x in t[key]),key)
 for c in t["check_ids"]: require(t["id"] in checks[c]["task_ids"],"check backlink")
for c in checks.values():
 refs(c,"task_ids","tasks"); refs(c,"requirement_ids","requirements")
 require(isinstance(c["command"],str) and bool(c["command"]),"command")
 require(c["status"] in ("pending","passed","failed","blocked","skipped","stale"),"check status")
 require(c["evidence_ref"] is None or isinstance(c["evidence_ref"],str),"evidence reference")
for gate in g["release_gates"]:
 refs(gate,"requires_task_ids","tasks"); refs(gate,"requires_requirement_ids","requirements")
visited=set(); active=set()
def visit(tid):
 if tid in active: errors.append("dependency cycle"); return
 if tid in visited: return
 active.add(tid)
 for dep in tasks[tid]["depends_on"]:
  if dep in tasks: visit(dep)
 active.remove(tid); visited.add(tid)
for tid in tasks: visit(tid)
require(set(p["requirement_sources"])=={s["path"] for s in sources.values()},"project sources")
for key in ("requirement_sources","verification_commands","protected_paths"): require(isinstance(p[key],list) and all(isinstance(x,str) for x in p[key]),"project "+key)
require(p["evidence_path"]==".wigtn/evidence.json","evidence path")
require(e["artifact_type"]=="acceptance","evidence type")
for key in ("source_artifacts","requirements","checks","external_actions","limitations"): require(isinstance(e[key],list),"evidence "+key)
require(isinstance(e["release_authority"]["source_request"],str),"authority source")
for key in ("commit","push","pull_request","deploy"): require(type(e["release_authority"][key]) is bool,"authority "+key)
rstatus={r["id"]:"stale" if r["source_id"] in stale_sources else r["status"] for r in reqs.values()}
tstatus={t["id"]:"stale" if any(rstatus[r]=="stale" for r in t["requirement_ids"]) else t["status"] for t in tasks.values()}
result={"saved_revision":g["revision"],"fresh":not drift,"valid_artifacts":not errors,"drift_paths":drift,"tasks":[]}
for tid in ("TASK-051","TASK-100"):
 t=tasks[tid]; result["tasks"].append({"id":tid,"status":tstatus[tid],"eligible":not errors and tstatus[tid] in ("draft","ready") and all(tstatus[d]=="verified" for d in t["depends_on"]) and all(rstatus[r]=="active" for r in t["requirement_ids"]),"dependency_ids":t["depends_on"],"requirement_ids":t["requirement_ids"],"intended_paths":t["intended_paths"],"check_commands":[checks[c]["command"] for c in t["check_ids"]]})
print(json.dumps({"errors":errors,"assessment":result},indent=2))
'"'"
```

## 18-06-drift-100-candidate

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-study-20260908/homes/candidate/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md
cat /private/tmp/wigtn-scoped-study-20260908/homes/candidate/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/18-06-drift-100-candidate/work --json inspect --task TASK-051 --task TASK-100'
```

## 19-07-blocked-60-baseline

```sh
/bin/zsh -lc 'cat skills/work-planner/SKILL.md skills/work-planner/references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 -B ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/19-07-blocked-60-baseline/work --json inspect'
```

```sh
/bin/zsh -lc "python3 -B -c 'import json; from pathlib import Path; g=json.loads(Path(\".wigtn/workgraph.json\").read_text()); print(json.dumps({\"revision\":g[\"revision\"],\"tasks\":[t for t in g[\"tasks\"] if t[\"id\"] in [\"TASK-031\",\"TASK-060\"]],\"checks\":[c for c in g[\"checks\"] if c[\"id\"] in [\"CHK-031\",\"CHK-060\"]]},indent=2))'"
```

## 20-07-blocked-60-candidate

```sh
/bin/zsh -lc 'cat skills/work-planner/SKILL.md skills/work-planner/references/workgraph-contract.md'
```

```sh
/bin/zsh -lc 'python3 -B ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/20-07-blocked-60-candidate/work --json inspect --task TASK-031 --task TASK-060'
```

## 21-07-blocked-60-bare

```sh
/bin/zsh -lc "pwd; rg --files --hidden -g '"'!.git'"' -g 'AGENTS.md' -g '.wigtn/**'"
```

```sh
/bin/zsh -lc 'cat .wigtn/project.json .wigtn/workgraph.json .wigtn/evidence.json .wigtn/history.txt'
```

```sh
/bin/zsh -lc "python3 -B -c 'import json,pathlib,hashlib,collections
root=pathlib.Path.cwd()
g=json.loads((root/\".wigtn/workgraph.json\").read_text())
print(\"structure\",{k:len(v) if isinstance(v,list) else v for k,v in g.items() if k not in [\"sources\",\"requirements\",\"tasks\",\"checks\"]})
for k in [\"sources\",\"requirements\",\"tasks\",\"checks\"]:
 print(k,\"count\",len(g[k]),\"keysets\",collections.Counter(tuple(sorted(x)) for x in g[k]))
print(\"selected\",json.dumps([t for t in g[\"tasks\"] if t[\"id\"] in [\"TASK-001\",\"TASK-002\",\"TASK-031\",\"TASK-060\"]],indent=2))
drift=[]
for s in g[\"sources\"]:
 p=(root/s[\"path\"]).resolve()
 assert p.is_relative_to(root)
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()"'!=s["sha256"]: drift.append(s["path"])
print("drift",drift)
print("statuses",{k:dict(collections.Counter(x["status"] for x in g[k])) for k in ["requirements","tasks","checks"]})'"'"
```

```sh
/bin/zsh -lc "python3 -B -c 'import json,pathlib,re
root=pathlib.Path.cwd()
def read(p):
 return json.loads((root/p).read_text(),object_pairs_hook=unique)
def unique(pairs):
 d={}
 for k,v in pairs:
  assert k not in d, \"duplicate key\"
  d[k]=v
 return d
g=read(\".wigtn/workgraph.json\"); p=read(\".wigtn/project.json\"); e=read(\".wigtn/evidence.json\")
assert all(x[\"schema_version\"]==\"1.0\" for x in [g,p,e])
assert type(g[\"revision\"]) is int and g[\"revision\"]>=0
maps={}
for key in [\"sources\",\"requirements\",\"artifacts\",\"tasks\",\"checks\",\"release_gates\"]:
 assert isinstance(g[key],list)
 maps[key]={x[\"id\"]:x for x in g[key]}
 assert len(maps[key])==len(g[key])
def refs(obj,key,target):
 assert isinstance(obj[key],list) and all(isinstance(x,str) for x in obj[key])
 assert len(set(obj[key]))==len(obj[key])
 assert all(x in maps[target] for x in obj[key]), (obj[\"id\"],key)
def path(s):
 assert isinstance(s,str) and s and not pathlib.Path(s).is_absolute()
 assert (root/s).resolve().is_relative_to(root)
for s in g[\"sources\"]:
 path(s[\"path\"]); assert re.fullmatch(\"[0-9a-f]{64}\",s[\"sha256\"])
for r in g[\"requirements\"]:
 assert r[\"source_id\"] in maps[\"sources\"]
 assert r[\"source_sha256\"]==maps[\"sources\"][r[\"source_id\"]][\"sha256\"]
 assert isinstance(r[\"text\"],str) and r[\"status\"] in [\"active\",\"stale\",\"retired\",\"superseded\"]
for t in g[\"tasks\"]:
 for key,target in [(\"requirement_ids\",\"requirements\"),(\"artifact_ids\",\"artifacts\"),(\"depends_on\",\"tasks\"),(\"check_ids\",\"checks\")]: refs(t,key,target)
 assert t[\"status\"] in [\"draft\",\"ready\",\"in_progress\",\"blocked\",\"implemented\",\"verified\",\"stale\",\"cancelled\"]
 assert t[\"risk\"] in [\"low\",\"medium\",\"high\"]
 assert t[\"blocker\"] is None or isinstance(t[\"blocker\"],str)
 for key in [\"intended_paths\",\"protected_paths\",\"evidence_refs\"]:
  assert isinstance(t[key],list)
  for s in t[key]: path(s)
 for s in t[\"evidence_refs\"]: assert (root/s).is_file()
 for c in t[\"check_ids\"]: assert t[\"id\"] in maps[\"checks\"][c][\"task_ids\"]
for c in g[\"checks\"]:
 refs(c,\"task_ids\",\"tasks\"); refs(c,\"requirement_ids\",\"requirements\")
 assert isinstance(c[\"command\"],str) and c[\"command\"]
 assert c[\"status\"] in [\"pending\",\"passed\",\"failed\",\"blocked\",\"stale\",\"skipped\"]
 if c[\"evidence_ref\"] is not None:
  path(c[\"evidence_ref\"]); assert (root/c[\"evidence_ref\"]).is_file()
 for t in c[\"task_ids\"]: assert c[\"id\"] in maps[\"tasks\"][t][\"check_ids\"]
visited=set(); stack=set()
def visit(t):
 assert t not in stack,\"dependency cycle\"
 if t in visited:return
 stack.add(t)
 for d in maps[\"tasks\"][t][\"depends_on\"]:visit(d)
 stack.remove(t);visited.add(t)
for t in maps[\"tasks\"]:visit(t)
for gate in g[\"release_gates\"]:
 refs(gate,\"requires_task_ids\",\"tasks\");refs(gate,\"requires_requirement_ids\",\"requirements\")
 assert isinstance(gate[\"authority_actions\"],list)
assert set(p[\"requirement_sources\"])=={s[\"path\"] for s in g[\"sources\"]}
for key in [\"requirement_sources\",\"protected_paths\",\"verification_commands\"]: assert isinstance(p[key],list) and all(isinstance(s,str) for s in p[key])
path(p[\"evidence_path\"])
assert e[\"artifact_type\"]==\"acceptance\"
for key in [\"source_artifacts\",\"requirements\",\"checks\",\"external_actions\",\"limitations\"]: assert isinstance(e[key],list)
assert isinstance(e[\"release_authority\"][\"source_request\"],str)
for key in [\"commit\",\"push\",\"pull_request\",\"deploy\"]:assert type(e[\"release_authority\"][key]) is bool
print(\"Artifact structure and graph references valid; no dependency cycles.\")
print(json.dumps([{ \"id\":t[\"id\"],\"status\":t[\"status\"],\"eligible\":t[\"status\"] in [\"draft\",\"ready\"] and all(maps[\"tasks\"][d][\"status\"]==\"verified\" for d in t[\"depends_on\"]) and all(maps[\"requirements\"][r][\"status\"]==\"active\" for r in t[\"requirement_ids\"]),\"dependency_ids\":t[\"depends_on\"],\"requirement_ids\":t[\"requirement_ids\"],\"intended_paths\":t[\"intended_paths\"],\"check_commands\":[maps[\"checks\"][c][\"command\"] for c in t[\"check_ids\"]]} for t in g[\"tasks\"] if t[\"id\"] in [\"TASK-031\",\"TASK-060\"]]))'"
```

## 22-08-blocked-100-bare

```sh
/bin/zsh -lc 'pwd; rg --files --hidden .wigtn'
```

```sh
/bin/zsh -lc 'cat .wigtn/project.json .wigtn/workgraph.json .wigtn/evidence.json .wigtn/history.txt'
```

```sh
/bin/zsh -lc "python3 -c 'import json,pathlib,hashlib,collections; p=pathlib.Path(\".\"); g=json.loads((p/\".wigtn/workgraph.json\").read_text()); print(\"graph keys\",list(g)); [(print(k,len(v),\"shapes\",dict(collections.Counter(tuple(sorted(x)) for x in v if isinstance(x,dict)))),print(\"sample\",v[0] if v else None)) for k,v in g.items() if isinstance(v,list)]; print(\"requested\",[t for t in g[\"tasks\"] if t[\"id\"] in [\"TASK-051\",\"TASK-100\"]]); print(\"nonverified\",[(t[\"id\"],t[\"status\"]) for t in g[\"tasks\"] if t[\"status\"]"'!="verified"]); print("req statuses",collections.Counter(r["status"] for r in g["requirements"])); print("drift",[s["path"] for s in g["sources"] if not (p/s["path"]).is_file() or hashlib.sha256((p/s["path"]).read_bytes()).hexdigest()!=s["sha256"]])'"'"
```

```sh
/bin/zsh -lc "python3 -c 'import json,pathlib,re; p=pathlib.Path(\".\"); g=json.loads((p/\".wigtn/workgraph.json\").read_text()); project=json.loads((p/\".wigtn/project.json\").read_text()); e=json.loads((p/\".wigtn/evidence.json\").read_text()); errors=[]; groups={k:{x[\"id\"]:x for x in g[k]} for k in [\"sources\",\"requirements\",\"artifacts\",\"tasks\",\"checks\",\"release_gates\"]};
for k,items in groups.items():
 if len(items)"'!=len(g[k]): errors.append("duplicate "+k)
def refs(obj,key,target):
 for v in obj[key]:
  if v not in groups[target]: errors.append(str((obj.get("id"),key,v)))
for s in g["sources"]:
 if not re.fullmatch("[0-9a-f]{64}",s["sha256"]): errors.append("hash format")
for r in g["requirements"]:
 if r["source_id"] not in groups["sources"] or r["source_sha256"]!=groups["sources"][r["source_id"]]["sha256"]: errors.append("requirement source")
 if r["status"] not in ["active","stale","retired","superseded"]: errors.append("requirement status")
for t in g["tasks"]:
 for key,target in [("requirement_ids","requirements"),("artifact_ids","artifacts"),("depends_on","tasks"),("check_ids","checks")]: refs(t,key,target)
 if t["status"] not in ["draft","ready","in_progress","blocked","implemented","verified","stale","cancelled"]: errors.append("task status")
 for c in t["check_ids"]:
  if c in groups["checks"] and t["id"] not in groups["checks"][c]["task_ids"]: errors.append("check backlink")
for c in g["checks"]:
 refs(c,"task_ids","tasks"); refs(c,"requirement_ids","requirements")
 if not isinstance(c["command"],str) or not c["command"]: errors.append("command")
 if c["status"] not in ["pending","passed","failed","blocked","skipped","stale"]: errors.append("check status")
 if c["evidence_ref"] and not (p/c["evidence_ref"]).is_file(): errors.append("missing evidence")
for gate in g["release_gates"]:
 refs(gate,"requires_task_ids","tasks"); refs(gate,"requires_requirement_ids","requirements")
seen=set(); visiting=set()
def visit(i):
 if i in visiting: errors.append("cycle"); return
 if i in seen: return
 visiting.add(i)
 for dep in groups["tasks"][i]["depends_on"]:
  if dep in groups["tasks"]: visit(dep)
 visiting.remove(i); seen.add(i)
for i in groups["tasks"]: visit(i)
if set(project["requirement_sources"])!={s["path"] for s in g["sources"]}: errors.append("source catalog mismatch")
if not all(x["schema_version"]=="1.0" for x in [g,project,e]): errors.append("version")
if not isinstance(g["revision"],int) or g["revision"]<1: errors.append("revision")
print(json.dumps({"errors":errors,"evidence":e,"revision":g["revision"],"selected_checks":[c for c in g["checks"] if c["id"] in ["CHK-051","CHK-100"]]}))'"'"
```

## 23-08-blocked-100-baseline

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-study-20260908/homes/baseline/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md'
```

```sh
/bin/zsh -lc 'python3 ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/23-08-blocked-100-baseline/work --json inspect'
```

```sh
/bin/zsh -lc 'rg --files --hidden .wigtn'
```

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-study-20260908/homes/baseline/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/references/workgraph-contract.md'
```

```sh
/bin/zsh -lc "python3 -c 'import json; from pathlib import Path; g=json.loads(Path(\".wigtn/workgraph.json\").read_text()); print(\"saved_revision\",g[\"revision\"]); ts=[t for t in g[\"tasks\"] if t[\"id\"] in [\"TASK-051\",\"TASK-100\"]]; print(json.dumps(ts)); print(json.dumps([c for c in g[\"checks\"] if any(t[\"id\"] in c.get(\"task_ids\",[]) for t in ts)])); print(json.dumps([d for d in g[\"tasks\"] if any(d[\"id\"] in t.get(\"dependency_ids\",[]) for t in ts)]))'"
```

## 24-08-blocked-100-candidate

```sh
/bin/zsh -lc 'cat /private/tmp/wigtn-scoped-study-20260908/homes/candidate/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/SKILL.md
cat /private/tmp/wigtn-scoped-study-20260908/homes/candidate/plugins/cache/wigtn/wigtn-plugins-with-codex/0.5.4/skills/work-planner/references/workgraph-contract.md'
```

```sh
/bin/zsh -lc "pwd
rg --files --hidden -g AGENTS.md -g '.wigtn/**' -g '"'!**/.git/**'"'"
```

```sh
/bin/zsh -lc 'python3 -B ../../scripts/wigtn.py --root /private/tmp/wigtn-scoped-study-20260908/runs/24-08-blocked-100-candidate/work --json inspect --task TASK-051 --task TASK-100'
```
