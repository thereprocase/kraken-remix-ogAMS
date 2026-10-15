"""Removable feed-end extension of the accepted native body.

No source mesh or recovered outline is used. The original analytic features
are split at one plane; two instances of a rectangular key with a tapered seat locate the end.
All coordinates derive from the platform, bay and feed datums.
"""
from pathlib import Path
import argparse, json
from build123d import Solid, Wire, Edge, Face, Compound, import_step, export_step
from mechanical_body import build, resolve_design, norm, union, cut
from native_features import box_bounds, export_stage, export_3mf
import numpy as np

ROOT = Path(__file__).resolve().parent
INSERT = dict(cut_height=5.0, rail_width=6.0, rail_depth=6.0,
              rail_engagement=3.0, fit_clearance=0.15,
              seating_taper=0.8, tip_lead=0.4, rail_wall_margin=4.0)


def rail_wire(cx, p, d, z, offset=0.):
    """Rectangular key profile about its centre and the platform mid-depth."""
    cy=p['platform_y']+p['platform_depth']/2
    w=d['rail_width']/2+offset;h=d['rail_depth']/2+offset
    pts=[(cx-w,cy-h,z),(cx+w,cy-h,z),(cx+w,cy+h,z),(cx-w,cy+h,z)]
    return Wire([Edge.make_line(a,b) for a,b in zip(pts,pts[1:]+pts[:1])])


def key_pair(cx,p,d):
    """One keyed pin with a 45-degree lead and matching registration collar.

    Running clearance is 0.15mm on each side. The matching root taper seats
    against the socket mouth and registers XY as the shoulder sets Z.
    """
    tip=p['z_feed']-d['cut_height'];root=tip-d['rail_engagement']
    collar=root+d['seating_taper'];lead=d['tip_lead'];fit=d['fit_clearance']
    def wire(z,offset=0):return rail_wire(cx,p,d,z,offset)
    key=Solid.make_loft([wire(root,d['seating_taper']),wire(collar),
                         wire(tip-lead),wire(tip,-lead)],ruled=True)
    running=Solid.extrude(Face(wire(root,fit)),(0,0,d['rail_engagement']+fit))
    seat=Solid.make_loft([wire(root,d['seating_taper']),wire(collar)],ruled=True)
    return key,union([running,seat])


def split_body(original,parameters,d=INSERT):
    p=resolve_design(parameters);stop=p['z_feed']-d['cut_height'];shoulder=stop-d['rail_engagement']
    assert 0<d['fit_clearance']<d['seating_taper']<d['rail_engagement']
    assert 0<d['cut_height']<p['box_clip_base_length']
    # Work in the shared canonical frame, then mirror this one feature set.
    def handed(s):
        if p['mirror']:
            from build123d import Plane
            return s.mirror(Plane.YZ).translate((p['mirror_translation'],0,0))
        return s
    bounds=original.bounding_box();margin=d['rail_width']
    lower=box_bounds(bounds.min.X-margin,bounds.max.X+margin,
                     bounds.min.Y-margin,bounds.max.Y+margin,
                     p['z_nonfeed']-margin,shoulder)
    upper=box_bounds(bounds.min.X-margin,bounds.max.X+margin,
                     bounds.min.Y-margin,bounds.max.Y+margin,shoulder,p['z_feed']+margin)
    body=norm(original.intersect(lower));insert=norm(original.intersect(upper))
    setback=d['rail_width']/2+d['seating_taper']+d['rail_wall_margin']
    centers=[p['bay_datum']+p['bay_width']-setback+i*p['pitch'] for i in range(p['bay_count'])]
    for center in centers:
        key,socket=key_pair(center,p,d);key=handed(key);socket=handed(socket)
        assert cut(key,original).volume<1e-5,'Key leaves original platform envelope'
        body=union([body,key]);insert=cut(insert,socket)
    for name,s in [('cut body',body),('insert',insert)]:
        assert s.is_valid and len(s.solids())==1, f'{name} must be one valid solid'
    assert body.bounding_box().max.Z<=stop+1e-6
    return body,insert,dict(cut_plane=stop,rail_centers_canonical=centers,
        shoulder_plane=shoulder,rail_tip=stop,body_height=stop-p['z_nonfeed'],parameters=d)


def flat_insert(insert,p,d):
    # Broad shoulder on the bed; closed key sockets require only short bridges.
    shoulder=p['z_feed']-d['cut_height']-d['rail_engagement']
    return insert.translate((0,0,-shoulder))


def export_assembly(body,insert,side,base,suffix='cut5'):
    """Two native parts; mesh union of those exact delivered print meshes.

    Avoid a second native fuse across zero-clearance seating faces: it can
    change internal coincident faces by tiny OCCT Boolean tolerances.
    """
    from mesh_ops import make_manifold
    from export_guards import rfid_no_addition
    from validation_metadata import provenance
    shapes=[]
    for part in [f'{base}_{suffix}',f'{base}_insert_{suffix}']:
        data=np.load(ROOT/'artifacts'/f'{side}_{part}_display.npz')
        shapes.append(make_manifold(data['v'],data['t']))
    assert abs((shapes[0]^shapes[1]).volume())<.001,'Delivered parts interfere'
    mesh=(shapes[0]+shapes[1]).to_mesh64()
    v=np.array(mesh.vert_properties,dtype=np.float64,order='C',copy=True)[:,:3].copy()
    t=np.array(mesh.tri_verts,dtype=np.uint64,order='C',copy=True)
    stage=f'{base}_assembled_{suffix}';shape=Compound([body,insert])
    assert shape.is_valid and len(shape.solids())==2
    gate=rfid_no_addition(ROOT,side,stage,v,t)
    path=ROOT/'artifacts'/f'{side}_{stage}'
    export_step(shape,str(path)+'.step');export_3mf(shape,str(path)+'.3mf',mesh=(v,t))
    np.savez(str(path)+'_display.npz',v=v,t=t)
    return dict(provenance=provenance(side,stage),valid=True,solids=2,
                volume_mm3=shape.volume,rfid_export_gate=gate,
                representation='Two separate native parts; mesh union of delivered bodies.')


def run(side,variant,d=INSERT,from_accepted=False):
    from right import P as RIGHT
    from left import P as LEFT
    parameters=RIGHT if side=='right' else LEFT;p=resolve_design(parameters)
    stage=('M3' if side=='right' else 'M4') if variant=='standard' else 'M5_gear_edit'
    print(f'Building {side} {stage} cut/insert',flush=True)
    original=import_step(ROOT/'artifacts'/f'{side}_{stage}.step') if from_accepted else build(parameters,stage,variant=='pocket')
    body,insert,details=split_body(original,parameters,d)
    suffix=f"cut{d['cut_height']:g}";label=f'{stage}_{suffix}'
    reports={}
    for name,s in [(label,body),(f'{stage}_insert_{suffix}',insert)]:
        print(f'Exporting {side} {name}',flush=True)
        reports[name]=export_stage(s,ROOT,side,name)
    reports[f'{stage}_assembled_{suffix}']=export_assembly(body,insert,side,stage,suffix)
    flat=flat_insert(insert,p,d);flat_label=f'{stage}_insert_flat_{suffix}'
    # Validate no-addition in assembly coordinates above, never on relocated parts.
    path=ROOT/'artifacts'/f'{side}_{flat_label}'
    export_step(flat,str(path)+'.step');v,t=export_3mf(flat,str(path)+'.3mf')
    np.savez(str(path)+'_display.npz',v=v,t=t)
    details.update(side=side,variant=variant,base_stage=stage,exports=reports,
                   flat_transform='Translate Z by negative shoulder_plane; no rotation',
                   native_added_to_original_mm3=0.,
                   native_added_basis='Keys are checked within the original native platform; all subsequent operations split or remove material.',
                   native_net_removed_from_original_mm3=original.volume-body.volume-insert.volume,
                   native_body_insert_overlap_mm3=(norm(body.intersect(insert)).volume if body.intersect(insert) is not None else 0.))
    (ROOT/'reports'/f'{side}_{label}_build.json').write_text(json.dumps(details,indent=2))
    print(json.dumps({k:v for k,v in details.items() if k!='exports'},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('side',choices=['right','left'])
    parser.add_argument('variant',choices=['standard','pocket']);parser.add_argument('--from-accepted',action='store_true')
    parser.add_argument('--cut-height',type=float,default=INSERT['cut_height'])
    parser.add_argument('--fit-clearance',type=float,default=INSERT['fit_clearance'])
    args=parser.parse_args();run(args.side,args.variant,{**INSERT,'cut_height':args.cut_height,'fit_clearance':args.fit_clearance},args.from_accepted)
