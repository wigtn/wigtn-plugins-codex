"""Reject malformed project context before generating or saving a plan."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(os.environ.get('WIGTN_TEST_ROOT',str(Path(__file__).resolve().parents[1])))
CLI=ROOT/'plugins/wigtn-plugins-with-codex/scripts/wigtn.py'
class ProjectGuard(unittest.TestCase):
 def test_invalid_context_preserves_graph_for_preview_and_apply(self):
  for field,value in [('verification_commands','pytest'),('verification_commands',17),('protected_paths','src.py'),('prd_profile','invalid')]:
   for apply in [False,True]:
    with self.subTest(field=field,value=value,apply=apply),tempfile.TemporaryDirectory() as t:
     root=Path(t);(root/'req.md').write_text('REQ-A: Compute A.\n')
     def run(*a):return subprocess.run([sys.executable,'-B',str(CLI),'--root',str(root),'--json',*a],text=True,capture_output=True)
     self.assertEqual(run('init','--apply').returncode,0);self.assertEqual(run('import','req.md','--apply').returncode,0)
     p=root/'.wigtn/project.json';d=json.loads(p.read_text());d[field]=value;p.write_text(json.dumps(d));graph=root/'.wigtn/workgraph.json';before=graph.read_bytes()
     out=run('plan',*(['--apply'] if apply else []));self.assertEqual(out.returncode,2,out.stdout+out.stderr);self.assertIn('invalid project context',json.loads(out.stdout)['error']);self.assertEqual(graph.read_bytes(),before)
if __name__=='__main__':unittest.main(verbosity=2)
