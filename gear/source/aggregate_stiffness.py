"""Paired load-case comparisons; no comparing minima from different loads."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
A=ROOT/'analysis'
def read(v,h,c):return json.loads((A/f'stiffness-{v}-h{h:g}-core{c:g}.json').read_text())
rows=[]
for h in [1.5,1,.75,.5]:
 for c in ([1,.5,.25] if h<=.75 else [1,.5]):
  original=read('original',h,c)
  for variant in ['plain','spokes']:
   candidate=read(variant,h,c)
   assert candidate['input_sha256']==hashlib.sha256((ROOT/'artifacts'/f'gear-{variant}.stl').read_bytes()).hexdigest()
   cases=[]
   for b,q in zip(original['checks'],candidate['checks']):
    assert (b['mode'],b['load'])==(q['mode'],q['load'])
    cases.append(dict(mode=b['mode'],load=b['load'],stiffness_ratio=q['stiffness']/b['stiffness'],original_compliance=b['compliance'],candidate_compliance=q['compliance']))
   rows.append(dict(variant=variant,grid_mm=h,core_fraction=c,cases=cases,
    minimum_torsion_ratio=min(x['stiffness_ratio'] for x in cases if x['mode']=='in_plane'),
    minimum_bending_ratio=min(x['stiffness_ratio'] for x in cases if x['mode']=='out_of_plane')))
summary=[]
for variant in ['plain','spokes']:
 fine=[r for r in rows if r['variant']==variant and r['grid_mm']==.5]
 convergence=[]
 for f in fine:
  coarse=next(r for r in rows if r['variant']==variant and r['grid_mm']==.75 and r['core_fraction']==f['core_fraction'])
  convergence.append(dict(core_fraction=f['core_fraction'],max_paired_ratio_relative_change=max(abs(b['stiffness_ratio']/a['stiffness_ratio']-1) for a,b in zip(coarse['cases'],f['cases'])),
    max_original_compliance_relative_change=max(abs(b['original_compliance']/a['original_compliance']-1) for a,b in zip(coarse['cases'],f['cases'])),
    max_candidate_compliance_relative_change=max(abs(b['candidate_compliance']/a['candidate_compliance']-1) for a,b in zip(coarse['cases'],f['cases']))))
 summary.append(dict(variant=variant,finest_grid_mm=.5,minimum_torsion_ratio_all_core_sensitivities=min(r['minimum_torsion_ratio'] for r in fine),minimum_bending_ratio_all_core_sensitivities=min(r['minimum_bending_ratio'] for r in fine),convergence_from_075_to_05=convergence,
  finer_all_cases_pass=all(x['stiffness_ratio']>1 for r in fine for x in r['cases']),
  physical_equivalence_certified=False))
result=dict(status='PASS_COMPARATIVE_LINEAR_MODEL_ONLY',load_cases_per_configuration=52,finest_core_sensitivities=[1,.5,.25],summary=summary,rows=rows)
(A/'STIFFNESS-SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(summary,indent=2))
for row in rows:
 if row['grid_mm']==.5:print(row['variant'],row['core_fraction'],row['minimum_torsion_ratio'],row['minimum_bending_ratio'])
