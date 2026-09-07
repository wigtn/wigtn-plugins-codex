"""Regression for imports invoked outside the selected repository root."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(os.environ.get('WIGTN_TEST_ROOT',str(Path(__file__).resolve().parents[1])))
CLI=ROOT/'plugins/wigtn-plugins-with-codex/scripts/wigtn.py'
class ImportRoot(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.repo=self.base/'repo';self.cwd=self.base/'elsewhere';self.repo.mkdir();self.cwd.mkdir()
  (self.repo/'requirements.md').write_text('REQ-RIGHT: Use the selected repository.\n');(self.cwd/'requirements.md').write_text('REQ-WRONG: Do not import the working directory.\n')
  self.assertEqual(self.runcli('init','--apply').returncode,0)
 def tearDown(self):self.tmp.cleanup()
 def runcli(self,*args):return subprocess.run([sys.executable,'-B',str(CLI),'--root',str(self.repo),'--json',*args],cwd=self.cwd,text=True,capture_output=True)
 def graph(self):return (self.repo/'.wigtn/workgraph.json').read_bytes()
 def test_relative_source_uses_root_and_preserves_dry_run(self):
  before=self.graph();p=self.runcli('import','requirements.md');self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertEqual(before,self.graph())
  p=self.runcli('import','requirements.md','--apply');self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertEqual([r['id'] for r in json.loads(self.graph())['requirements']],['REQ-RIGHT'])
 def test_absolute_inside_allowed_outside_rejected_without_mutation(self):
  p=self.runcli('import',str(self.repo/'requirements.md'),'--apply');self.assertEqual(p.returncode,0,p.stdout+p.stderr);before=self.graph()
  p=self.runcli('import',str(self.cwd/'requirements.md'),'--apply');self.assertEqual(p.returncode,2);self.assertEqual(before,self.graph())
 def test_symlink_escape_rejected_without_mutation(self):
  (self.repo/'escape.md').symlink_to(self.cwd/'requirements.md');before=self.graph();p=self.runcli('import','escape.md','--apply');self.assertEqual(p.returncode,2);self.assertEqual(before,self.graph())
if __name__=='__main__':unittest.main(verbosity=2)
