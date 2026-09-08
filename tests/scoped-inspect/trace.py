#!/usr/bin/env python3
"""Extract command records for manual audit. Does not assert execution safety."""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();sections=[];rows=[];thread_ids=[]
for run in sorted((root/'runs').iterdir()):
 if not (run/'meta.json').exists():continue
 meta=json.loads((run/'meta.json').read_text());commands=[];completed=0
 for line in (run/'events.jsonl').read_text().splitlines():
  try:event=json.loads(line)
  except ValueError:continue
  if event.get('type')=='thread.started':thread_ids.append(event['thread_id'])
  if event.get('type')=='turn.completed':completed+=1
  item=event.get('item',{})
  if event.get('type')=='item.completed' and item.get('type')=='command_execution':commands.append(item['command'])
 rows.append({'run':run.name,'case':meta['case'],'arm':meta['arm'],'command_items':len(commands),
              'completed_turns':completed,'workspace_unchanged':meta['unchanged'],
              'used_task_option':any('inspect --task' in c for c in commands),
              'read_workgraph_reference':any('references/workgraph-contract.md' in c for c in commands)})
 sections.append('## '+run.name+'\n\n'+'\n\n'.join('```sh\n'+c+'\n```' for c in commands))
(root/'command-trace.md').write_text('\n\n'.join(sections)+'\n')
counters={'runs':len(rows),'unique_session_ids':len(set(thread_ids)),
 'completed_turns':sum(r['completed_turns'] for r in rows),'command_items':sum(r['command_items'] for r in rows),
 'manual_review_status':'not performed by this script; see trace-audit.json if present','rows':rows}
(root/'trace-counters.json').write_text(json.dumps(counters,indent=2)+'\n')
print(json.dumps({k:v for k,v in counters.items() if k!='rows'},indent=2))
