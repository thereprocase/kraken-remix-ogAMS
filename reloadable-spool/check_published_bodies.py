"""Reproduce added-part rotation-envelope checks using public repository 3MFs."""
from pathlib import Path
import argparse,json,hashlib,zipfile,xml.etree.ElementTree as ET
import numpy as np,manifold3d as mf
from source_mesh import ROOT
from mesh_tools import make_manifold
ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,default=ROOT.parent);args=ap.parse_args();P=json.loads((ROOT/'parameters.json').read_text())
def cyl(r,z,h):return mf.Manifold.cylinder(h,r,r,512).translate((0,0,z))
def ring(ro,ri,z,h):return cyl(ro,z,h)-cyl(ri,z-1,h+2)
base=P['gear_disc_top'];top=base+P['backing_thickness'];ff=top+P['core_width_nominal'];bore=P['shaft_barrel_diameter']/2+P['sliding_clearance_radial'];r=P['flange_diameter']/2
# Sleeve conservative radius includes key for every azimuth and full height.
sr=P['assumed_cardboard_id']/2+P['assumed_cardboard_wall']-P['core_key_outer_recess']
envs={'backing':ring(r,bore,base,P['backing_thickness']),'sleeve_webs_key':ring(sr,bore,top,P['core_width_min']-P['sleeve_end_gap_at_min_width']),'far_flange_ribs_lug':ring(r,bore,ff,P['removable_flange_thickness']+P['tail_lug_height'])};cases=[]
for side,faces in [('right',[-82.27,1.73]),('left',[-81.63,2.37])]:
 for variant in ('standard','pocket'):
  p=args.repo/'models'/f'{side}-body-{variant}_full.3mf'
  with zipfile.ZipFile(p) as z:x=ET.fromstring(z.read('3D/3dmodel.model'))
  objects=x.findall('.//{*}object');assert len(objects)==1 and x.find('{*}build')[0].attrib.get('transform') is None
  v=np.array([[float(a.attrib[k]) for k in ('x','y','z')] for a in x.findall('.//{*}vertex')]);t=np.array([[int(a.attrib[k]) for k in ('v1','v2','v3')] for a in x.findall('.//{*}triangle')]);body=make_manifold(v,t);rows=[]
  for bay,gf in enumerate(faces,1):
   for shift in (-.79,0,.79):
    for name,env in envs.items():
     moved=env.rotate((0,90,0)).translate((gf+2.15+shift,-54.39,-24.18));vol=(body^moved).volume();assert vol<1e-6,(p,bay,name,vol);rows.append({'bay':bay,'axial_shift_mm':shift,'envelope':name,'overlap_mm3':vol})
  cases.append({'source':str(p.relative_to(args.repo)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'checks':rows});print(p.name,'PASS',flush=True)
(ROOT/'analysis/published-body-envelope.json').write_text(json.dumps({'status':'PASS body geometry only; OEM drive hardware unavailable','circular_envelope_sides':512,'max_inscribed_radial_deficit_mm':float(r*(1-np.cos(np.pi/512))),'cases':cases},indent=2)+'\n')
