"""Interleave two real CLI writers; assert no stale-revision acceptance or lost updates."""
from pathlib import Path
import json,os,subprocess,sys,tempfile,time,unittest
ROOT=Path(os.environ.get('WIGTN_TEST_ROOT',str(Path(__file__).resolve().parents[1])))
CLI=ROOT/'plugins/wigtn-plugins-with-codex/scripts/wigtn.py'
class Concurrency(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.root=self.base/'repo';self.root.mkdir();(self.root/'requirements.md').write_text('REQ-A: Save A.\nREQ-B: Save B.\n')
  for args in [('init','--apply'),('import','requirements.md','--apply'),('plan','--apply')]:self.assertEqual(self.runcli(*args).returncode,0)
  self.initial=self.graph();self.task=self.initial['tasks'][0]['id']
 def tearDown(self):self.tmp.cleanup()
 def graph(self):return json.loads((self.root/'.wigtn/workgraph.json').read_text())
 def runcli(self,*args):return subprocess.run([sys.executable,'-B',str(CLI),'--root',str(self.root),'--json',*args],text=True,capture_output=True,timeout=15)
 def waitfor(self,p):
  until=time.monotonic()+8
  while not p.exists() and time.monotonic()<until:time.sleep(.01)
  self.assertTrue(p.exists(),str(p))
 def writer(self,name,paused,args):
  # Wrapper pauses after the actual disk read, without changing the graph or implementation logic.
  wrapper=self.base/(name+'.py');wrapper.write_text('''import importlib.util,sys,time\nfrom pathlib import Path\ncli=Path(sys.argv[1]);base=Path(sys.argv[2]);name=sys.argv[3];paused=sys.argv[4]=='yes'\nsys.path.insert(0,str(cli.parent));s=importlib.util.spec_from_file_location('cli_under_test',cli);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nread=m.require_graph\ndef hook(root):\n g=read(root);(base/(name+'.read')).write_text('read')\n if paused:\n  until=time.monotonic()+10\n  while not (base/(name+'.release')).exists():\n   if time.monotonic()>until:raise ValueError('test barrier timed out')\n   time.sleep(.01)\n return g\nm.require_graph=hook\n(base/(name+'.start')).write_text('start')\nsys.argv=[str(cli)]+sys.argv[5:];raise SystemExit(m.main())\n''')
  return subprocess.Popen([sys.executable,'-B',str(wrapper),str(CLI),str(self.base),name,'yes' if paused else 'no','--root',str(self.root),'--json',*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 def pair(self,expected):
  rev=['--expected-revision',str(self.initial['revision'])] if expected else []
  a=self.writer('a',True,['task','update',self.task,'--title','Writer A',*rev,'--apply']);b=None
  try:
   self.waitfor(self.base/'a.read');b=self.writer('b',False,['task','update',self.task,'--risk','high',*rev,'--apply']);self.waitfor(self.base/'b.start')
   # Hold A while B attempts the same transaction; record actual observed order.
   until=time.monotonic()+.4
   while b.poll() is None and not (self.base/'b.read').exists() and time.monotonic()<until:time.sleep(.01)
   (self.base/'a.release').write_text('release');ao,ae=a.communicate(timeout=12);bo,be=b.communicate(timeout=12)
   self.assertEqual(a.returncode,0,ao+ae)
   if expected:self.assertEqual(b.returncode,2,bo+be);self.assertIn('revision conflict',bo)
   else:self.assertEqual(b.returncode,0,bo+be)
   g=self.graph();t=next(t for t in g['tasks'] if t['id']==self.task);self.assertEqual(t['title'],'Writer A')
   self.assertEqual(t['risk'],self.initial['tasks'][0]['risk'] if expected else 'high')
   self.assertEqual(g['revision'],self.initial['revision']+(1 if expected else 2))
  finally:
   for p in [a,b]:
    if p is not None and p.poll() is None:p.kill();p.communicate()
 def test_same_revision_second_writer_rejected(self):self.pair(True)
 def test_no_revision_second_writer_merges_latest(self):self.pair(False)
 def test_dry_run_does_not_create_lock_or_change_state(self):
  lock=self.root/'.wigtn/.write.lock'
  if lock.exists():lock.unlink() # no live writers in this test
  before={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  self.assertEqual(self.runcli('task','update',self.task,'--title','Preview').returncode,0)
  self.assertEqual(before,{str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
 def test_killed_writer_releases_lock(self):
  a=self.writer('killed',True,['task','update',self.task,'--title','Never saved','--apply'])
  try:self.waitfor(self.base/'killed.read')
  finally:a.kill();a.communicate()
  p=self.runcli('task','update',self.task,'--title','Recovered','--apply');self.assertEqual(p.returncode,0,p.stdout+p.stderr)
  self.assertEqual(self.graph()['tasks'][0]['title'],'Recovered')
if __name__=='__main__':unittest.main(verbosity=2)
