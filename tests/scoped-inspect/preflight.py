#!/usr/bin/env python3
"""Check construction-derived expected state against both CLI views; no model calls."""
import hashlib,json,subprocess,sys
from pathlib import Path
r=Path(sys.argv[1]).resolve();protocol=json.loads((r/'protocol.json').read_text());rows=[]
for name,case in protocol['cases'].items():
 row={'case':name};expected=case['expected']
 for arm in ['baseline','candidate']:
  command=[sys.executable,'-B',str(r/'snapshots'/arm/'plugins/wigtn-plugins-with-codex/scripts/wigtn.py'),'--root',str(r/'fixtures'/name),'--json','inspect']
  if arm=='candidate':
   for task in expected['tasks']:command+=['--task',task['id']]
  result=subprocess.run(command,capture_output=True,text=True);data=json.loads(result.stdout)
  (r/f'preflight-{name}-{arm}.json').write_text(result.stdout)
  assert result.returncode==(0 if expected['fresh'] and expected['valid_artifacts'] else 1),(name,arm,result.stdout)
  assert data['valid_artifacts']==expected['valid_artifacts']
  assert data['fresh']==expected['fresh']
  assert sorted(x['path'] for x in data['source_drift'])==expected['drift_paths']
  for exp in expected['tasks']:
   task=next(t for t in data['tasks'] if t['id']==exp['id'])
   assert task['status']==exp['status'],(name,task,exp)
   assert (task['id'] in [t['id'] for t in data['next_tasks']])==exp['eligible']
   assert task['depends_on']==exp['dependency_ids']
   assert task['requirement_ids']==exp['requirement_ids']
   assert task['intended_paths']==exp['intended_paths']
   assert sorted(c['command'] for c in data['checks'] if c['id'] in task['check_ids'])==sorted(exp['check_commands'])
  row[arm+'_bytes']=len(result.stdout.encode())
 row['reduction_percent']=round(100*(1-row['candidate_bytes']/row['baseline_bytes']),2);rows.append(row)
(r/'deterministic-results.json').write_text(json.dumps(rows,indent=2)+'\n')
manifest=json.loads((r/'input-manifest.json').read_text())
assert all(hashlib.sha256((r/p).read_bytes()).hexdigest()==sha for p,sha in manifest.items())
print(json.dumps(rows,indent=2))
