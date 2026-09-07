import hashlib,importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=Path(os.environ.get('WIGTN_TEST_ROOT',str(R)))/'plugins/wigtn-plugins-with-codex';CLI=P/'scripts/wigtn.py'
spec=importlib.util.spec_from_file_location('fixture',R/'scripts/check-workgraph-contract.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Inspect(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.r=Path(self.tmp.name);(self.r/'docs').mkdir();(self.r/'.wigtn').mkdir();(self.r/'docs/prd.md').write_text('Original requirement\n');g=m.valid_graph();g['sources'][0]['sha256']=hashlib.sha256((self.r/'docs/prd.md').read_bytes()).hexdigest()
  for x in g['requirements']:x['source_sha256']=g['sources'][0]['sha256']
  (self.r/'.wigtn/workgraph.json').write_text(json.dumps(g));(self.r/'.wigtn/evidence.json').write_bytes((R/'tests/evidence/valid-acceptance.json').read_bytes())
  self.project={'schema_version':'1.0','requirement_sources':['docs/prd.md'],'verification_commands':['touch NEVER_EXECUTE'],'protected_paths':['.git'],'prd_profile':'auto','evidence_path':'.wigtn/evidence.json'};self.saveproject()
 def tearDown(self):self.tmp.cleanup()
 def saveproject(self):(self.r/'.wigtn/project.json').write_text(json.dumps(self.project))
 def runinspect(self):
  before={str(p.relative_to(self.r)):p.read_bytes() for p in self.r.rglob('*') if p.is_file()}
  out=subprocess.run([sys.executable,'-B',str(CLI),'--root',str(self.r),'--json','inspect'],text=True,capture_output=True)
  self.assertEqual(before,{str(p.relative_to(self.r)):p.read_bytes() for p in self.r.rglob('*') if p.is_file()});return out.returncode,json.loads(out.stdout)
 def test_fresh_readonly_and_no_saved_command_execution(self):
  code,d=self.runinspect();self.assertEqual(code,0,d);self.assertTrue(d['valid_artifacts']);self.assertTrue(d['fresh']);self.assertEqual([t['id'] for t in d['next_tasks']],['TASK-SCREEN']);self.assertFalse((self.r/'NEVER_EXECUTE').exists())
 def test_drift_propagates_to_dependent_tasks_without_mutation(self):
  (self.r/'docs/prd.md').write_text('Changed requirement\n');code,d=self.runinspect();self.assertEqual(code,1,d);self.assertFalse(d['fresh']);self.assertTrue(all(t['status']=='stale' for t in d['tasks']));self.assertEqual(d['next_tasks'],[])
 def test_missing_source_has_explicit_drift(self):
  (self.r/'docs/prd.md').unlink();code,d=self.runinspect();self.assertEqual(code,1);self.assertEqual(d['source_drift'][0]['actual'],'missing')
 def test_invalid_project_withholds_eligible_tasks(self):
  self.project['verification_commands']=7;self.saveproject();code,d=self.runinspect();self.assertEqual(code,1);self.assertFalse(d['validations']['project']['valid']);self.assertEqual(d['next_tasks'],[]);self.assertEqual(d['summary']['next_task_ids'],[])
 def test_corrupt_evidence_withholds_eligible_tasks(self):
  (self.r/'.wigtn/evidence.json').write_text('{');code,d=self.runinspect();self.assertEqual(code,1);self.assertFalse(d['validations']['evidence']['valid']);self.assertEqual(d['next_tasks'],[])
 def test_invalid_graph_fails_closed(self):
  (self.r/'.wigtn/workgraph.json').write_text('{}');code,d=self.runinspect();self.assertEqual(code,2);self.assertIn('error',d);self.assertNotIn('next_tasks',d)
if __name__=='__main__':unittest.main(verbosity=2)
