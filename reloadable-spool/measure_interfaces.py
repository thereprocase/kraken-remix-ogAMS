"""Axis-aware source measurements. Meshes retained, never refitted for manufacture."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
ROOT=Path(__file__).resolve().parent

from source_mesh import read_stl,source
from mesh_tools import make_manifold
paths={'gear':source('gear'),'nut':source('nut')}
out={}
for name,path in paths.items():
 v,t=read_stl(path);s=make_manifold(v,t);fits=[]
 for z in ([5,8,12] if name=='gear' else [3,5,8]):
  loops=s.slice(z).to_polygons();a=np.asarray(max(loops,key=lambda a:np.ptp(a,axis=0).sum()))
  c=np.mean(a,axis=0);r=np.linalg.norm(a-c,axis=1).mean()
  fit=least_squares(lambda p:np.linalg.norm(a-p[:2],axis=1)-p[2],[*c,r]).x
  fits.append({'z':z,'axis_xy':fit[:2].tolist(),'radius':fit[2],'max_residual':float(np.abs(np.linalg.norm(a-fit[:2],axis=1)-fit[2]).max())})
 axis=np.mean([f['axis_xy'] for f in fits],axis=0)
 tri=v[t];r=np.linalg.norm(tri[:,:,:2]-axis,axis=2);area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
 flat=(np.ptp(tri[:,:,2],axis=1)<1e-5)&(r.min(1)>25)
 planes={}
 for z,a in zip(np.round(tri[flat,0,2],5),area[flat]):planes[float(z)]=planes.get(float(z),0)+float(a)
 sec=[]
 for z in ([4.1,8,14,16,18,20,58,60,62,64,66,68,70,71.8] if name=='gear' else [.1,1,1.2,1.3,2,3,5,8,10,11.8]):
  loops=[]
  for poly in s.slice(z).to_polygons():
   rad=np.linalg.norm(np.asarray(poly)-axis,axis=1);loops.append([float(rad.min()),float(rad.max())])
  sec.append({'z':z,'radial_ranges':loops})
 out[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'axis_fits':fits,'axis_xy':axis.tolist(),'dominant_planes':sorted(planes.items(),key=lambda a:-a[1])[:10],'sections':sec}
 print(name,json.dumps(out[name],indent=2),flush=True)
if (ROOT/'reference/bambu_wide.stl').exists():
 v,t=read_stl(ROOT/'reference/bambu_wide.stl');r=np.linalg.norm(v[:,1:],axis=1);key=v[(r>40.86)&(r<50)&(v[:,0]<30.21)]
 out['bambu_key']={'bounds_original_xyz':[key.min(0).tolist(),key.max(0).tolist()],'vertices':key.tolist()}
 print('key',key.min(0),key.max(0),flush=True)
else:
 prior=json.loads((ROOT/'analysis/interfaces.json').read_text());out['bambu_key']=prior['bambu_key']
(ROOT/'analysis/interfaces.json').write_text(json.dumps(out,indent=2)+'\n')
