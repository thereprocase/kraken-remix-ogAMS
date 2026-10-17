"""Two analytic parts around immutable Kraken gear/nut meshes.
All manufacturing shapes come from named drivers and ordinary cylinders,
plates, radial webs and a tapered cardboard-notch key. Millimetres.
"""
from pathlib import Path
import json,sys,math
import numpy as np
from build123d import Solid,Plane,Axis,Wire,Face,export_step,Compound
ROOT=Path(__file__).resolve().parent

from source_mesh import read_stl,write_stl,source
from mesh_tools import triangulate,make_manifold,export_3mf
P=json.loads((ROOT/'parameters.json').read_text())
I=json.loads((ROOT/'analysis/interfaces.json').read_text())

def cyl(r,h,z=0):return Solid.make_cylinder(r,h,Plane(origin=(0,0,z)))
def ring(ro,ri,h,z=0):return cyl(ro,h,z).cut(cyl(ri,h,z))
def radial_web(ri,ro,w,h,z,angle):
 return Solid.make_box(ro-ri,w,h,Plane(origin=(ri,-w/2,z))).rotate(Axis.Z,angle)
def build(p=P):
 r=p['flange_diameter']/2;b=p['backing_thickness'];sr=p['core_support_diameter']/2
 bore=p['shaft_barrel_diameter']/2+p['sliding_clearance_radial'];collar=bore+p['centering_collar_wall']
 h=p['core_width_min']-p['sleeve_end_gap_at_min_width'];ch=p['sleeve_tip_chamfer']
 lower=ring(r,bore,b)
 sleeve=ring(sr,sr-p['core_support_wall'],h-ch,b)
 tip=Solid.make_cone(sr,sr-ch,ch,Plane(origin=(0,0,b+h-ch))).cut(cyl(sr-p['core_support_wall'],ch,b+h-ch))
 lower=lower.fuse(sleeve,tip,ring(collar,bore,p['centering_collar_height'],b))
 for j in range(p['lower_web_count']):lower=lower.fuse(radial_web(collar-.1,sr-p['core_support_wall']+.1,p['lower_web_thickness'],p['lower_web_height'],b,j*360/p['lower_web_count']))
 # Key protrudes into the cardboard's existing end notch. Its top is a 45deg
 # ramp; footprint starts inside the sleeve so it is one attached solid.
 kw=p['core_key_width'];kp=p['assumed_cardboard_id']/2+p['assumed_cardboard_wall']-p['core_key_outer_recess']-sr;kl=p['core_key_axial_length'];kr=kp
 assert 0<kp<kl, 'Cardboard wall/key envelope inconsistent'
 points=[(sr-p['core_support_wall']/2,-kw/2,b),(sr+kp,-kw/2,b),(sr+kp,-kw/2,b+kl-kr),(sr,-kw/2,b+kl),(sr-p['core_support_wall']/2,-kw/2,b+kl)]
 key=Solid.extrude(Face(Wire.make_polygon(points,close=True)),(0,kw,0));lower=lower.fuse(key)
 f=p['removable_flange_thickness'];rh=p['flange_rib_height'];rw=p['flange_rim_width']
 upper=ring(r,bore,f).fuse(ring(r,r-rw,rh,f))
 for j in range(p['flange_rib_count']):upper=upper.fuse(radial_web(p['flange_rib_inner_radius'],r-rw/2,p['flange_rib_width'],rh,f,j*360/p['flange_rib_count']))
 # Two radial tail holes live entirely OUTSIDE the winding face. The low
 # lug adds no bump or hole on the inner face and stays inside D200.
 lr=p['tail_lug_radius'];ll=p['tail_lug_radial_length'];lw=p['tail_lug_width'];lh=p['tail_lug_height']
 upper=upper.fuse(Solid.make_box(ll,lw,lh,Plane(origin=(lr-ll/2,-lw/2,f))))
 for side in (-1,1):
  tool=Solid.make_cylinder(p['tail_hole_diameter']/2,r-lr+ll,Plane(origin=(lr-ll/2,side*p['tail_hole_pitch']/2,f+lh/2),z_dir=(1,0,0)))
  upper=upper.cut(tool)
 return {'backing-sleeve':lower,'removable-flange':upper}

def main():
 (ROOT/'artifacts').mkdir(exist_ok=True);(ROOT/'analysis').mkdir(exist_ok=True)
 parts=build();checks={};meshes={};ga=I['gear']['axis_xy']
 for name,s in parts.items():
  assert s.is_valid and len(s.solids())==1,name
  v,t=triangulate(s);m=make_manifold(v,t)
  export_step(s,ROOT/'artifacts'/f'{name}.step');write_stl(v,t,ROOT/'artifacts'/f'{name}.stl');export_3mf(s,ROOT/'artifacts'/f'{name}.3mf',mesh=(v,t))
  np.savez_compressed(ROOT/'artifacts'/f'{name}.npz',v=v,t=t)
  shift=np.array([*ga,P['gear_disc_top'] if name=='backing-sleeve' else P['gear_disc_top']+P['backing_thickness']+P['core_width_nominal']])
  meshes[name]=(v+shift,t);np.savez_compressed(ROOT/'artifacts'/f'{name}-assembled.npz',v=v+shift,t=t)
  checks[name]={'native_valid':s.is_valid,'native_solid_count':len(s.solids()),'native_volume_mm3':s.volume,'mesh_volume_mm3':m.volume(),'mesh_manifold_status':str(m.status()),'print_bounds':list(m.bounding_box()),'assembly_translation':shift.tolist(),'triangles':len(t)}
  print(name,checks[name],flush=True)
 export_step(Compound(children=[s.translate((*ga,P['gear_disc_top'] if n=='backing-sleeve' else P['gear_disc_top']+P['backing_thickness']+P['core_width_nominal'])) for n,s in parts.items()]),ROOT/'artifacts/added-parts-assembly.step')
 (ROOT/'analysis/build.json').write_text(json.dumps(checks,indent=2)+'\n')
if __name__=='__main__':main()
