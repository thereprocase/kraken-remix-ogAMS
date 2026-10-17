"""Axial assembly and helical installation checks on actual meshes."""
from check_thread import ROOT,ga,na,nv,nt,g,radial,loop_at,angles
import numpy as np,json
from scipy.optimize import brentq
from mesh_tools import make_manifold
P=json.loads((ROOT/'parameters.json').read_text());T=json.loads((ROOT/'analysis/thread.json').read_text());N=T['configurations'][-1];top=N['nut_outer_face_z'];phase=N['nut_phase_deg'];pitch=6.0
parts={}
for name in ('backing-sleeve','removable-flange'):
 d=np.load(ROOT/'artifacts'/f'{name}-assembled.npz');parts[name]=make_manifold(d['v'],d['t'])
rows=[]
for dz in np.linspace(0,13.2,45):
 a=nv.copy();a[:,:2]-=na;a[:,1:]*=-1
 ph=(phase+360*dz/pitch)*np.pi/180;rot=np.array([[np.cos(ph),-np.sin(ph)],[np.sin(ph),np.cos(ph)]])
 a[:,:2]=a[:,:2]@rot.T+ga;a[:,2]+=top+dz;m=make_manifold(a,nt)
 row={'lift_mm':float(dz),'rotation_deg':float(phase+360*dz/pitch),'gear_overlap_mm3':(m^g).volume(),'backing_overlap_mm3':(m^parts['backing-sleeve']).volume(),'flange_overlap_mm3':(m^parts['removable-flange']).volume()};rows.append(row)
 assert row['gear_overlap_mm3']<1e-6 and row['backing_overlap_mm3']<1e-6
 if dz>0:assert row['flange_overlap_mm3']<1e-6
 print('path',round(dz,2),row['gear_overlap_mm3'],flush=True)
# Lower and upper parts slide axially over gear shaft; minimum bores exceed
# maximum shaft barrel radius, plus explicit finite travel samples.
slides={}
for name,part in parts.items():
 slides[name]=[{'lift_mm':float(z),'gear_intersection_mm3':(part.translate((0,0,z))^g).volume()} for z in np.linspace(0,75,16)]
# Load-side flank proximity at fixed nut seating plane: sample actual surfaces,
# solve angle at first contact. This is geometric contact, no stress/load solve.
z=np.arange(top-11.9+.05,top-.049,.2);gg=np.array([radial(loop_at(g,a,ga,True),ga) for a in z]);source=make_manifold(nv,nt);nn=np.array([radial(loop_at(source,top-a,na,False),na) for a in z])
def gap(deg):
 ix=(deg/360*len(angles)-np.arange(len(angles)))%len(angles);i0=np.floor(ix).astype(int);f=ix-i0;i=i0%len(angles)
 return float((nn[:,i]*(1-f)+nn[:,(i+1)%len(angles)]*f-gg).min())
contacts=[]
for sign in (-1,1):
 a=brentq(gap,phase,phase+sign*30);contacts.append({'phase_deg':a,'relative_rotation_deg':a-phase,'sampled_min_radial_gap_mm':gap(a)})
out={'nut_helical_path':rows,'path_sampling_limit':'45 positions over 13.2 mm, pitch 6 mm. Finite samples supplemented by source matching thread profiles, not a rigorous swept Boolean or physical friction test.','sliding_install_paths':slides,'sampled_flank_contact_limits_at_fixed_seating_z':contacts,'no_stress_or_clamp_force_certification':True}
(ROOT/'analysis/paths.json').write_text(json.dumps(out,indent=2)+'\n')
