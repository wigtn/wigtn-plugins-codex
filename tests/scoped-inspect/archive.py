#!/usr/bin/env python3
"""Copy an explicit evidence allowlist; never copy Codex homes/authentication."""
import hashlib,json,shutil,sys
from pathlib import Path
source,destination=map(lambda s:Path(s).resolve(),sys.argv[1:3])
if destination.exists():raise SystemExit('Destination must be new')
entries=['protocol.json','input-manifest.json','frozen-study.py','execution-started.json',
         'fixtures','snapshots','runs','results.json','deterministic-results.json']
entries += [name for name in ['adversarial-results.json','dense-dependency-result.json','command-trace.md','trace-counters.json','trace-audit.json'] if (source/name).is_file()]
entries += [p.name for p in sorted(source.glob('preflight-*.json'))]
for name in entries:
 p=source/name
 if not p.exists():raise SystemExit(f'Missing evidence: {name}')
 if p.is_symlink() or (p.is_dir() and any(q.is_symlink() for q in p.rglob('*'))):raise SystemExit(f'Unexpected evidence symlink: {name}')
destination.mkdir(parents=True)
for name in entries:
 p=source/name
 if p.is_dir():shutil.copytree(p,destination/name,ignore=shutil.ignore_patterns('__pycache__'))
 else:shutil.copy2(p,destination/name)
manifest={str(p.relative_to(destination)):hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(destination.rglob('*')) if p.is_file()}
(destination/'archive-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
original=json.loads((destination/'input-manifest.json').read_text())
assert all(manifest.get(name)==sha for name,sha in original.items()),'Frozen input verification failed'
print(json.dumps({'files':len(manifest),'bytes':sum(p.stat().st_size for p in destination.rglob('*') if p.is_file()),
      'manifest_sha256':hashlib.sha256((destination/'archive-manifest.json').read_bytes()).hexdigest()},indent=2))
