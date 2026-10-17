import sys,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent;
from source_mesh import read_stl
from mesh_tools import make_manifold
out={}
for name in ('wide','narrow'):
 v,t=read_stl(ROOT/'reference'/f'bambu_{name}.stl');v=v[:,[1,2,0]];s=make_manifold(v,t);rows=[]
 print(name,flush=True)
 for z in [-33.6,-32,-30.4,-30.2,-30,-29.5,-29,-27,-20,-10,-7,-5,0,.3,1,5,10,20,27,29,29.5,30,30.2,30.4,32,33.6]:
  polys=s.slice(z).to_polygons();ls=[]
  for poly in polys:
   a=np.asarray(poly);r=np.linalg.norm(a,axis=1);ls.append({'r_min':float(r.min()),'r_med':float(np.median(r)),'r_max':float(r.max()),'n':len(a)})
  if ls:print(z,[(round(a['r_min'],3),round(a['r_med'],3),round(a['r_max'],3)) for a in ls])
  rows.append({'axial_x':z,'loops':ls})
 out[name]=rows
(ROOT/'analysis/bambu_axial_sections.json').write_text(json.dumps(out,indent=2)+'\n')
# Core outer surface vertex clusters and their axial extents.
v,t=read_stl(ROOT/'reference/bambu_wide.stl');r=np.linalg.norm(v[:,1:],axis=1)
for rr in [40,40.5,40.75,41,42,43,44]:
 sel=abs(r-rr)<.03
 if sel.any():print('wide r',rr,'count',sel.sum(),'axial',v[sel,0].min(),v[sel,0].max())
