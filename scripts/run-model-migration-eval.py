#!/usr/bin/env python3
"""Snapshot-based, sequential pilot. No calls without --execute; no billing estimates."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import time
import sys

from migration_cases import PROMPTS as CASES, RUBRIC, ACTIVATION, SUITES
from migration_evidence import seal, seal_run

CODE_CASES = {'ordinary', 'delivery'}
ORACLE = '''import importlib.util, sys
spec = importlib.util.spec_from_file_location('evaluated_scores', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for values in ([], [1], [3, 1, 2], [2, 2, -1], [5, 0, -3, 5]):
    original = values.copy()
    result = module.sorted_scores(values)
    assert result == sorted(original), (original, result)
    assert values == original, (original, values)
print('Independent oracle: PASS (5 inputs, ordering and nonmutation)')
'''

def check_implementation(work, log):
    return invoke([sys.executable, '-I', '-B', '-c', ORACLE, str(work/'scores.py')],
                  os.environ.copy(), log.parent, log, timeout=30)

def snapshot_marketplace(source, destination):
    # Copy only the evaluated distributable, not reports, other plugins or repository files.
    catalog = json.loads((source/'.agents/plugins/marketplace.json').read_text())
    catalog['plugins'] = [p for p in catalog['plugins'] if p['name']=='wigtn-plugins-with-codex']
    if len(catalog['plugins']) != 1:
        raise ValueError('expected one WIGTN core plugin')
    plugin = source/'plugins/wigtn-plugins-with-codex'
    if any(p.is_symlink() for p in plugin.rglob('*')):
        raise ValueError('plugin snapshot must not follow symlinks')
    catalog['plugins'][0]['source'] = {'source':'local','path':'./plugins/wigtn-plugins-with-codex'}
    target = destination/'.agents/plugins/marketplace.json'
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(catalog, indent=2)+'\n')
    shutil.copytree(plugin, destination/'plugins/wigtn-plugins-with-codex',
                    ignore=shutil.ignore_patterns('__pycache__','.DS_Store'))

def digest_tree(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name != '.DS_Store'}

def invoke(command, env, cwd, log, timeout=240, stdin=None):
    start = time.monotonic()
    with log.open('w') as out, log.with_suffix('.stderr').open('w') as err:
        try:
            result = subprocess.run(command, env=env, cwd=cwd, input=stdin, text=True,
                                    stdout=out, stderr=err, timeout=timeout)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
    return {'exit_code': code, 'duration_seconds': round(time.monotonic()-start, 3)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--model', default='gpt-6-astra')
    ap.add_argument('--effort', default='medium', choices=['low','medium','high','xhigh','max'])
    ap.add_argument('--repeat', type=int, default=2)
    ap.add_argument('--suite', choices=list(SUITES), default='smoke',
                    help='smoke: 24; targeted/contracts: 30 calls at repeat=2; prints plan unless --execute')
    ap.add_argument('--seed', type=int, default=907)
    ap.add_argument('--codex', default=os.environ.get('CODEX_BIN') or shutil.which('codex') or '/Applications/ChatGPT.app/Contents/Resources/codex')
    ap.add_argument('--execute', action='store_true')
    args=ap.parse_args()
    args.baseline=args.baseline.resolve()
    args.candidate=args.candidate.resolve()
    args.root=args.root.resolve()
    if args.repeat < 1: ap.error('--repeat must be positive')
    if args.root.exists(): ap.error('--root must be fresh')
    for source in (args.baseline,args.candidate):
        if not (source/'.agents/plugins/marketplace.json').is_file(): ap.error(f'not a marketplace: {source}')
        if source.resolve() in args.root.resolve().parents: ap.error('output must be outside source')
    case_ids = SUITES[args.suite]
    schedule=[]; rng=random.Random(args.seed)
    for rep in range(1,args.repeat+1):
        for case in case_ids:
            arms=['bare','baseline','candidate']; rng.shuffle(arms)
            for arm in arms: schedule.append({'arm':arm,'case':case,'repeat':rep})
    plan={'model':args.model,'effort':args.effort,'seed':args.seed,'calls':len(schedule),
          'suite':args.suite,'schedule':schedule,'prompts':{c:CASES[c] for c in case_ids},
          'treatment':'delivery adds explicit verified-delivery invocation to baseline/candidate only',
          'schema_version':2,
          'review_rubric':{c:RUBRIC[c] for c in case_ids},
          'activation_required':{c:ACTIVATION[c] for c in case_ids if c in ACTIVATION},
          'pricing':'not estimated; CLI usage is not a bill'}
    if not args.execute:
        print(json.dumps(plan,ensure_ascii=False,indent=2));return
    auth=Path(os.environ.get('CODEX_AUTH_FILE',str(Path.home()/'.codex/auth.json')))
    if not auth.is_file(): ap.error('Codex authentication unavailable')
    args.root.mkdir(parents=True)
    plan['cli']=subprocess.check_output([args.codex,'--version'],text=True).strip()
    plan['created_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    evaluator=args.root/'evaluator';evaluator.mkdir()
    for name in ['run-model-migration-eval.py','score-model-migration-eval.py','codex_usage.py','migration_evidence.py','migration_cases.py']:
        shutil.copy2(Path(__file__).with_name(name),evaluator/name)
    plan['evaluator_hashes']=digest_tree(evaluator)
    plan['python']=sys.version
    plan['snapshots']={}
    for arm,src in [('baseline',args.baseline),('candidate',args.candidate)]:
        dest=args.root/'snapshots'/arm
        snapshot_marketplace(src,dest)
        plan['snapshots'][arm]=digest_tree(dest)
    (args.root/'protocol.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    seal(args.root, ['protocol.json', 'evaluator', 'snapshots'], 'input-manifest.json')
    common=[args.codex,'--disable','remote_plugin','--disable','apps']
    envs={}
    for arm in ['bare','baseline','candidate']:
        home=args.root/'homes'/arm;home.mkdir(parents=True)
        (home/'auth.json').symlink_to(auth.resolve())
        envs[arm]={**os.environ,'CODEX_HOME':str(home)}
        if arm!='bare':
            for label,cmd in [('marketplace',['plugin','marketplace','add',str(args.root/'snapshots'/arm),'--json']),
                              ('plugin',['plugin','add','wigtn-plugins-with-codex@wigtn','--json'])]:
                meta=invoke(common+cmd,envs[arm],args.root,args.root/f'{arm}-{label}.json')
                if meta['exit_code']: raise SystemExit(f'{arm} {label} failed: {meta}')
        probe=args.root/'probe'/arm;probe.mkdir(parents=True)
        log=args.root/f'{arm}-prompt.json'
        meta=invoke(common+['-C',str(probe),'debug','prompt-input','Write a PRD'],envs[arm],probe,log)
        exposed='wigtn-plugins-with-codex:product-spec' in log.read_text()
        if meta['exit_code'] or exposed != (arm!='bare'): raise SystemExit(f'catalog isolation failed: {arm}')
    for order,item in enumerate(schedule,1):
        arm,case,rep=item['arm'],item['case'],item['repeat']
        run=args.root/'runs'/f'{order:03}-{arm}-{case}-{rep}';work=run/'work';work.mkdir(parents=True)
        if case in CODE_CASES:
            (work/'scores.py').write_text('def sorted_scores(scores):\n    scores.sort()\n    return scores\n')
            (work/'test_scores.py').write_text('import unittest\nfrom scores import sorted_scores\nclass Scores(unittest.TestCase):\n    def test_sort(self):\n        self.assertEqual(sorted_scores([3,1,2]),[1,2,3])\n    def test_preserve(self):\n        values=[3,1,2]; sorted_scores(values); self.assertEqual(values,[3,1,2])\n')
            (work/'notes.txt').write_text('User draft: preserve this file.\n')
        before=digest_tree(work)
        if case in CODE_CASES:
            precheck=check_implementation(work,run/'oracle-before.txt')
            if precheck['exit_code'] != 1:
                raise SystemExit('fault fixture must fail the independent oracle before execution')
        prompt=CASES[case]
        if case=='delivery' and arm!='bare':
            prompt='Use $wigtn-plugins-with-codex:verified-delivery. '+prompt
        (run/'prompt.txt').write_text(prompt)
        meta=invoke(common+['-a','never','-m',args.model,'-c',f'model_reasoning_effort="{args.effort}"',
                           '-s','workspace-write' if case in CODE_CASES else 'read-only','-C',str(work),
                           'exec','--ephemeral','--ignore-rules','--skip-git-repo-check','--json',
                           '-o',str(run/'answer.md'),'-'],envs[arm],work,run/'events.jsonl',stdin=prompt)
        meta.update(item);meta.update(order=order,model=args.model,effort=args.effort)
        meta['before_hashes']=before
        if case in CODE_CASES:
            check=check_implementation(work,run/'oracle.txt')
            meta['oracle_before']=precheck
            after=digest_tree(work)
            meta['after_hashes']=after
            meta['unexpected_changes']=sorted(p for p in set(before)|set(after)
                                               if before.get(p)!=after.get(p) and p!='scores.py')
            meta['oracle']=check
            meta['draft_preserved']=(work/'notes.txt').is_file() and (work/'notes.txt').read_text()=='User draft: preserve this file.\n'
            meta['unsolicited_state']=any((work/p).exists() for p in ['.wigtn','PRD.md','docs/PRD.md'])
        (run/'meta.json').write_text(json.dumps(meta,indent=2)+'\n')
        seal_run(run)
        print(f'{order}/{len(schedule)} {arm}/{case} exit={meta["exit_code"]} {meta["duration_seconds"]}s',flush=True)
        if meta['exit_code']:
            # Retain failed run; stop before wasting the rest of the model budget.
            raise SystemExit('Incomplete pilot: inspect retained failure before starting a new run')
    print(args.root,flush=True)
if __name__=='__main__': main()
