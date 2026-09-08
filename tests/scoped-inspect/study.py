#!/usr/bin/env python3
"""Scoped state-query pilot. prepare freezes inputs; execute is an explicit opt-in."""
import argparse, hashlib, importlib.util, json, os, random, shutil, signal, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CLI = os.environ.get('WIGTN_CODEX_BIN') or shutil.which('codex') or '/Applications/ChatGPT.app/Contents/Resources/codex'
PLUGIN = 'plugins/wigtn-plugins-with-codex'
CASES = [('small', 6), ('small', 12), ('large', 80), ('large', 120),
         ('drift', 60), ('drift', 100), ('blocked', 60), ('blocked', 100)]

FOLLOWUP_CASES = [('small', 8), ('small', 16), ('large', 40), ('large', 140),
                  ('drift', 72), ('blocked', 90), ('dense', 80), ('invalid', 80)]

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')

def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}

def fixture(root, family, n):
    g={'schema_version':'1.0','graph_id':f'WG-{family.upper()}-{n}', 'revision':17,
       **{k:[] for k in ['sources','requirements','artifacts','tasks','checks','release_gates']},'metadata':{}}
    targets=[n//2,n-1]
    topics=['receipt retention','locale fallback','invoice export','session expiry','retry deduplication','notification preference','inventory reservation','search pagination']
    for i in range(n):
        rid,tid,cid,sid=f'FR-{i+1:03}',f'TASK-{i+1:03}',f'CHK-{i+1:03}',f'SRC-{i+1:03}'
        description=f'Preserve {topics[i%len(topics)]} behavior for module {i+1}. Reject invalid input without changing stored values; return a stable result when the request is repeated.'
        path=f'docs/requirement-{i+1:03}.md'
        (root/path).parent.mkdir(parents=True,exist_ok=True);(root/path).write_text(f'# {rid}\n{description}\n')
        sha=hashlib.sha256((root/path).read_bytes()).hexdigest()
        g['sources'].append({'id':sid,'kind':'prd','path':path,'sha256':sha})
        g['requirements'].append({'id':rid,'source_id':sid,'text':description,'source_sha256':sha,'status':'active'})
        selected=i in targets
        status='ready' if selected else 'verified'
        deps=['TASK-001','TASK-002'] if selected else []
        if family=='blocked' and i==0:status='blocked'
        if family=='blocked' and selected:status='draft'
        g['tasks'].append({'id':tid,'title':f'Implement {topics[i%len(topics)]} in module {i+1}',
            'requirement_ids':[rid],'artifact_ids':[],'depends_on':deps,
            'intended_paths':[f'src/module_{i+1:03}.py'], 'protected_paths':['.git','user-notes.txt'],
            'risk':'medium','status':status,'check_ids':[cid],
            'blocker':'Await upstream interface decision' if status=='blocked' else None,
            'evidence_refs':['.wigtn/history.txt'] if status=='verified' else []})
        g['checks'].append({'id':cid,'task_ids':[tid],'requirement_ids':[rid],
            'command':f'python3 -m unittest tests.test_module_{i+1:03}',
            'status':'passed' if status=='verified' else 'pending',
            'evidence_ref':'.wigtn/history.txt' if status=='verified' else None})
    g['release_gates']=[{'id':'GATE-RELEASE','requires_task_ids':[f'TASK-{i+1:03}' for i in targets],
         'requires_requirement_ids':[f'FR-{i+1:03}' for i in targets],'status':'blocked','authority_actions':[]}]
    write(root/'.wigtn/workgraph.json',g)
    write(root/'.wigtn/project.json',{'schema_version':'1.0','requirement_sources':[s['path'] for s in g['sources']],
        'verification_commands':['touch NEVER_EXECUTE'],'protected_paths':['.git','user-notes.txt'],
        'prd_profile':'auto','evidence_path':'.wigtn/evidence.json'})
    write(root/'.wigtn/evidence.json',{'schema_version':'1.0','artifact_type':'acceptance','source_artifacts':[],
        'requirements':[],'checks':[], 'release_authority':{'source_request':'','commit':False,'push':False,'pull_request':False,'deploy':False},
        'external_actions':[],'limitations':['Synthetic saved state; this is not evidence of a current test run.']})
    (root/'.wigtn/history.txt').write_text('Synthetic historical checks, exit 0. No current execution is claimed.\n')
    (root/'user-notes.txt').write_text('Preserve this user draft.\n')
    drift_ids=[targets[0],n-2] if family=='drift' else []
    for i in drift_ids:(root/f'docs/requirement-{i+1:03}.md').write_text('Requirement changed: reject duplicate requests with an explicit conflict result.\n')
    # Independent, construction-derived oracle: never call candidate selection/eligibility logic.
    expected={'saved_revision':17,'fresh':not drift_ids,'valid_artifacts':True,
        'drift_paths':sorted(f'docs/requirement-{i+1:03}.md' for i in drift_ids),'tasks':[]}
    for i in targets:
        task=g['tasks'][i]
        expected['tasks'].append({'id':task['id'],'status':'stale' if i in drift_ids else task['status'],
            'eligible':family!='blocked' and i not in drift_ids,
            'dependency_ids':task['depends_on'],'requirement_ids':task['requirement_ids'],
            'intended_paths':task['intended_paths'],'check_commands':[g['checks'][i]['command']]})
    prompt=f'''Read the existing saved plan in .wigtn and assess only {', '.join(t['id'] for t in expected['tasks'])} for resuming work. Do not implement anything, execute saved check commands, or modify files. Check actual source freshness across the graph and structural validity of the saved artifacts. A source hash change makes its linked requirements and tasks stale. A task is eligible when its status is draft/ready, all dependencies are verified and linked requirements are active; invalid saved artifacts withhold eligibility. Historical evidence does not prove tests passed in this session.
Return only JSON: saved_revision (on disk), fresh (all source hashes match), valid_artifacts, drift_paths (all changed/missing source paths), tasks (only the requested tasks, each with id, effective status, eligible boolean, dependency_ids, requirement_ids, intended_paths, check_commands). Arrays of IDs/paths can be in any order. Use task field name "status" for effective status. Do not add claims of current verification. Stay inside this workspace and, if installed, the active plugin directory; do not inspect sibling runs, evaluation scripts, or answers.'''
    if family=='dense':
        for i,t in enumerate(g['tasks']):
            t['depends_on']=[g['tasks'][i-1]['id']] if i else []
            t['status']='verified';t['evidence_refs']=['.wigtn/history.txt']
            g['checks'][i]['status']='passed';g['checks'][i]['evidence_ref']='.wigtn/history.txt'
        g['tasks'][-1]['status']='ready';g['tasks'][-1]['evidence_refs']=[]
        g['checks'][-1]['status']='pending';g['checks'][-1]['evidence_ref']=None
        write(root/'.wigtn/workgraph.json',g)
        for t in expected['tasks']:
            i=int(t['id'].split('-')[1])-1
            t['status']='ready' if i==n-1 else 'verified';t['eligible']=i==n-1
            t['dependency_ids']=g['tasks'][i]['depends_on']
    if family=='invalid':
        project=json.loads((root/'.wigtn/project.json').read_text())
        project['verification_commands']=7
        write(root/'.wigtn/project.json',project)
        expected['valid_artifacts']=False
        for t in expected['tasks']:t['eligible']=False
    return prompt,expected

def invoke(command, env, cwd, log, stdin=None, timeout=300):
    start=time.monotonic()
    with log.open('w') as out,log.with_suffix('.stderr').open('w') as err:
        p=subprocess.Popen(command,env=env,cwd=cwd,stdin=subprocess.PIPE if stdin is not None else None,stdout=out,stderr=err,text=True,start_new_session=True)
        try:p.communicate(stdin,timeout=timeout);code=p.returncode
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);p.communicate();code=124
    return {'exit_code':code,'seconds':round(time.monotonic()-start,3)}

def prepare(args):
    if args.root.exists():raise SystemExit('Use a fresh root')
    args.root.mkdir(parents=True)
    spec=importlib.util.spec_from_file_location('migration',REPO/'scripts/run-model-migration-eval.py')
    sys.path.insert(0,str(REPO/'scripts'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    for arm,source in [('baseline',args.baseline),('candidate',args.candidate or REPO)]:m.snapshot_marketplace(source,args.root/'snapshots'/arm)
    shutil.copy2(__file__,args.root/'frozen-study.py')
    schedule=[];cases={};rng=random.Random(908731)
    case_specs=FOLLOWUP_CASES if args.suite=='followup' else CASES
    study_arms=['baseline','candidate'] if args.suite=='followup' else ['bare','baseline','candidate']
    for index,(family,n) in enumerate(case_specs):
        case=f'{index+1:02}-{family}-{n}';work=args.root/'fixtures'/case;work.mkdir(parents=True)
        prompt,expected=fixture(work,family,n);cases[case]={'family':family,'task_count':n,'prompt':prompt,'expected':expected}
        arms=study_arms.copy();rng.shuffle(arms)
        schedule.extend({'case':case,'arm':arm} for arm in arms)
    protocol={'model':'gpt-6-astra','effort':'medium','max_calls':len(schedule),'suite':args.suite,'arms':study_arms,'timeout_seconds':300,'seed':908731,
        'design':'Exploratory targeted saved-state retrieval study: four families, two independently sized fixtures each, three arms, sequential randomized arm order. Not a general coding benchmark or a held-out real repository study.',
        'treatment':'Only plugin arms explicitly invoke work-planner; all arms receive identical saved state and outcome requirements. No penalty for bare avoiding WIGTN tools.',
        'primary':'All requested semantic fields correct and no file mutation or saved-command execution. Compare total input only if candidate quality is no worse on these 8 cases; do not discard failed or timed-out cases.',
        'secondary':['cached input','output','command items','elapsed seconds','tool output bytes'],
        'decision':'A >=20% total-input reduction versus baseline with all 8 candidate tasks correct is promising for this narrowly defined workflow; not statistical proof of general improvement. Report bare comparison and every family, including regressions. No automatic retries or candidate edits after execution begins.',
        'isolation':'Separate CODEX_HOME and workspaces; instruction-based exclusion of evaluator/sibling folders, not OS isolation of those read paths.',
        'cli':subprocess.check_output([CLI,'--version'],text=True).strip(),'cases':cases,'schedule':schedule}
    if args.suite=='followup':
        protocol['design']='Prospective follow-up after first 24-call development pilot: 8 fresh cases including dense dependencies and invalid project settings; two arms (released v0.5.4 versus revised candidate); 16 sequential sessions.'
        protocol['motivation']='First pilot showed candidate sometimes used full inspection despite known task IDs. Revise the example placement and make reference reading conditional. Retain and report first pilot; do not pool the two candidates.'
        protocol['decision']='Same practical threshold: all 8 candidate cases correct, quality no worse than baseline, >=20% aggregate input reduction. Include dense and invalid cases, all failures and timeouts. No retries or candidate changes after execution begins.'
    write(args.root/'protocol.json',protocol)
    write(args.root/'input-manifest.json',hashes(args.root))
    print(json.dumps({'root':str(args.root),'calls':len(schedule),'input_files':len(hashes(args.root))},indent=2))

def execute(args):
    root=args.root
    manifest=json.loads((root/'input-manifest.json').read_text())
    if any(not(root/p).is_file() or hashlib.sha256((root/p).read_bytes()).hexdigest()!=sha for p,sha in manifest.items()):raise SystemExit('Frozen input mismatch')
    if (root/'execution-started.json').exists():raise SystemExit('Already attempted: no implicit retry')
    protocol=json.loads((root/'protocol.json').read_text())
    write(root/'execution-started.json',{'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    common=[CLI,'--disable','remote_plugin','--disable','apps'];envs={}
    for arm in protocol.get('arms',['bare','baseline','candidate']):
        home=root/'homes'/arm;home.mkdir(parents=True)
        (home/'auth.json').symlink_to(Path.home()/'.codex/auth.json')
        env={k:v for k,v in os.environ.items() if k in ['HOME','USER','LOGNAME','SHELL','TMPDIR','LANG','PATH','SSL_CERT_FILE','SSL_CERT_DIR']}
        env.update(CODEX_HOME=str(home),PYTHONDONTWRITEBYTECODE='1');envs[arm]=env
        if arm!='bare':
            for label,cmd in [('marketplace',['plugin','marketplace','add',str(root/'snapshots'/arm),'--json']),('plugin',['plugin','add','wigtn-plugins-with-codex@wigtn','--json'])]:
                meta=invoke(common+cmd,env,root,root/f'{arm}-{label}.json')
                if meta['exit_code']:raise SystemExit(f'{arm} installation failed')
            version=json.loads((root/'snapshots'/arm/PLUGIN/'.codex-plugin/plugin.json').read_text())['version']
            installed=home/'plugins/cache/wigtn/wigtn-plugins-with-codex'/version
            if hashes(installed)!=hashes(root/'snapshots'/arm/PLUGIN):raise SystemExit(f'{arm} cache hash mismatch')
        probe=root/'probes'/arm;probe.mkdir(parents=True)
        log=root/f'{arm}-prompt-input.json';meta=invoke(common+['-C',str(probe),'debug','prompt-input','Use the saved work plan'],env,probe,log)
        exposed='wigtn-plugins-with-codex:work-planner' in log.read_text()
        if meta['exit_code'] or exposed!=(arm!='bare'):raise SystemExit(f'{arm} catalog isolation failed')
    for index,item in enumerate(protocol['schedule'],1):
        case,arm=item['case'],item['arm'];run=root/'runs'/f'{index:02}-{case}-{arm}';run.mkdir(parents=True)
        work=run/'work';shutil.copytree(root/'fixtures'/case,work);before=hashes(work)
        prompt=protocol['cases'][case]['prompt']
        if arm!='bare':prompt='Use $wigtn-plugins-with-codex:work-planner.\n'+prompt
        (run/'prompt.txt').write_text(prompt)
        meta=invoke(common+['-a','never','-m',protocol['model'],'-c',f'model_reasoning_effort="{protocol["effort"]}"','-s','read-only','-C',str(work),'exec','--ignore-rules','--skip-git-repo-check','--ephemeral','--json','-o',str(run/'answer.md'),'-'],envs[arm],work,run/'events.jsonl',stdin=prompt,timeout=protocol['timeout_seconds'])
        meta.update(item);meta['unchanged']=before==hashes(work);write(run/'meta.json',meta)
        print(f'{index}/{len(protocol["schedule"])} {case} {arm} exit={meta["exit_code"]} {meta["seconds"]}s',flush=True)
        if meta['exit_code']:raise SystemExit('Stopped on incomplete run; retained failure, no automatic retry')

def canonical(value):
    if isinstance(value,dict):return {k:canonical(v) for k,v in sorted(value.items())}
    if isinstance(value,list):return sorted((canonical(v) for v in value),key=lambda x:json.dumps(x,sort_keys=True))
    return value

def analyze(args):
    protocol=json.loads((args.root/'protocol.json').read_text());rows=[]
    for run in sorted((args.root/'runs').glob('*')):
        meta=json.loads((run/'meta.json').read_text());expected=protocol['cases'][meta['case']]['expected']
        raw=(run/'answer.md').read_text() if (run/'answer.md').exists() else ''
        try:answer=json.loads(raw.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip())
        except ValueError:answer=None
        failures=[]
        if not isinstance(answer,dict):failures=['No JSON object']
        else:
            for key,value in expected.items():
                if canonical(answer.get(key))!=canonical(value):failures.append(key)
        if not meta['unchanged']:failures.append('workspace mutation')
        usage=None;commands=[];output_bytes=0
        for line in (run/'events.jsonl').read_text().splitlines():
            try:e=json.loads(line)
            except ValueError:continue
            if e.get('type')=='turn.completed':usage=e.get('usage')
            item=e.get('item',{})
            if e.get('type')=='item.completed' and item.get('type')=='command_execution':
                commands.append(item.get('command',''));output_bytes+=len(item.get('aggregated_output','').encode())
        if meta['exit_code']!=0 or usage is None:failures.append('incomplete')
        row={**meta,'pass':not failures,'failures':failures,'usage':usage,'command_items':len(commands),'tool_output_bytes':output_bytes}
        rows.append(row)
    totals={}
    for arm in protocol.get('arms',['bare','baseline','candidate']):
        selected=[r for r in rows if r['arm']==arm];complete=all(r['usage'] is not None for r in selected)
        totals[arm]={'runs':len(selected),'passed':sum(r['pass'] for r in selected),
            **{key:sum(r['usage'][key] for r in selected) if complete else None for key in ['input_tokens','cached_input_tokens','output_tokens']},
            **{key:round(sum(r[key] for r in selected),3) for key in ['seconds','command_items','tool_output_bytes']}}
    write(args.root/'results.json',{'rows':rows,'totals':totals});print(json.dumps(totals,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','execute','analyze']);p.add_argument('--root',type=Path,required=True);p.add_argument('--baseline',type=Path);p.add_argument('--candidate',type=Path,help='Optional exact candidate snapshot; defaults to this checkout');p.add_argument('--suite',choices=['initial','followup'],default='initial')
    a=p.parse_args();a.root=a.root.resolve();globals()[a.action](a)
