import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from codex_usage import read_events,api_equivalent_cost
class UsageMissing(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'events.jsonl'
 def tearDown(self):self.tmp.cleanup()
 def write(self,*values):self.path.write_text('\n'.join(json.dumps({'type':'turn.completed','usage':v}) for v in values)+'\n')
 def test_absent_optional_is_unknown(self):
  self.write({'input_tokens':100,'output_tokens':10});u=read_events(self.path)
  for f in ['cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens','visible_output_tokens','uncached_input_tokens']:self.assertIsNone(u[f],f)
 def test_explicit_zero_is_known(self):
  self.write({'input_tokens':100,'output_tokens':10,'cached_input_tokens':0,'cache_write_input_tokens':0,'reasoning_output_tokens':0});u=read_events(self.path);self.assertEqual(u['visible_output_tokens'],10);self.assertEqual(u['uncached_input_tokens'],100)
 def test_missing_one_turn_propagates(self):
  full={'input_tokens':100,'output_tokens':10,'cached_input_tokens':20,'cache_write_input_tokens':0,'reasoning_output_tokens':2}
  for values in [(full,{'input_tokens':100,'output_tokens':10}),({'input_tokens':100,'output_tokens':10},full)]:
   self.write(*values);u=read_events(self.path);self.assertEqual(u['input_tokens'],200);self.assertIsNone(u['reasoning_output_tokens']);self.assertIsNone(u['uncached_input_tokens'])
 def test_invalid_required_counters_rejected(self):
  for value in [None,-1,True,'100',1.5]:
   with self.subTest(value=value):
    self.write({'input_tokens':value,'output_tokens':10})
    with self.assertRaises(ValueError):read_events(self.path)
 def test_invalid_optional_counters_rejected(self):
  for value in [-1,True,'10',1.5]:
   with self.subTest(value=value):
    self.write({'input_tokens':100,'output_tokens':10,'reasoning_output_tokens':value})
    with self.assertRaises(ValueError):read_events(self.path)
 def test_impossible_breakdown_rejected(self):
  for extras in [{'reasoning_output_tokens':11},{'cached_input_tokens':101},{'cached_input_tokens':60,'cache_write_input_tokens':50}]:
   self.write({'input_tokens':100,'output_tokens':10,**extras})
   with self.assertRaises(ValueError):read_events(self.path)
 def test_missing_cache_prevents_cache_adjusted_price(self):
  self.write({'input_tokens':100,'output_tokens':10});u=read_events(self.path)
  self.assertIsNone(api_equivalent_cost(u,input_per_million=4,cached_input_per_million=.4,cache_write_per_million=5,output_per_million=20))
 def test_cli_has_no_assumed_prices(self):
  self.write({'input_tokens':100,'output_tokens':10});c=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/codex_usage.py'),str(self.path)],capture_output=True,text=True);self.assertEqual(c.returncode,0,c.stderr);self.assertIsNone(json.loads(c.stdout)['api_equivalent_usd'])
 def test_summary_preserves_unknown_without_crashing(self):
  root=Path(self.tmp.name);p=root/'runs/candidate/acceptance.1.events.jsonl';p.parent.mkdir(parents=True);self.write({'input_tokens':100,'output_tokens':10});p.write_bytes(self.path.read_bytes())
  c=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/summarize-token-efficiency.py'),str(root)],capture_output=True,text=True);self.assertEqual(c.returncode,0,c.stderr);d=json.loads((root/'TOKEN-EFFICIENCY.json').read_text());self.assertIsNone(d['arms']['candidate']['reasoning_output_tokens']);self.assertIn('unknown',(root/'TOKEN-EFFICIENCY.md').read_text())
if __name__=='__main__':unittest.main(verbosity=2)
