"""v5 drop-in front bar: the accepted cut5 split, with U-slots open to the bar's floor-side (+Y) edge in place of the
blind key sockets. The body keys are unchanged (same key solid as feed_end_insert.key_pair), so v4-key bodies stay
compatible. Running clearance 0.30 mm per side (owner's P1S fit ladder, 2026-10-28); zero-gap 45 degree seat tapers on
the two X flanks and the closed (-Y) flank.
"""
from pathlib import Path
import argparse,hashlib,json,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parent;FULL=ROOT.parent
sys.path.insert(0,str(FULL))
from build123d import Solid,Wire,Edge,Face,Compound,Plane,import_step,export_step
from mechanical_body import resolve_design,norm,union,cut
from native_features import box_bounds,export_3mf,triangulate
from feed_end_insert import INSERT,rail_wire,key_pair
import manifold3d as mf

SLOT=dict(fit_clearance=0.30,top_clearance=0.70,reach=25.0)
# fit_clearance: running clearance on the two X flanks. top_clearance: vertical clearance above the key (owner
# 2026-10-28: the bar must never hang on the keys above the tub floor; it bottoms on the box floor and can be pushed
# a hair past nominal by hand). reach: slot tool extends this far past the platform underside.
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def u_wire(cx,p,d,z,xoff,topoff,ybig):
    """Rectangle around the key, extended to ybig on the +Y (floor) side. xoff widens the two X flanks;
    topoff sets the closed (-Y) flank below the key body top (key half-depth + topoff)."""
    cy=p['platform_y']+p['platform_depth']/2;w=d['rail_width']/2+xoff;h=d['rail_depth']/2+topoff
    pts=[(cx-w,cy-h,z),(cx+w,cy-h,z),(cx+w,ybig,z),(cx-w,ybig,z)]
    return Wire([Edge.make_line(a,b) for a,b in zip(pts,pts[1:]+pts[:1])])

def slot_pair(cx,p,d):
    """Key as released; slot = running U (0.30 on X flanks, top_clearance above the key body) plus a seat whose X
    flanks are the zero-gap 45 degree tapers and whose closed flank follows the key's root collar offset by
    top_clearance, so the bar can sit top_clearance lower than the collar-seated position and never hangs on the key."""
    key,_=key_pair(cx,p,{**d,'fit_clearance':INSERT['fit_clearance']})   # the released key, untouched
    tip=p['z_feed']-d['cut_height'];root=tip-d['rail_engagement'];collar=root+d['seating_taper'];fit=d['fit_clearance'];tc=d['top_clearance']
    ybig=p['platform_y']+p['platform_depth']+d['reach']
    running=Solid.extrude(Face(u_wire(cx,p,d,root,fit,tc,ybig)),(0,0,d['rail_engagement']+fit))
    seat=Solid.make_loft([u_wire(cx,p,d,root,d['seating_taper'],d['seating_taper']+tc,ybig),u_wire(cx,p,d,collar,0,tc,ybig)],ruled=True)
    return key,union([running,seat])

def split(original,p,d):
    stop=p['z_feed']-d['cut_height'];shoulder=stop-d['rail_engagement']
    def handed(s):return s.mirror(Plane.YZ).translate((p['mirror_translation'],0,0)) if p['mirror'] else s
    bounds=original.bounding_box();margin=d['rail_width']
    lower=box_bounds(bounds.min.X-margin,bounds.max.X+margin,bounds.min.Y-margin,bounds.max.Y+margin,p['z_nonfeed']-margin,shoulder)
    upper=box_bounds(bounds.min.X-margin,bounds.max.X+margin,bounds.min.Y-margin,bounds.max.Y+margin,shoulder,p['z_feed']+margin)
    body=norm(original.intersect(lower));insert=norm(original.intersect(upper))
    setback=d['rail_width']/2+d['seating_taper']+d['rail_wall_margin']
    centers=[p['bay_datum']+p['bay_width']-setback+i*p['pitch'] for i in range(p['bay_count'])]
    keys=[]
    for center in centers:
        key,socket=slot_pair(center,p,d);key=handed(key);socket=handed(socket)
        assert cut(key,original).volume<1e-5,'Key leaves original platform envelope'
        body=union([body,key]);insert=cut(insert,socket);keys.append(key)
    for name,s in [('cut body',body),('insert',insert)]:
        assert s.is_valid and len(s.solids())==1,f'{name} must be one valid solid'
    return body,insert,keys,dict(shoulder_plane=shoulder,rail_tip=stop,rail_centers_canonical=centers)

def manifold(v,t):return mf.Manifold(mf.Mesh(np.asarray(v,np.float32),np.asarray(t,np.uint32)))

def run(side,out):
    t0=time.time();p=resolve_design(__import__(side).P);d={**INSERT,**SLOT}
    for folder in ['artifacts','reports','analysis']:(out/folder).mkdir(parents=True,exist_ok=True)
    source=FULL/'artifacts'/f'{side}_M5_gear_edit.step';original=import_step(source)
    assert original.is_valid and len(original.solids())==1
    body,insert,keys,details=split(original,p,d)
    # Keys unchanged: the split body must equal the accepted cut5 body.
    acc=np.load(FULL/'artifacts'/f'{side}_M5_gear_edit_cut5_display.npz');accm=manifold(acc['v'],acc['t'])
    bv,bt=triangulate(body);bodym=manifold(bv,bt);sym=(accm-bodym).volume()+(bodym-accm).volume()
    print(side,'split body vs accepted cut5 body: symmetric difference',round(sym,4),'mm3',flush=True)
    label=f'{side}_bar_slot_v5';base=out/'artifacts'/label
    v,t=triangulate(insert);export_step(insert,str(base)+'.step');export_3mf(insert,str(base)+'.3mf',mesh=(v,t));np.savez_compressed(str(base)+'_display.npz',v=v,t=t)
    flat=insert.translate((0,0,-details['shoulder_plane']));fv,ft=triangulate(flat)
    export_step(flat,str(base)+'_flat.step');export_3mf(flat,str(base)+'_flat.3mf',mesh=(fv,ft));np.savez_compressed(str(base)+'_flat_display.npz',v=fv,t=ft)
    # Drop-in path check: each key, lifted from seated, sweeps +Y through the open slot with no interference.
    barm=manifold(v,t);checks=[]
    for key in keys:
        kv,kt=triangulate(key);km=manifold(kv,kt)
        # seated: zero-gap tapers touch; the sweep starts 0.05 mm up the slot and goes 20 mm.
        worst=0.0
        for lift in np.arange(0.05,20.01,0.25):
            inter=(barm^km.translate((0,lift,0))).volume();worst=max(worst,inter)
        bb=km.bounding_box()
        # vertical float: the bar may go top_clearance further down than nominal (key moves -Y relative to the bar)
        free=(barm^km.translate((0,-(d['top_clearance']-0.05),0))).volume();hit=(barm^km.translate((0,-(d['top_clearance']+0.3),0))).volume()
        checks.append(dict(key_bbox=list(bb),max_interference_mm3_along_drop=worst,float_free_mm3=free,float_stop_mm3=hit,pass_=worst<1e-3 and free<1e-3 and hit>0.5))
    # Bar material under the key (floor side) at the key's X: the slot must open through it.
    for c,key in zip(checks,keys):
        bb=key.bounding_box();probe=box_bounds(bb.min.X+0.5,bb.max.X-0.5,bb.max.Y+0.05,p['bottom_y']+p['platform_depth']+5,details['shoulder_plane']+0.05,details['rail_tip']+d['fit_clearance']-0.05)
        pv,pt=triangulate(probe);left=(barm^manifold(pv,pt)).volume();c['bar_material_in_slot_below_key_mm3']=left;c['pass_']=c['pass_'] and left<1e-3
    report=dict(side=side,status='V5_BAR_CANDIDATE',parameters=d,source=str(source),source_sha256=sha(source),split=details,
                split_body_vs_accepted_cut5_symmetric_difference_mm3=sym,keys_unchanged=sym<2.0,
                bar_volume_mm3=insert.volume,bar_valid=insert.is_valid,drop_in_checks=checks,
                flat_transform='Translate Z by negative shoulder_plane; no rotation',elapsed_s=time.time()-t0,
                files={q.name:sha(q) for q in out.glob('artifacts/'+label+'*')})
    (out/'reports'/f'{side}-v5-bar.json').write_text(json.dumps(report,indent=2))
    print('DONE',side,round(report['elapsed_s'],1),'checks',[(round(c['max_interference_mm3_along_drop'],6),round(c['bar_material_in_slot_below_key_mm3'],6),c['pass_']) for c in checks],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('side',choices=['right','left']);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();run(a.side,a.out.resolve())
