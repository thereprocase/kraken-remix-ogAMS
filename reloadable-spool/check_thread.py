"""Retained mesh thread phase check, with corrected nut axis and rigid flip."""
import sys,json,math
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar
ROOT=Path(__file__).resolve().parent;
from source_mesh import read_stl,source
from mesh_tools import make_manifold
I=json.loads((ROOT/'analysis/interfaces.json').read_text());ga=np.array(I['gear']['axis_xy']);na=np.array(I['nut']['axis_xy'])
gv,gt=read_stl(source('gear'));nv,nt=read_stl(source('nut'))
g=make_manifold(gv,gt);n=make_manifold(nv,nt)
angles=np.arange(0,360,.5)*np.pi/180

def radial(poly,axis):
 a=np.asarray(poly)-axis;b=np.roll(a,-1,axis=0);d=b-a
 u=np.stack([np.cos(angles),np.sin(angles)],axis=1)
 # vectorized ray/segment intersections in polar star-shaped thread sections
 den=u[:,0,None]*d[None,:,1]-u[:,1,None]*d[None,:,0]
 with np.errstate(divide='ignore',invalid='ignore'):
  rr=(a[None,:,0]*d[None,:,1]-a[None,:,1]*d[None,:,0])/den
  tt=(a[None,:,0]*u[:,1,None]-a[None,:,1]*u[:,0,None])/den
 rr[(tt< -1e-8)|(tt>1+1e-8)|(rr<0)]=-np.inf
 return rr.max(1)

def loop_at(s,z,axis,outer):
 loops=s.slice(float(z)).to_polygons()
 return (max if outer else min)(loops,key=lambda p:np.median(np.linalg.norm(np.array(p)-axis,axis=1)))

P=json.loads((ROOT/'parameters.json').read_text())
def check(core_width):
 backing_top=P['gear_disc_top']+P['backing_thickness'];flange_thickness=P['removable_flange_thickness'];nut_flange=P['nut_flange_thickness']
 top=backing_top+core_width+flange_thickness+nut_flange
 zs=np.arange(top-11.9+.05,top-.049,.25)
 gg=np.array([radial(loop_at(g,z,ga,True),ga) for z in zs])
 nn=np.array([radial(loop_at(n,top-z,na,False),na) for z in zs])
 def gaps(phi):
  # Rx180 inverts source angle; Rz(phi) supplies nut clocking.
  idx=(phi/(2*np.pi)*len(angles)-np.arange(len(angles)))%len(angles)
  lo0=np.floor(idx).astype(int);frac=idx-lo0;lo=lo0%len(angles)
  nr=nn[:,lo]*(1-frac)+nn[:,(lo+1)%len(angles)]*frac
  return nr-gg
 grid=np.arange(0,360,1);mins=np.array([gaps(a*np.pi/180).min() for a in grid]);best=grid[mins.argmax()]
 opt=minimize_scalar(lambda a:-gaps(a*np.pi/180).min(),bounds=(best-1,best+1),method='bounded');phase=float(opt.x%360)
 arr=nv.copy();arr[:,:2]-=na;arr[:,1:]*=-1
 ph=phase*np.pi/180;rot=np.array([[np.cos(ph),-np.sin(ph)],[np.sin(ph),np.cos(ph)]])
 arr[:,:2]=arr[:,:2]@rot.T+ga;arr[:,2]+=top
 placed=make_manifold(arr,nt);overlap=(g^placed).volume()
 result={'core_width':core_width,'nut_outer_face_z':top,'nut_inner_tip_z':top-11.9,'nut_phase_deg':phase,'thread_overlap_axial_mm':11.9,'radial_sample_min_clearance_mm':float(gaps(ph).min()),'radial_sample_max_clearance_mm':float(gaps(ph).max()),'sampling':'0.5 deg rays, 0.25 mm axial; explicit mesh Boolean supplements samples','gear_nut_interference_mm3':overlap,'shaft_tip_above_nut_mm':71.8999938965-top}
 assert overlap<1e-6 and gaps(ph).min()>0, "No compatible retained thread phase"
 print(json.dumps(result),flush=True)
 if core_width==P['core_width_nominal']:np.savez_compressed(ROOT/'artifacts/nut-assembled.npz',v=arr,t=nt)
 return result
if __name__=='__main__':
 out={'axis_provenance':'analysis/interfaces.json; fitted outer barrels, source facets unchanged','configurations':[check(w) for w in (P['core_width_min'],(P['core_width_min']+P['core_width_nominal'])/2,P['core_width_nominal'])]}
 # Axial pitch by circular radial sections; compare source ray at same phase.
 z=np.arange(24,64,.05);r=np.array([radial(loop_at(g,a,ga,True),ga)[0] for a in z]);cross=[]
 for j in range(len(z)-1):
  if r[j]<15.3<=r[j+1]:cross.append(float(z[j]+(15.3-r[j])/(r[j+1]-r[j])*.05))
 out['pitch_from_rising_midflank_crossings']={'crossings_z':cross,'median_pitch_mm':float(np.median(np.diff(cross)))}
 (ROOT/'analysis/thread.json').write_text(json.dumps(out,indent=2)+'\n')
