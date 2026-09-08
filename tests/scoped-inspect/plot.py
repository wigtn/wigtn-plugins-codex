#!/usr/bin/env python3
"""Render archived measurements; requires Matplotlib, performs no model calls."""
import json,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(sys.argv[1]).resolve();d=Path(sys.argv[2]).resolve();d.mkdir(parents=True,exist_ok=True)
data=json.loads((r/'results.json').read_text());protocol=json.loads((r/'protocol.json').read_text());arms=protocol.get('arms',['bare','baseline','candidate']);cases=sorted({row['case'] for row in data['rows']})
fig,ax=plt.subplots(figsize=(11,7));fig.patch.set_facecolor('#fafaf8');ax.set_facecolor('#fafaf8')
colors={'bare':'#bbc3cf','baseline':'#68788d','candidate':'#187f6d'}
labels={'bare':'No plugin','baseline':'v0.5.4','candidate':'Candidate 1'}
labels['candidate']='Candidate 2' if protocol.get('suite')=='followup' else 'Candidate 1'
for j,arm in enumerate(arms):
 values=[next(x['usage']['input_tokens']/1000 for x in data['rows'] if x['case']==case and x['arm']==arm) for case in cases]
 bars=ax.barh([i+(j-(len(arms)-1)/2)*.23 for i in range(len(cases))],values,height=.2,label=labels[arm],color=colors[arm])
 if arm=='candidate':ax.bar_label(bars,labels=[f'{v:.1f}' for v in values],padding=4,fontsize=9,color='#126858')
ax.set_yticks(range(len(cases)),[f'{c.split("-")[1].capitalize()} / {c.split("-")[2]} tasks' for c in cases]);ax.invert_yaxis()
ax.set_xlabel('Total input tokens reported by Codex CLI (thousands; cached input included)',labelpad=12)
ax.set_title(f'Focused saved-state retrieval: complete results from {len(data["rows"])} sessions',loc='left',fontsize=14,pad=45)
ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),ncol=3,frameon=False)
ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
for edge in ['top','right','left']:ax.spines[edge].set_visible(False)
ax.spines['bottom'].set_color('#c5cad0');ax.tick_params(axis='y',length=0)
fig.text(.02,.015,'Eight synthetic cases per arm. See the report for accuracy. This is not a general coding benchmark.',fontsize=9,color='#586573')
fig.tight_layout(rect=[0,.045,1,1]);fig.savefig(d/'input-by-case.png',dpi=170,facecolor=fig.get_facecolor());fig.savefig(d/'input-by-case.svg',facecolor=fig.get_facecolor())
print(d/'input-by-case.png')
