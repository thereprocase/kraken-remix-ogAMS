"""Stock tightening-tool cavity against corrected-axis inverted stock nut."""
from check_thread import ROOT,ga,na,nv,nt,g,radial,loop_at,angles
import numpy as np,json
from scipy.optimize import minimize_scalar
from mesh_tools import make_manifold
from source_mesh import source
src=str(source('tool'))
d=np.load(src);tv,tt=d['v0'],d['t0'];tool=make_manifold(tv,tt)
# Tool is centred at zero to within source tessellation residual. Its open
# face is source Z-92.5; the six-lobe(?) outline is retained, not reconstructed.
N=json.loads((ROOT/'analysis/thread.json').read_text())['configurations'][-1];top=N['nut_outer_face_z'];phi=N['nut_phase_deg'];flangebase=top-1.5
nd=np.load(ROOT/'artifacts/nut-assembled.npz');nut=make_manifold(nd['v'],nd['t'])
zsamples=np.arange(flangebase+.05,top-.049,.1)
nr=np.array([radial(loop_at(nut,z,ga,True),ga) for z in zsamples])
tr=np.array([radial(loop_at(tool,-92.5-(z-flangebase),np.zeros(2),False),np.zeros(2)) for z in zsamples])
def gaps(deg):
 ix=(deg/360*len(angles)-np.arange(len(angles)))%len(angles);i0=np.floor(ix).astype(int);f=ix-i0;i=i0%len(angles)
 return tr[:,i]*(1-f)+tr[:,(i+1)%len(angles)]*f-nr
vals=np.array([gaps(j).min() for j in range(360)]);best=vals.argmax();fit=minimize_scalar(lambda a:-gaps(a).min(),bounds=(best-1,best+1),method='bounded');phase=float(fit.x%360)
a=tv.copy();a[:,1:]*=-1;ph=phase*np.pi/180;rot=np.array([[np.cos(ph),-np.sin(ph)],[np.sin(ph),np.cos(ph)]]);a[:,:2]=a[:,:2]@rot.T+ga;a[:,2]+=flangebase-92.5
m=make_manifold(a,tt);fd=np.load(ROOT/'artifacts/removable-flange-assembled.npz');flange=make_manifold(fd['v'],fd['t'])
np.savez_compressed(ROOT/'analysis/tool-assembled.npz',v=a,t=tt)
out={'tool_source':src,'tool_rotation_z_deg_after_flip':phase,'tool_open_face_z':float(a[:,2].min()),'tool_top_z':float(a[:,2].max()),'retained_nut_overlap_mm3':(m^nut).volume(),'gear_overlap_mm3':(m^g).volume(),'new_flange_overlap_mm3':(m^flange).volume(),'sampled_nut_cavity_min_radial_clearance':float(gaps(phase).min()),'tool_outer_envelope_radius':float(np.linalg.norm(a[:,:2]-ga,axis=1).max()),'radial_ribs_start':54,'note':'Tool used outside AMS before installation; only rigid registration; no tool or nut surface altered.'}
assert max(out[k] for k in ('retained_nut_overlap_mm3','gear_overlap_mm3','new_flange_overlap_mm3'))<1e-6
assert out['sampled_nut_cavity_min_radial_clearance']>0
print(out,flush=True);(ROOT/'analysis/tool.json').write_text(json.dumps(out,indent=2)+'\n')
