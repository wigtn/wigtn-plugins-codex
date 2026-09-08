import copy,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
R=Path(sys.argv[1]).resolve();CLI=R/'snapshots/candidate/plugins/wigtn-plugins-with-codex/scripts/wigtn.py'
results=[]
def tree(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file()}
for scenario in ['invalid-project','invalid-evidence','unrelated-invalid-task','missing-selected-source','missing-unrelated-source','shared-check-unrelated-requirement']:
 with tempfile.TemporaryDirectory() as tmp:
  r=Path(tmp)/'work';shutil.copytree(R/'fixtures/03-large-80',r)
  g=json.loads((r/'.wigtn/workgraph.json').read_text())
  if scenario=='invalid-project':
   p=r/'.wigtn/project.json';d=json.loads(p.read_text());d['verification_commands']=7;p.write_text(json.dumps(d))
  if scenario=='invalid-evidence':(r/'.wigtn/evidence.json').write_text('{')
  if scenario=='unrelated-invalid-task':g['tasks'][75]['depends_on']=['TASK-MISSING']
  if scenario=='missing-selected-source':(r/'docs/requirement-041.md').unlink()
  if scenario=='missing-unrelated-source':(r/'docs/requirement-076.md').unlink()
  if scenario=='shared-check-unrelated-requirement':g['checks'][40]['requirement_ids'].append('FR-076')
  (r/'.wigtn/workgraph.json').write_text(json.dumps(g));before=tree(r)
  p=subprocess.run([sys.executable,'-B',str(CLI),'--root',str(r),'--json','inspect','--task','TASK-041'],text=True,capture_output=True)
  d=json.loads(p.stdout);assert tree(r)==before
  if scenario in ['invalid-project','invalid-evidence']:assert p.returncode==1 and not d['valid_artifacts'] and not d['next_tasks']
  if scenario=='unrelated-invalid-task':assert p.returncode==2 and 'error' in d
  if scenario=='missing-selected-source':assert p.returncode==1 and not d['next_tasks'] and d['source_drift'][0]['actual']=='missing'
  if scenario=='missing-unrelated-source':assert p.returncode==1 and d['source_drift'][0]['path']=='docs/requirement-076.md' and d['next_tasks']
  if scenario=='shared-check-unrelated-requirement':assert p.returncode==0 and 'FR-076' in [x['id'] for x in d['requirements']] and 'SRC-076' in [x['id'] for x in d['sources']]
  results.append({'scenario':scenario,'pass':True,'exit_code':p.returncode,'unchanged':True})
(R/'adversarial-results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
