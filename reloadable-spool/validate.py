"""Native/export fidelity, source invariance, core proxy and part interference."""
import json,hashlib,zipfile,xml.etree.ElementTree as ET
import numpy as np
from build123d import import_step
import manifold3d as mf
from source_mesh import ROOT,source,read_stl
from mesh_tools import make_manifold
P=json.loads((ROOT/'parameters.json').read_text());I=json.loads((ROOT/'analysis/interfaces.json').read_text());ga=I['gear']['axis_xy'];rows={};parts={}
NS={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
for name in ('backing-sleeve','removable-flange'):
 step=import_step(ROOT/'artifacts'/f'{name}.step');v,t=read_stl(ROOT/'artifacts'/f'{name}.stl');m=make_manifold(v,t);d=np.load(ROOT/'artifacts'/f'{name}-assembled.npz');parts[name]=make_manifold(d['v'],d['t'])
 with zipfile.ZipFile(ROOT/'artifacts'/f'{name}.3mf') as z:
  x=ET.fromstring(z.read('3D/3dmodel.model'));v3=np.array([[float(q.attrib[k]) for k in ('x','y','z')] for q in x.findall('.//m:vertex',NS)]);t3=np.array([[int(q.attrib[k]) for k in ('v1','v2','v3')] for q in x.findall('.//m:triangle',NS)])
 d=np.load(ROOT/'artifacts'/f'{name}.npz');maxerr=float(np.abs(v3-d['v']).max());m3=make_manifold(v3,t3)
 rows[name]={'step_reread_valid':step.is_valid,'step_solid_count':len(step.solids()),'step_volume_mm3':step.volume,'stl_manifold':str(m.status()),'stl_volume_mm3':m.volume(),'stl_components':len(m.decompose()),'three_mf_manifold':str(m3.status()),'three_mf_vertex_max_deviation_mm':maxerr,'three_mf_faces_identical_to_native_tessellation':bool(np.array_equal(t3,d['t'])),'native_to_stl_volume_relative_error':abs(step.volume-m.volume())/step.volume}
 assert step.is_valid and len(step.solids())==1 and len(m.decompose())==1 and maxerr<1e-6
 assert rows[name]['native_to_stl_volume_relative_error']<1e-4
for name in ('gear','nut'):
 assert hashlib.sha256(source(name).read_bytes()).hexdigest()==I[name]['sha256'],name+' source changed'
gv,gt=read_stl(source('gear'));parts['gear']=make_manifold(gv,gt);d=np.load(ROOT/'artifacts/nut-assembled.npz');parts['nut']=make_manifold(d['v'],d['t'])
pairs=[]
for i,(a,ma) in enumerate(parts.items()):
 for b,mb in list(parts.items())[i+1:]:
  inter=ma^mb;vol=inter.volume();row={'a':a,'b':b,'overlap_mm3':vol}
  if vol>1e-6:
   bb=inter.bounding_box();depth=bb[5]-bb[2]
   row.update(axial_intersection_depth_mm=depth,classification='Source-float32 coplanar contact rounding; <=0.00001 mm, no CAD adjustment')
   assert {a,b}=={'removable-flange','nut'} and depth<1e-5
  pairs.append(row)
# Illustrative core only: dimensions of real cardboard remain UNVERIFIED.
base=P['gear_disc_top']+P['backing_thickness'];ri=P['assumed_cardboard_id']/2;ro=ri+P['assumed_cardboard_wall'];h=P['core_width_nominal']
core=mf.Manifold.cylinder(h,ro,ro,512)-mf.Manifold.cylinder(h,ri,ri,512)
notch_width=3.5;notch_depth=5.3
notch=mf.Manifold.cube((ro+1,notch_width,notch_depth)).translate((0,-notch_width/2,0));core=(core-notch).translate((*ga,base))
proxy_checks={n:(core^m).volume() for n,m in parts.items()}
assert max(proxy_checks.values())<1e-6
mesh=core.to_mesh64();np.savez_compressed(ROOT/'analysis/cardboard-PROXY-UNVERIFIED.npz',v=np.asarray(mesh.vert_properties)[:,:3],t=mesh.tri_verts)
# Through lug holes, small interior test cylinder proves the exported voids.
hole_checks=[];lugx=P['tail_lug_radius'];lugz=base+P['core_width_nominal']+P['removable_flange_thickness']+P['tail_lug_height']/2
for side in (-1,1):
 check=mf.Manifold.cylinder(8,1.0,1.0,64).rotate((0,90,0)).translate((lugx-3+ga[0],side*P['tail_hole_pitch']/2+ga[1],lugz));hole_checks.append((check^parts['removable-flange']).volume())
assert max(hole_checks)<1e-6
with zipfile.ZipFile(ROOT/'artifacts/assembly-reference-NOT-FOR-PRINT.3mf') as z:
 x=ET.fromstring(z.read('3D/3dmodel.model'));objects=x.findall('.//m:object',NS)
 gearobj=objects[0];av=np.array([[float(q.attrib[k]) for k in ('x','y','z')] for q in gearobj.findall('.//m:vertex',NS)]);at=np.array([[int(q.attrib[k]) for k in ('v1','v2','v3')] for q in gearobj.findall('.//m:triangle',NS)])
 assert len(objects)==4 and np.array_equal(av,gv) and np.array_equal(at,gt)
out={'status':'GEOMETRIC CHECKS PASS; PROTOTYPE, NOT INSTALL-CERTIFIED','exports':rows,'pairwise_actual_mesh_checks':pairs,'cardboard_proxy':{'id_mm':2*ri,'wall_mm':P['assumed_cardboard_wall'],'notch_width_mm':notch_width,'notch_depth_mm':notch_depth,'source':'ID/wall assumptions; notch based on Bambu plastic key envelope, NOT measured cardboard.','part_overlap_mm3':proxy_checks,'nominal_radial_clearance_mm':ri-P['core_support_diameter']/2,'key_tip_recess_inside_assumed_core_od_mm':P['core_key_outer_recess'],'sleeve_to_flange_end_gap_nominal_mm':h-(P['core_width_min']-P['sleeve_end_gap_at_min_width'])},'tail_hole_interior_overlap_mm3':hole_checks,'assembly_3mf_object_count':len(objects),'assembly_3mf_gear_vertices_and_faces_exactly_equal_to_retained_source':True,'retained_source_hashes_verified':True,'installed_drive_hardware':'UNVERIFIED: no installed OEM drive gear/hub geometry. Must check backing at gear engagement before operation.','physical_cardboard_fit':'UNVERIFIED','physical_clamp_torque_and_strength':'UNVERIFIED; no new FEA or test'}
(ROOT/'analysis/validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
