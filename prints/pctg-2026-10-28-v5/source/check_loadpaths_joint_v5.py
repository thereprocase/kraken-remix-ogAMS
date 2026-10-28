"""Native load-strip invariance, cable envelope, and delivered cross-half motion.

v5 variant (2026-10-28): the cap box locating wall region is split at native Z -91 so the deliberate v5 end-wall
foot (bed end, Z -124.95..-92) is reported separately and the wall above it must still be identical to the accepted
body. The v5 drop-in bar (U-slots) replaces the accepted bar in the cross-half insert path."""
from pathlib import Path
import sys,json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parent;FULL=ROOT.parent;sys.path.insert(0,str(FULL))
from build123d import import_step,Plane
from native_features import box_bounds
from mechanical_body import resolve_design,norm,cut,union
from validate_stage import make_manifold
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mesh(p):d=np.load(p);return make_manifold(d['v'],d['t'])
def volume(s):return 0. if s is None else float(s.volume)
out=Path(sys.argv[1]).resolve();records=[];parts={}
for side in ['right','left']:
 p=resolve_design(__import__(side).P);s=import_step(out/'artifacts'/f'{side}_body_pocket_cut5_printable.step');old=import_step(FULL/'artifacts'/f'{side}_M5_gear_edit_cut5.step')
 def handed(shape):return shape.mirror(Plane.YZ).translate((p['mirror_translation'],0,0)) if p['mirror'] else shape
 regions=[]
 for name,z in [('shaft',p['axle_z']),('roller',p['roller_axis_z'])]:
  regions.append((name+' load section',box_bounds(-150,150,-150,150,z-10,z+10)))
 # Preserve all material in the whole outer locating wall and feed seating
 # strip; stronger than the individual retained hardware probe patches.
 a=p['bay_datum'];b=a+2*p['bay_width']+p['middle_wall']
 regions.extend([('cap box locating wall above the v5 foot zone',handed(box_bounds(a-100,a,-150,150,-91,130))),
  ('broad box seating land',handed(box_bounds(a,a+p['box_feed_land_width'],p['platform_y']+p['platform_depth'],p['bottom_y']+1,p['z_feed']-p['box_feed_land_front_offset'],130)))])
 rows=[]
 foot=handed(box_bounds(a-100,a,-150,150,-130,-91));fa=norm(s.intersect(foot));fb=norm(old.intersect(foot))
 foot_change=volume(norm(fa.cut(fb)))+volume(norm(fb.cut(fa)))
 for name,region in regions:
  aa=norm(s.intersect(region));bb=norm(old.intersect(region));change=volume(norm(aa.cut(bb)))+volume(norm(bb.cut(aa)))
  rows.append(dict(region=name,native_symmetric_difference_mm3=change,status='PASS' if change<.001 else 'FAIL'))
 # Cable bundle entry receives a removal-only roof; preserve its already
 # validated clearance and the entire lower RFID backing skin alongside it.
 wall=a+p['bay_width']+p['middle_wall'];e=p['boolean_overlap']
 corridor=handed(box_bounds(wall,wall+p['tray_entry_width'],p['platform_y'],p['bottom_y']+e,p['tray_entry_z'],p['tray_entry_z']+p['tray_entry_width']))
 added=norm(s.cut(old));obstruction=volume(norm(added.intersect(corridor))) if added else 0.
 rows.append(dict(region='cap end wall foot zone (v5 feature, native Z -130..-91)',native_symmetric_difference_mm3=foot_change,status='REPORTED',scope='Deliberate v5 rear foot; see rear_face_v5.py report for the feature volumes.'))
 rows.append(dict(region='main cable entry no new obstruction',added_native_mm3=obstruction,status='PASS' if obstruction<.001 else 'FAIL',scope='Existing15mm opening and lower rectangular route retained; actual cable bundle dimensions remain unprovided.'))
 parts[side]=mesh(out/'artifacts'/f'{side}_body_pocket_cut5_printable_display.npz')
 parts[side+'bar']=mesh(out/'artifacts'/f'{side}_bar_slot_v5_display.npz')
 records.append(dict(side=side,checks=rows,status='PASS' if all(r['status'] in ('PASS','REPORTED') for r in rows) else 'FAIL'))
 print(side,[(r['region'],r['status']) for r in rows],flush=True)
r=parts['right'];l=parts['left'].translate([167.36,0,0]);rb=parts['rightbar'];lb=parts['leftbar'].translate([167.36,0,0]);joint=[];insert=[]
for z in [-200.,-150.,-100.,-50.,-20.,-10.,-5.,-2.,0.]:
 v=float((r^l.translate([0,0,z])).volume());joint.append(dict(offset_z_mm=z,overlap_mm3=v,status='PASS' if abs(v)<.01 else 'FAIL'))
for z in np.linspace(0,12,49):
 for side,bar,other in [('right',rb,l+lb),('left',lb,r+rb)]:
  v=float((bar.translate([0,0,float(z)])^other).volume());insert.append(dict(side=side,travel_mm=float(z),overlap_mm3=v,status='PASS' if abs(v)<.001 else 'FAIL'))
result=dict(native_regions=records,seam_slide=joint,cross_half_insert_path=insert,status='PASS' if all(r['status']=='PASS' for r in records+joint+insert) else 'FAIL',limits='Native unchanged20mm Z strips permit reuse of the prior sampled net-section calculation, not reuse of unconverged whole-body FE stiffness. Discrete motion samples; no full AMS box or fully routed flexible cables. No physical warp/strength qualification.',hashes={str(p):sha(p) for p in (out/'artifacts').glob('*printable*')})
(out/'reports'/'loadpaths-joint.json').write_text(json.dumps(result,indent=2));print(result['status'],flush=True)
