"""Owner fit correction: keyless sleeve and inward-stiffened clamping annulus.
Original source exports stay untouched. Flange prints outer face down.
"""
from pathlib import Path
import json,sys,hashlib,math
import numpy as np
from build123d import Solid,Plane,Axis,import_step,export_step,Compound
R=Path(__file__).resolve().parent;B=R.parents[1];F=B
sys.path.insert(0,str(B))
from mesh_tools import triangulate,make_manifold,export_3mf
from source_mesh import write_stl
P=json.loads((F/'parameters.json').read_text())
def cyl(r,h,z=0):return Solid.make_cylinder(r,h,Plane(origin=(0,0,z)))
def ring(ro,ri,h,z=0):return cyl(ro,h,z).cut(cyl(ri,h,z))
def norm(s):return s if hasattr(s,"wrapped") else Compound(children=list(s))
def vol(s):return 0 if s is None else s.volume if hasattr(s,'volume') else Compound(children=list(s)).volume
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out=R/'artifacts';out.mkdir(exist_ok=True)
bore=P['shaft_barrel_diameter']/2+P['sliding_clearance_radial'];skin=P['removable_flange_thickness'];sr=P['core_support_diameter']/2
sources=[B/'artifacts/backing-sleeve.step',F/'artifacts/removable-flange.step'];hashes={str(p):sha(p) for p in sources}
old_lower=import_step(sources[0]);old_upper=import_step(sources[1])
# Remove only material projecting beyond the sleeve radius above the backing.
lower=old_lower.cut(ring(44,sr,5.1,P['backing_thickness']))
# Upper face remains at original Z1.6. Added material extends into the vacant
# core centre and stops 0.40 mm short of the sleeve ID at every core width.
reinforcement_radius=sr-P['core_support_wall']-.40
added_depth=3.0
upper=ring(P['flange_diameter']/2,bore,skin).fuse(ring(reinforcement_radius,bore,added_depth,-added_depth))
hole_centers=[]
for pair in range(3):
 theta=math.pi/P['flange_rib_count']+pair*2*math.pi/3
 half=math.asin(6/91)
 for sign in [-1,1]:
  a=theta+sign*half;x,y=91*math.cos(a),91*math.sin(a)
  upper=upper.cut(Solid.make_cylinder(4,skin,Plane(origin=(x,y,0))))
  hole_centers.append([x,y])
# Native contact regions and hole bores must remain exact.
protected=ring(45,40.9,skin)
contact_delta=vol(norm(old_upper.intersect(protected)).cut(upper))+vol(norm(upper.intersect(protected)).cut(old_upper))
assert contact_delta<1e-6
nut_contact=ring(50,bore,.01,skin-.01)
assert vol(norm(old_upper.intersect(nut_contact)).cut(upper))+vol(norm(upper.intersect(nut_contact)).cut(old_upper))<1e-6
checks=[]
for name,shape in [('backing-sleeve-keyless',lower),('removable-flange-stiff-annulus',upper)]:
 assert shape.is_valid and len(shape.solids())==1
 export_step(shape,out/(name+'-installed.step'));back=import_step(out/(name+'-installed.step'))
 assert vol(back.cut(shape))+vol(shape.cut(back))<1e-5
 printed=shape if name.startswith('backing') else shape.rotate(Axis.X,180).translate((0,0,skin))
 export_step(printed,out/(name+'.step'))
 v,t=triangulate(printed);m=make_manifold(v,t);assert len(m.decompose())==1
 assert v[:,2].min()>-1e-5
 write_stl(v,t,out/(name+'.stl'));export_3mf(printed,out/(name+'.3mf'),mesh=(v,t));np.savez_compressed(out/(name+'.npz'),v=v,t=t)
 checks.append({'name':name,'native_valid':True,'solids':1,'volume_mm3':shape.volume,'bounds_print_mm':[v.min(0).tolist(),v.max(0).tolist()]})
# Existing sleeve at the shortest and longest documented core widths.
collisions=[]
for width in [60,61.2,62.4]:
 placed=upper.translate((0,0,P['backing_thickness']+width));overlap=vol(lower.intersect(placed));assert overlap<1e-6
 collisions.append({'core_width_mm':width,'added_parts_overlap_mm3':overlap})
for p in sources:assert sha(p)==hashes[str(p)]
report={'status':'native geometry checks PASS; physical fit and stiffness unverified','parameters':{'annulus_outer_radius_mm':reinforcement_radius,'annulus_inner_radius_mm':bore,'added_depth_mm':added_depth,'total_central_thickness_mm':skin+added_depth,'sleeve_radial_clearance_mm':.4,'outer_skin_mm':skin,'outer_ribs_removed':True,'key_removed':True},'parts':checks,'cardboard_contact_delta_mm3':contact_delta,'hole_centers':hole_centers,'core_width_checks':collisions,'source_sha256':{str(Path(k).relative_to(B)):v for k,v in hashes.items()},'limits':'See EXPORT-CHECKS.json for independent mesh/nut/tool/gear checks; no physical strength claim. Clamping friction is owner-selected, not measured.'}
(R/'CHECKS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
