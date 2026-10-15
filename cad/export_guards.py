"""Read-only validation gates. No mesh data from this module constructs CAD geometry."""
from pathlib import Path
import json,hashlib,numpy as np,manifold3d as mf
from mesh_ops import make_manifold,boxclip

def rfid_no_addition(root,side,stage,v,t):
 root=Path(root);baseline=root/'reference'/f'{side}_rfid_baseline.npz'
 if not baseline.exists():raise RuntimeError(f'RFID export gate baseline missing: {baseline}')
 old=np.load(baseline);prior=make_manifold(old['v'],old['t']);cad=make_manifold(v,t)
 center=-1.775 if side=='right' else -1.134265
 bounds=([center-.89,-39.,-39.],[center+.89,62.,78.])
 delta=cad-prior
 residual=boxclip(delta,*bounds);added=residual.volume()
 access_bounds=([-2.675,-39.,-39.],[.376,62.,78.]) if side=='right' else ([-2.034,-39.,-39.],[1.215,62.,78.])
 # Only the PCB access envelope belongs to this cavity. A broad box also
 # includes the adjacent roller bearing, which is a different interface.
 polygon=[[-39.04,-41.63],[62.,-41.63],[62.,72.97],[-39.04,72.97]]
 for normal,offset in [(np.array([.723471761,.690353975]),-11.9618094+38.4),(np.array([.685152,-.7284]),-48.15979)]:
  clipped=[]
  for aa,bb in zip(polygon,polygon[1:]+polygon[:1]):
   aa,bb=np.array(aa),np.array(bb);da,db=aa@normal-offset,bb@normal-offset
   if da>=0:clipped.append(aa.tolist())
   if (da>=0)!=(db>=0):clipped.append((aa+(bb-aa)*da/(da-db)).tolist())
  polygon=clipped
 access_x=(-.875,.376) if side=='right' else (-.23525,1.215)
 access=mf.CrossSection([polygon]).extrude(access_x[1]-access_x[0]).transform([[0,0,1,access_x[0]],[1,0,0,0],[0,1,0,0]])
 # Locate the existing loft entrance plane for validation only. The broad
 # envelope above would otherwise count unchanged cradle tessellation outside it.
 tri=old['v'][old['t']];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);area=np.linalg.norm(cross,axis=1)
 normals=cross/np.maximum(area[:,None],1e-30);centers=tri.mean(1)
 expected=np.array([-2/(1.25 if side=='right' else 1.45),.72347,.69035]);expected/=np.linalg.norm(expected)
 mask=(abs(normals@expected)>.999)&(centers[:,0]>access_x[0]-.01)&(centers[:,0]<access_x[1]+.01)&(centers[:,1]>-35)&(centers[:,2]<73)&(centers[:,2]>-42)
 vertices=tri[mask].reshape(-1,3);assert len(vertices)>12,'Prior RFID loft plane not found'
 center=vertices.mean(0);_,_,vh=np.linalg.svd(vertices-center,full_matrices=False);normal=vh[-1];normal*=np.sign(normal@expected)
 offsets=vertices@normal;offset=float(offsets.max()+1e-5)
 access=access.trim_by_plane(normal.tolist(),offset)
 access_residual=delta^access;access_added=access_residual.volume();added_full=added+access_added
 limit=1e-6
 report=dict(side=side,stage=stage,gate='No added material in prior RFID friction pocket',baseline=str(baseline),baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),bounds_mm=bounds,added_to_prior_friction_pocket_mm3=added,numerical_volume_tolerance_mm3=limit,added_to_prior_full_pocket_mm3=added_full,access_residual_components=[dict(volume_mm3=q.volume(),bounds_mm=list(q.bounding_box())) for q in sorted(access_residual.decompose(),key=lambda q:-q.volume())[:20]],access_envelope_planes='PCB roof envelope clipped to independently fitted prior loft entrance plane',prior_access_plane_normal=normal.tolist(),prior_access_plane_offset=offset,prior_access_plane_fit_range_mm=float(np.ptp(offsets)),added_to_access_envelope_mm3=access_added,no_added_pocket_material_pass=max(added,added_full)<=limit,residual_bounds_mm=list(residual.bounding_box()) if added>0 else None,residual_components=[dict(volume_mm3=q.volume(),bounds_mm=list(q.bounding_box())) for q in sorted(residual.decompose(),key=lambda q:-q.volume())[:12]])
 (root/'reports'/f'{side}_{stage}_export_gate.json').write_text(json.dumps(report,indent=2,allow_nan=False))
 if max(added,added_full)>limit:
  np.savez(root/'analysis'/f'{side}_{stage}_rejected_export_candidate.npz',v=v,t=t)
  raise RuntimeError(f'Refusing STEP/3MF export: added {added:.9f} mm3 friction / {added_full:.9f} mm3 full cavity inside the prior RFID pocket; allowed numerical residue {limit} mm3')
 return report
