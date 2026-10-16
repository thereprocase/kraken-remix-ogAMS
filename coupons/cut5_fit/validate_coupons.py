"""Check delivered coupon STEP/3MF, independent sections and local print/path limits."""
from pathlib import Path
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "cad"))
from build123d import import_step
from mesh_ops import make_manifold
from build_coupons import audit_release, sha


def read_mesh(path):
    ns = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    with zipfile.ZipFile(path) as z:
        doc = ET.fromstring(z.read('3D/3dmodel.model'))
    assert doc.attrib['unit'] == 'millimeter'
    v = np.array([[float(n.attrib[k]) for k in ['x','y','z']]
                  for n in doc.findall('.//m:vertex',ns)])
    t = np.array([[int(n.attrib[k]) for k in ['v1','v2','v3']]
                  for n in doc.findall('.//m:triangle',ns)], dtype=np.uint64)
    return v, make_manifold(v,t)


def section_hits(mesh, axis, z):
    start, end = [0.,0.,z], [0.,0.,z]
    start[axis], end[axis] = -30., 30.
    return sorted(set(round(h.position[axis],6) for h in mesh.ray_cast(start,end)))


def main():
    cases = [('socket_1_c010',.10), ('socket_2_c015_nominal',.15), ('socket_3_c020',.20)]
    meshes, natives, rows = {}, {}, []
    for name in ['key_common']+[name for name,_ in cases]:
        path = HERE/'artifacts'/name
        native = import_step(str(path)+'.step')
        v, mesh = read_mesh(Path(str(path)+'.3mf'))
        height = 6. if name=='key_common' else 8.
        assert native.is_valid and len(native.solids()) == 1, name
        assert str(mesh.status()).endswith('NoError'), str(mesh.status())
        assert len(mesh.decompose()) == 1, name
        assert abs(native.volume-mesh.volume()) < .001, name
        assert np.max(np.abs(v.min(axis=0)-[-10.,-8.,0.])) < 1e-5
        assert np.max(np.abs(v.max(axis=0)-[10.,8.,height])) < 1e-5
        # Connected layers on a broad first layer; bridge ceiling remains explicit.
        prior = mesh.slice(.001)
        bed_area = prior.area()
        islands, overhangs = [], []
        for z in np.arange(.2,height,.2):
            section = mesh.slice(float(z))
            count = sum((piece ^ prior.offset(.2)).area()<1e-7 for piece in section.decompose())
            if count:
                islands.append(dict(z_mm=float(z),count=int(count)))
            unsupported = section-prior.offset(.2)
            if unsupported.area() > .01:
                overhangs.append(dict(z_mm=float(z),area_mm2=unsupported.area()))
            prior = section
        assert not islands and bed_area > 250, name
        rows.append(dict(part=name,status='PASS',native_valid=True,solids=1,
                         native_mesh_volume_error_mm3=abs(native.volume-mesh.volume()),
                         bounds_mm=[v.min(axis=0).tolist(),v.max(axis=0).tolist()],
                         bed_area_mm2=bed_area,unsupported_layer_islands=islands,
                         bridge_layers=overhangs))
        meshes[name] = mesh
        natives[name] = native
    key = meshes['key_common']
    fits = []
    for name, clearance in cases:
        flat = meshes[name]
        seated = flat.translate([0.,0.,3.])
        gaps, taper_gaps = [], []
        for axis in [0,1]:
            k = section_hits(key,axis,4.2)
            s = section_hits(seated,axis,4.2)
            assert len(k)==2 and len(s)==4
            assert abs(k[1]-k[0]-6.) < 1e-5
            assert abs(s[2]-s[1]-(6.+2*clearance)) < 1e-5
            gaps.extend([k[0]-s[1],s[2]-k[1]])
            k = section_hits(key,axis,3.3)
            s = section_hits(seated,axis,3.3)
            assert abs(k[1]-k[0]-7.) < 1e-5
            taper_gaps.extend([k[0]-s[1],s[2]-k[1]])
        assert max(abs(g-clearance) for g in gaps) < 1e-5
        assert max(abs(g) for g in taper_gaps) < 1e-5
        roof_hits = flat.ray_cast([0.,0.,-1.],[0.,0.,10.])
        depths = sorted(h.position[2] for h in roof_hits)
        assert len(depths)==2 and abs(depths[0]-(3.+clearance)) < 1e-5
        sweep = [abs((key ^ seated.translate([0.,0.,float(z)])).volume())
                 for z in np.linspace(0.,4.,41)]
        # Independently check native STEP contacts. Separately rounded mesh
        # facets can leave a minute film at the exact zero-gap seating datum.
        native_sweep = []
        for z in [0.,.1,1.,3.2,4.]:
            overlap = natives['key_common'].intersect(natives[name].translate((0.,0.,3.+z)))
            native_sweep.append(abs(overlap.volume) if overlap is not None else 0.)
        assert max(native_sweep) < 1e-7
        assert max(sweep) < .001  # Same mesh intersection budget as production cut5.
        blocks = []
        for axis in [0,1]:
            for sign in [-1,1]:
                offset=[0.,0.,0.]; offset[axis]=sign*.05
                blocks.append((key ^ seated.translate(offset)).volume())
        assert min(blocks) > .001
        down = (key ^ seated.translate([0.,0.,-.05])).volume()
        assert down > .001
        fits.append(dict(socket=name,status='PASS',four_running_gaps_mm=gaps,
                         four_seated_taper_gaps_mm=taper_gaps,
                         socket_depth_mm=depths[0],roof_stock_mm=depths[1]-depths[0],
                         ceiling_bridge_span_mm=6.+2*clearance,
                         maximum_path_overlap_mm3=max(sweep),path_samples=41,
                         mesh_intersection_tolerance_mm3=.001,
                         maximum_native_path_overlap_mm3=max(native_sweep),
                         xy_005mm_obstruction_mm3=blocks,down_005mm_obstruction_mm3=down))
    # Negative control confirms the path check detects material collision.
    negative = (key ^ meshes['socket_2_c015_nominal'].translate([.5,0.,3.])).volume()
    assert negative > .1
    report = dict(status='PASS',parts=rows,fits=fits,
                  misaligned_negative_control_overlap_mm3=negative,
                  accepted_release=audit_release(),
                  scope='Coupon geometry/print orientation only; no physical fit, full-body spacing or AMS capture certification.',
                  hashes={str(p.relative_to(HERE)):sha(p) for p in sorted((HERE/'artifacts').iterdir())})
    (HERE/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
