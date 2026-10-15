"""Check actual delivered STL against the exact printed reference mesh."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
import manifold3d as mf
from scipy.signal import find_peaks
from gear_web import ROOT,read_stl,make_manifold

def tri_keys(v,t):
    # Orientation-independent exact float32 vertex coordinates, not distances.
    q=v[t].astype('<f4');order=np.lexsort((q[:,:,2],q[:,:,1],q[:,:,0]),axis=1)
    q=np.take_along_axis(q,order[:,:,None],axis=1)
    return np.ascontiguousarray(q.reshape(len(q),9)).view(np.dtype((np.void,36))).ravel()

ref=json.loads((ROOT/'REFERENCE.json').read_text());v,t=read_stl(ref['path']);original=make_manifold(v,t)
tri=v[t];rad=np.linalg.norm(tri[:,:,:2],axis=2)
groups={'tooth_engagement_nonplanar':np.all(rad>=95.,axis=1)&(np.ptp(tri[:,:,2],axis=1)>1e-7),
        'hub_shaft_thread_shoulders':(tri[:,:,2].min(1)>=4.)&(tri[:,:,2].max(1)>4.),
        'bore_and_bearing_seats':np.all(rad<=14.,axis=1)}
polys=original.slice(2.0).to_polygons();outer=max(polys,key=lambda p:len(p));r=np.linalg.norm(outer,axis=1);angles=np.arctan2(outer[:,1],outer[:,0]);order=np.argsort(angles)
theta=np.linspace(-np.pi,np.pi,27400,endpoint=False);rr=np.interp(theta,angles[order],r[order],period=2*np.pi)
peaks,_=find_peaks(np.tile(rr,3),height=98.5,distance=100);peaks=peaks[(peaks>=len(rr))&(peaks<2*len(rr))]-len(rr)
assert len(peaks)==137,len(peaks)
rows=[]
for variant in ['plain','spokes']:
    path=ROOT/'artifacts'/f'gear-{variant}.stl';a,b=read_stl(path);cad=make_manifold(a,b);keys=tri_keys(a,b)
    checks=[]
    for name,mask in groups.items():
        source_keys=tri_keys(v,t[mask]);matched=np.isin(source_keys,keys)
        checks.append(dict(interface=name,source_triangles=len(source_keys),exactly_retained_triangles=int(matched.sum()),pass_exact_triangles=bool(matched.all())))
    added=cad-original;removed=original-cad
    for shape in [added,removed]:assert shape.status()==mf.Error.NoError
    # Changes are confined below the hub and inside the solid tooth rim.
    above=mf.Manifold.cube((240,240,100)).translate((-120,-120,4.000001))
    below=mf.Manifold.cube((240,240,10)).translate((-120,-120,-10.000001))
    bore=mf.Manifold.cylinder(100,14.,14.,circular_segments=360).translate((0,0,-1))
    z_added=(added^above).volume()+(added^below).volume();z_removed=(removed^above).volume()+(removed^below).volume()
    bore_change=(added^bore).volume()+(removed^bore).volume()
    rmax=0.
    for shape in [added,removed]:
        if shape.is_empty():continue
        pts=np.asarray(shape.to_mesh64().vert_properties)[:,:3];rmax=max(rmax,float(np.linalg.norm(pts[:,:2],axis=1).max()))
    section=cad.slice(3.9);loops=section.to_polygons()
    row=dict(variant=variant,stl_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),interfaces=checks,
             tooth_count=137,tooth_phase_and_profile='Exact retained interface triangles; no tooth geometry generated',
             maximum_changed_radius_mm=rmax,above_or_below_disc_added_mm3=z_added,above_or_below_disc_removed_mm3=z_removed,
             bore_or_bearing_change_mm3=bore_change,added_mm3=added.volume(),removed_mm3=removed.volume(),
             disc_top_z_mm=4.,original_section_loops=len(original.slice(3.9).to_polygons()),candidate_section_loops=len(loops),
             candidate_section_area_mm2=section.area(),connected_components=len(cad.decompose()),mesh_status=str(cad.status()))
    row['status']='PASS' if all(c['pass_exact_triangles'] for c in checks) and max(z_added,z_removed,bore_change)<=1e-8 and rmax<=90.01 and len(cad.decompose())==1 else 'FAIL'
    rows.append(row);print(variant,row['status'],[(c['interface'],c['exactly_retained_triangles'],c['source_triangles']) for c in checks],rmax,'loops',len(loops),flush=True)
(ROOT/'INTERFACES.json').write_text(json.dumps(dict(reference=ref,configurations=rows,scope='Exact triangle retention on named supplied interfaces plus change-envelope Boolean checks; does not certify unknown physical hardware.'),indent=2)+'\n')
assert all(r['status']=='PASS' for r in rows)
