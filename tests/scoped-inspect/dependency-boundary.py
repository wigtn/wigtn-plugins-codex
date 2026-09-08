#!/usr/bin/env python3
"""Post-freeze deterministic boundary check; no model calls."""
import json,sys,shutil,subprocess,tempfile
from pathlib import Path
r=Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as tmp:
 w=Path(tmp)/'work';shutil.copytree(r/'fixtures/03-large-80',w)
 p=w/'.wigtn/workgraph.json';g=json.loads(p.read_text())
 for i,t in enumerate(g['tasks']):
  t['depends_on']=[g['tasks'][i-1]['id']] if i else []
  t['status']='verified';t['evidence_refs']=['.wigtn/history.txt']
  g['checks'][i]['status']='passed';g['checks'][i]['evidence_ref']='.wigtn/history.txt'
 g['tasks'][-1]['status']='ready';g['tasks'][-1]['evidence_refs']=[]
 g['checks'][-1]['status']='pending';g['checks'][-1]['evidence_ref']=None
 p.write_text(json.dumps(g));row={'scenario':'80-task-chain-select-last','note':'Post-freeze deterministic boundary test, no model calls.'}
 for arm in ['baseline','candidate']:
  cmd=[sys.executable,'-B',str(r/'snapshots'/arm/'plugins/wigtn-plugins-with-codex/scripts/wigtn.py'),'--root',str(w),'--json','inspect']
  if arm=='candidate':cmd+=['--task','TASK-080']
  result=subprocess.run(cmd,text=True,capture_output=True);d=json.loads(result.stdout);assert result.returncode==0,result.stdout
  assert len(d['tasks'])==80;row[arm+'_bytes']=len(result.stdout.encode())
 row['reduction_percent']=round(100*(1-row['candidate_bytes']/row['baseline_bytes']),2)
 (r/'dense-dependency-result.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row,indent=2))
