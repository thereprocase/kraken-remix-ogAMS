"""Read the actual delivered STEP and 3MF files, independently of build objects."""
import hashlib,json,zipfile,xml.etree.ElementTree as ET,gc
import numpy as np
from build123d import import_step
from gear_web import ROOT,read_stl,make_manifold
results=[]
for variant in ['plain','spokes']:
 p=ROOT/'artifacts'/f'gear-{variant}'
 v,t=read_stl(p.with_suffix('.stl'));volume=make_manifold(v,t).volume()
 with zipfile.ZipFile(p.with_suffix('.3mf')) as z:doc=ET.fromstring(z.read('3D/3dmodel.model'))
 ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
 vv=np.array([[float(e.get(k)) for k in ['x','y','z']] for e in doc.findall('.//m:vertex',ns)])
 tt=np.array([[int(e.get(k)) for k in ['v1','v2','v3']] for e in doc.findall('.//m:triangle',ns)])
 assert doc.get('unit')=='millimeter' and np.array_equal(v,vv) and np.array_equal(t,tt)
 assert all(e.get('transform') is None for e in doc.findall('.//m:item',ns))
 print(variant,'3MF exact',flush=True)
 shape=import_step(p.with_suffix('.step'));bounds=shape.bounding_box()
 delta=abs(shape.volume-volume);assert shape.is_valid and len(shape.solids())==1 and delta<1e-4
 box=np.array([[bounds.min.X,bounds.min.Y,bounds.min.Z],[bounds.max.X,bounds.max.Y,bounds.max.Z]])
 assert np.max(abs(box-np.array([v.min(0),v.max(0)])))<1e-6
 # A faceted STEP must reproduce each delivered triangle as a planar face.
 # Compare triangle vertices without relying on OCCT face ordering.
 def key(points):return tuple(sorted(tuple(np.round(q,7)) for q in points))
 expected={key(v[f]) for f in t}
 actual={key([[q.X,q.Y,q.Z] for q in face.vertices()]) for face in shape.faces()}
 assert actual==expected,(len(actual),len(expected),len(expected-actual))
 row=dict(variant=variant,step_valid=True,step_solids=1,step_facets_match_stl=True,volume_difference_mm3=delta,
          three_mf_coordinates_and_triangles_exact=True,units_mm=True,orientation_unchanged=True,
          files={p.with_suffix(s).name:hashlib.sha256(p.with_suffix(s).read_bytes()).hexdigest() for s in ['.stl','.3mf','.step']})
 results.append(row);print(row,flush=True);del shape;gc.collect()
(ROOT/'analysis'/'export-readback.json').write_text(json.dumps(results,indent=2)+'\n')
