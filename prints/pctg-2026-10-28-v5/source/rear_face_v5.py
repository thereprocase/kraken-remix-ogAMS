"""v5 rear (bed-end) face on the v4 printable cut5 bodies: square wall feet and widened web feet.

Why: the native rebuild gave the end, middle and seam walls sloped leading edges that touch the print bed on 1.4 mm
pads only, so the first layers are a comb of thin rails (first PCTG print curled at layer 6). The support webs already
use the box rear-corner clearance line (front_support_y, front_support_angle); the walls stop far above it. Here every
wall gets a square foot down to that line, and each web/rib gets a 45-degree widened foot in the free space beside it.
All coordinates derive from the existing design datums; no reference mesh is read.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parent;FULL=ROOT.parent
sys.path.insert(0,str(FULL))
from build123d import import_step,export_step,Plane,Solid,Face,Wire,Edge,Vector
from mechanical_body import resolve_design,prism,norm,cut,union,case_locating_land
from native_features import triangulate,export_3mf,box_bounds
from export_guards import rfid_no_addition

REAR=dict(foot_start_above_nose_mm=0.2,   # overlap into the existing 1.4 mm nose pad
          seam_foot_y=12.4,seam_foot_top_y=16.0,seam_foot_run=6.0,   # short seam-wall foot; the hub sits below it
          web_widen_mm=3.0,web_taper_run_mm=3.0)   # +3 mm per side at the bed, 45 deg back to nominal
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def rect_wire(x0,x1,y0,y1,z):
    pts=[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
    return Wire([Edge.make_line(a,b) for a,b in zip(pts,pts[1:]+pts[:1])])

def build(side,out,source=None):
    t0=time.time();p=resolve_design(__import__(side).P);d=dict(REAR)
    for folder in ['artifacts','reports','analysis']:(out/folder).mkdir(parents=True,exist_ok=True)
    source=Path(source) if source else out/'artifacts'/f'{side}_body_pocket_cut5_printable.step'
    shape=import_step(source);start_volume=shape.volume
    assert shape.is_valid and len(shape.solids())==1
    x=p['bay_datum'];w=p['bay_width'];m=p['middle_wall'];e=p['boolean_overlap']
    inner=[x,x+w,x+w+m,x+2*w+m]
    intervals=[(inner[0]-p['end_wall'],inner[0]),(inner[1],inner[2]),(inner[3],inner[3]+p['seam_wall'])]
    front=p['z_nonfeed'];top=p['axle_y']-p['crown_height'];crown_front=p['axle_z']-p['crown_front_reach']
    nose_y=top+(crown_front-front)*math.tan(math.radians(p['front_shoulder_angle']))
    y0=nose_y-d['foot_start_above_nose_mm']
    support_y=p['front_support_y'];run=(p['bottom_y']-support_y)/math.tan(math.radians(p['front_support_angle']))
    def handed(s):return s.mirror(Plane.YZ).translate((p['mirror_translation'],0,0)) if p['mirror'] else s
    # AMS side envelope (circular side draft, tangential draft, locating land) and the print-end limits,
    # exactly as mechanical_body.build applies them. Every foot tool is trimmed by them BEFORE the union,
    # so the body outside the feet is never re-cut and stays identical to v4.
    radius=p['case_side_radius'];case_x=inner[0]-p['case_side_axis_from_bay']
    side_clearance=Solid.make_cylinder(radius,p['z_feed']-p['z_nonfeed']+2*e,Plane(origin=(case_x,p['case_side_y'],p['z_nonfeed']-e)))
    angle=math.radians(p['case_draft_angle']);ty=p['case_side_y']-radius*math.sin(angle)
    tx=case_x+radius*math.cos(angle);bottom=p['bottom_y']+e
    end_x=tx+(bottom-ty)*math.tan(angle);outside=intervals[0][0]-e
    draft=prism([(outside,ty),(tx,ty),(end_x,bottom),(outside,bottom)],p['z_nonfeed']-e,p['z_feed']+e,'Z')
    land=case_locating_land(p,inner[0]);envelope=cut(union([side_clearance,draft]),land)
    limits=box_bounds(intervals[0][0]-p['end_wall'],intervals[-1][1]+p['lower_joint_projection']+e,p['axle_y']-p['boss_radius']-p['crown_height'],p['bottom_y']+p['platform_depth'],p['z_nonfeed'],p['z_feed'])
    features=[]
    def add(name,tool,drivers):
        nonlocal shape
        tool=norm(cut(tool,envelope).intersect(limits));assert tool.is_valid
        before=shape.volume;shape=union([shape,handed(tool)],names=['body',name])
        assert shape.is_valid and len(shape.solids())==1,(name,'invalid or disconnected')
        features.append(dict(name=name,operation='union',added_mm3=shape.volume-before,drivers=drivers))
        print(side,name,round(shape.volume-before,3),flush=True)

    # Wall feet. The sloped edge is the support webs' existing rear-corner clearance line
    # (front_support_y at the bed face, front_support_angle to the floor); the wall is
    # square to the bed above it. The quad's inner edges lie inside the existing wall.
    foot=[(y0,front),(support_y,front),(p['bottom_y'],front+run),(y0,front+run)]
    for name,(a,b) in (('end wall foot',intervals[0]),('middle wall foot',intervals[1])):
        add(name,prism(foot,a,b),dict(x=[a,b],y_top=y0,y_bed=support_y,slope_deg_from_print_axis=p['front_support_angle'],z_run=run))
    a,b=intervals[2]
    seam=[(y0,front),(d['seam_foot_y'],front),(d['seam_foot_top_y'],front+d['seam_foot_run']),(y0,front+d['seam_foot_run'])]
    add('seam wall foot',prism(seam,a,b),dict(x=[a,b],y_top=y0,y_bed=d['seam_foot_y'],run=d['seam_foot_run']))

    # Widened web feet: 45 degree loft from +widen at the bed to the nominal web at Z front+taper.
    # Y range is the web's own bed-face extent (front lip to the corner-clearance start).
    cx=x+w/2;rib_a=cx+p['rib_center_offset']-p['rib_width']/2
    webs=[('end web',inner[0],inner[0]+p['end_web_width']),('cap-bay rib',rib_a,rib_a+p['rib_width']),
          ('middle wall flanges',inner[1],inner[2])]
    if p['aux_support_web']:
        s0=inner[2]+p['aux_web_wall_offset'];webs.append(('aux web',s0,s0+p['rib_width']))
    ylo,yhi=p['front_lip_y'],support_y;wd=d['web_widen_mm'];tz=d['web_taper_run_mm']
    for name,a,b in webs:
        loft=Solid.make_loft([rect_wire(a-wd,b+wd,ylo,yhi,front),rect_wire(a,b,ylo,yhi,front+tz)],ruled=True)
        assert loft.is_valid
        add(name+' widened foot',loft,dict(x=[a,b],widen=wd,taper_run=tz,y=[ylo,yhi]))

    assert shape.is_valid and len(shape.solids())==1

    label=f'{side}_body_pocket_cut5_v5';v,t=triangulate(shape)
    gate=rfid_no_addition(out,side,label,v,t)
    base=out/'artifacts'/label;export_step(shape,str(base)+'.step');export_3mf(shape,str(base)+'.3mf',mesh=(v,t));np.savez_compressed(str(base)+'_display.npz',v=v,t=t)
    reimport=import_step(str(base)+'.step');assert reimport.is_valid and len(reimport.solids())==1
    # Bed-face metrics in the print frame.
    import manifold3d as mf
    body=mf.Manifold(mf.Mesh(v.astype(np.float32),t.astype(np.uint32)))
    bed={}
    for z in (0.15,1,2,3,6,10):
        cs=body.slice(front+z);bed[f'{z}']=dict(area_mm2=cs.area(),regions=len(cs.decompose()))
    report=dict(side=side,status='V5_CANDIDATE',parameters=d,source=str(source),source_sha256=sha(source),features=features,
                initial_volume_mm3=start_volume,volume_mm3=shape.volume,native_valid=True,native_solids=1,
                export_roundtrip_volume_error_mm3=reimport.volume-shape.volume,rfid_gate=gate,bed_face=bed,
                drivers=dict(nose_y=nose_y,foot_y_top=y0,front_support_y=support_y,front_support_angle=p['front_support_angle'],corner_run_z=run,front_lip_y=p['front_lip_y']),
                elapsed_s=time.time()-t0,files={q.name:sha(q) for q in out.glob('artifacts/'+label+'*')})
    (out/'reports'/f'{side}-v5-build.json').write_text(json.dumps(report,indent=2))
    print('DONE',side,round(report['elapsed_s'],1),'bed',bed,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('side',choices=['right','left']);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--source',default=None)
    a=ap.parse_args();build(a.side,a.out.resolve(),a.source)
