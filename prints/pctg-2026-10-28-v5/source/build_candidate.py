"""Engineer-defined underside features on the accepted native cut5 bodies.

Reference meshes are never geometry inputs. All coordinates derive from the
existing mechanical datums and named printability parameters. Accepted sources
and releases are read-only; exports go exclusively beneath this directory.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parent;FULL=ROOT.parent
sys.path.insert(0,str(FULL))
from build123d import import_step,export_step,Plane,Vector,Edge,Wire,Face,Solid
from mechanical_body import resolve_design,prism,polar,norm,cut,union,cylinder,mounting_foot,rear_beam
from native_features import triangulate,export_3mf,box_bounds
from export_guards import rfid_no_addition

DESIGN=dict(underside_angle_deg=45.,cable_roof_bridge_mm=.8,
            feeder_channel_mode='constant_width',
            platform_step_chamfer_angle_deg=45.)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def build(side,out,mode):
 t0=time.time();p=resolve_design(__import__(side).P);d=dict(DESIGN)
 for folder in ['artifacts','reports','analysis']:(out/folder).mkdir(parents=True,exist_ok=True)
 baseline=FULL/'artifacts'/f'{side}_pre_circled_1711_display.npz';link=out/'artifacts'/baseline.name
 if not link.exists():link.symlink_to(baseline)
 source=FULL/'artifacts'/f'{side}_M5_gear_edit_cut5.step';shape=import_step(source);start_volume=shape.volume
 assert shape.is_valid and len(shape.solids())==1
 a=p['bay_datum']+p['bay_width']+p['middle_wall'];b=a+p['bay_width'];e=p['boolean_overlap']
 slope=math.tan(math.radians(d['underside_angle_deg']));features=[]
 def handed(s):return s.mirror(Plane.YZ).translate((p['mirror_translation'],0,0)) if p['mirror'] else s
 def remove(name,tool,drivers):
  nonlocal shape
  before=shape.volume;shape=cut(shape,handed(tool))
  assert shape.is_valid and len(shape.solids())==1,(name,'invalid or disconnected')
  features.append(dict(name=name,operation='bulk cut',removed_mm3=before-shape.volume,drivers=drivers))
  print(side,name,round(before-shape.volume,3),flush=True)

 # Cable-bundle passage: retain the existing rectangular opening, extend its
 # roof into a conventional 45 degree gable. It only removes material and
 # stops exactly at the cable-side skin; the RFID wall is not perforated.
 z=p['tray_entry_z']+p['tray_entry_relief_station']+p['tray_entry_relief_length']+e
 width=p['tray_entry_width'];cx=a+width/2;rise=(width-d['cable_roof_bridge_mm'])/2*slope
 points=[(a,z-e),(a+width,z-e),(cx+d['cable_roof_bridge_mm']/2,z+rise),(cx-d['cable_roof_bridge_mm']/2,z+rise)]
 tool=prism(points,p['platform_y']-e,p['bottom_y']+e,'Y')
 remove('cable entry gabled roof',tool,dict(clear_width=width,roof_angle=d['underside_angle_deg'],top_bridge=d['cable_roof_bridge_mm'],roof_start_z=z))

 # Deep-tray leading stock currently starts on a flat Z face. A single
 # 45 degree underside ramp grows from the existing curved cradle backing.
 # Preserve the complete cradle outer cylinder and both bounding walls.
 _,start=polar(p['floor_y'],p['floor_z'],p['cradle_radius'],p['cradle_rear_angle'])
 radius=p['cradle_radius']+p['cradle_skin']
 y0=p['floor_y']+math.sqrt(radius*radius-(start-p['floor_z'])**2)
 end=start+(p['bottom_y']-y0)*slope
 wedge=prism([(y0,start-e),(p['bottom_y']+e,start-e),(p['bottom_y']+e,end+e)],a,b)
 protected=cylinder(radius,a-e,b+e,p['floor_y'],p['floor_z'])
 ramp_tool=cut(wedge,protected)
 if p['ferrite_holder']:
  # Preserve the complete two-rail holder, not just its sampled contacts.
  # Its existing tray and seam-wall roots already support it. Do not add
  # a second root through the cable entrance below the holder.
  cx=b+p['seam_wall']-p['ferrite_seam_offset'];half=p['ferrite_mouth']/2
  top=p['bottom_y']-p['cradle_skin'];base=p['platform_y']-p['heel_radius']
  front=p['tray_rear_z']-p['ferrite_root_overlap'];outer=p['ferrite_rail_width']
  for low,high in [(cx-half-outer,cx-half),(cx+half,cx+half+outer)]:
   keep=box_bounds(low,high,base-e,p['bottom_y']+e,front-e,p['motor_front'])
   ramp_tool=cut(ramp_tool,keep)
 remove('deep tray underside ramp',ramp_tool,dict(angle=d['underside_angle_deg'],cradle_outer_radius=radius,start_z=start,start_y=y0,end_z=end,preserve_ferrite_rails=p['ferrite_holder']))

 # The platform depth step is a short outward ledge at the feed-end start.
 # Chamfer its underside inside the box seating strip, keeping that entire
 # mating strip and all platform surfaces beyond the chamfer unchanged.
 base=p['platform_y']+p['platform_depth'];top=base+p['case_step'];z=p['platform_front']
 run=p['case_step']/math.tan(math.radians(d['platform_step_chamfer_angle_deg']))
 low=p['bay_datum']+p['box_feed_land_width'];high=b
 tool=prism([(base,z-e),(top+e,z-e),(top+e,z+run+e)],low,high)
 remove('platform step underside chamfer',tool,dict(size=p['case_step'],angle_deg=d['platform_step_chamfer_angle_deg'],protected_box_land_end_x=low,start_z=z))

 if mode=='channel':
  # Experimental alternative: a constant-width open PTFE/cable route instead
  # of the unnecessarily wide flare. Its minimum width remains unchanged.
  # Kept separate until hardware, route and layer checks justify acceptance.
  for index in range(p['bay_count']):
   cx=p['bay_datum']+index*p['pitch']+p['bay_width']/2
   center=cx+p['mount_x_offset'];half=p['feeder_body_width']/2
   front=p['motor_front'];back=p['mount_front'];top=p['mount_top']-p['feeder_nose_rise'];bottom=p['motor_pocket_y']+p['mount_return_thickness']
   nose=norm(mounting_foot(p,center-half-e,center+half+e).intersect(box_bounds(center-half-e,center+half+e,top-e,bottom+e,front,back+e)))
   local=dict(p);local['deep_tray']=index==1
   nose=norm(nose.intersect(rear_beam(local,center-half-2*e,center+half+2*e,True)))
   angle=math.radians(p['feeder_nose_channel_angles'][index]);w=p['feeder_nose_channel_widths'][index]/2
   start=front-w-e;end=back+w+e;origin=center+p['feeder_nose_channel_offsets'][index]-(start-front)*math.tan(angle)
   profile=[(-w,top-e),(w,top-e),(w,bottom+e),(-w,bottom+e)]
   vertices=[Vector(origin+n*math.cos(angle),y,start+n*math.sin(angle)) for n,y in profile]
   face=Face(Wire([Edge.make_line(u,v) for u,v in zip(vertices,vertices[1:]+vertices[:1])]))
   length=(end-start)/math.cos(angle);slot=Solid.extrude(face,Vector(-math.sin(angle)*length,0,math.cos(angle)*length))
   nose=cut(nose,slot);before=shape.volume;shape=union([shape,handed(nose)],names=['accepted candidate','constant-width feeder nose'])
   features.append(dict(name=f'feeder nose {index+1} constant-width route',operation='bulk extrude and slot cut',added_mm3=shape.volume-before,clear_width=2*w))
   assert shape.is_valid and len(shape.solids())==1

 label=f'{side}_body_pocket_cut5_printable';v,t=triangulate(shape)
 gate=rfid_no_addition(out,side,label,v,t)
 base=out/'artifacts'/label;export_step(shape,str(base)+'.step');export_3mf(shape,str(base)+'.3mf',mesh=(v,t));np.savez_compressed(str(base)+'_display.npz',v=v,t=t)
 reimport=import_step(str(base)+'.step');assert reimport.is_valid and len(reimport.solids())==1
 report=dict(side=side,status='EXPERIMENTAL_NOT_RELEASED',mode=mode,parameters=d,source=str(source),source_sha256=sha(source),features=features,initial_volume_mm3=start_volume,volume_mm3=shape.volume,native_valid=True,native_solids=1,export_roundtrip_volume_error_mm3=reimport.volume-shape.volume,rfid_gate=gate,elapsed_s=time.time()-t0,files={x.name:sha(x) for x in out.glob('artifacts/'+label+'*')})
 (out/'reports'/f'{side}-build.json').write_text(json.dumps(report,indent=2))
 print('DONE',side,report['elapsed_s'],flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('side',choices=['right','left']);ap.add_argument('--mode',choices=['tray','channel'],default='tray');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();build(a.side,a.out.resolve(),a.mode)
