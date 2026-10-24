"""Pentagon cardboard-spool centering pairs using each stock holder interface.

The 55.5 mm release is preserved separately. This family covers the original
45..95 mm sizes without scaling their bores, snap ribs or insertion height.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile

import numpy as np
import manifold3d as mf
from mesh3mf import load
from rings_555 import manifold_of, write_stl

P = dict(radial_running_clearance=0.1, corner_interference=0.7,
         lead_radial_reduction=1.9, lead_height=2.0, lip_thickness=0.4,
         gear_flange_thickness=1.5, flange_radial_reach=10.25,
         maximum_preserved_radius=22.5, preserved_region_overlap=0.1,
         circular_segments=256, corners=5, phase_degrees=90.0)
ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_3mf(path, body):
    mesh = body.to_mesh64()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    vertices = ''.join(f'<vertex x="{x:.17g}" y="{y:.17g}" z="{z:.17g}"/>' for x, y, z in v)
    triangles = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in t)
    model = '<?xml version="1.0" encoding="UTF-8"?>' + \
        '<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">' + \
        '<resources><object id="1" type="model"><mesh><vertices>' + vertices + \
        '</vertices><triangles>' + triangles + '</triangles></mesh></object></resources>' + \
        '<build><item objectid="1"/></build></model>'
    content = '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    rels = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, value in [('3D/3dmodel.model', model), ('[Content_Types].xml', content), ('_rels/.rels', rels)]:
            info = zipfile.ZipInfo(name, (2026, 10, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, value)


def read_stl(path):
    records = np.frombuffer(path.read_bytes(), dtype=[('n', '<f4', 3),
        ('p', '<f4', (3, 3)), ('a', '<u2')], offset=84)
    v, index = np.unique(records['p'].reshape(-1, 3), axis=0, return_inverse=True)
    return manifold_of(v, index.reshape(-1, 3))


def symmetric_volume(a, b):
    return abs((a-b).volume()) + abs((b-a).volume())


def build_pair(stock, size):
    height = stock.bounding_box()[5]
    radius = size / 2
    support = radius - P['radial_running_clearance']
    corner = radius + P['corner_interference']
    scale = (corner - P['lead_radial_reduction']) / corner
    # At the smallest size, the outer lead must not be blocked by retained stock.
    # Keep the complete source bore and snap system inside a cylindrical envelope.
    preserve = min(P['maximum_preserved_radius'], support * scale - P['preserved_region_overlap'])
    assert preserve > 20.3, 'Insufficient room to preserve the supplied holder interface'
    angles = np.radians(P['phase_degrees'] + 360 / P['corners'] * np.arange(P['corners']))
    polygon = mf.CrossSection([np.column_stack([corner*np.cos(angles), corner*np.sin(angles)])])
    outline = polygon + mf.CrossSection.circle(support, P['circular_segments'])
    lip_t, lead_h = P['lip_thickness'], P['lead_height']
    straight = outline.extrude(height-lead_h-lip_t).translate((0, 0, lip_t))
    lead = outline.extrude(lead_h, scale_top=(scale, scale)).translate((0, 0, height-lead_h))
    keep = mf.Manifold.cylinder(height+2, preserve, preserve, P['circular_segments']).translate((0, 0, -1))
    lip_mask = mf.Manifold.cube((2*(radius+5), 2*(radius+5), lip_t)).translate((-radius-5, -radius-5, 0))
    cap = (stock ^ keep) + ((straight+lead)-keep) + (stock ^ lip_mask)
    flange_t = P['gear_flange_thickness']
    rise = flange_t-lip_t
    raised = cap.translate((0, 0, rise))
    above_mask = mf.Manifold.cube((2*(radius+15), 2*(radius+15), height+2)).translate((-radius-15, -radius-15, flange_t))
    outer = mf.CrossSection.circle(radius+P['flange_radial_reach'], P['circular_segments'])
    inner = mf.CrossSection.circle(radius-0.01, P['circular_segments'])
    flange = (cap.slice(lip_t/2) + (outer-inner)).extrude(flange_t)
    gear = (raised ^ above_mask) + flange
    assert symmetric_volume(cap ^ keep, stock ^ keep) < 1e-6
    elevated_keep = keep.translate((0, 0, rise)) ^ above_mask
    assert symmetric_volume(gear ^ elevated_keep, stock.translate((0, 0, rise)) ^ elevated_keep) < 1e-6
    # Below the shoulder, retain the accepted flange construction: constant
    # source-lip section through the thicker flange, not a scaled axial bore.
    collar_mask = mf.Manifold.cylinder(flange_t, preserve, preserve, P['circular_segments'])
    expected_collar = stock.slice(lip_t/2).extrude(flange_t) ^ collar_mask
    assert symmetric_volume(gear ^ collar_mask, expected_collar) < 1e-6
    # Independent section radii: five corners, support circle and top lead-in.
    section = np.vstack([np.asarray(q) for q in cap.slice(height-lead_h-0.1).to_polygons()])
    assert abs(np.hypot(section[:, 0], section[:, 1]).max()-corner) < 1e-6
    return {'cap-side': cap, 'gear-side-1.5mm-flange': gear}, dict(
        target_hole_mm=size, source_height_mm=height, preserved_radius_mm=preserve,
        corner_radius_mm=corner, support_radius_mm=support, top_scale=scale,
        gear_flange_od_mm=2*(radius+P['flange_radial_reach']),
        source_cap_interface_pass=True, source_gear_interface_above_flange_pass=True,
        source_flange_bore_section_pass=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sizes', nargs='+', type=float, default=list(range(45, 96)))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    models = args.output / 'models'; models.mkdir()
    rows = []
    for size in args.sizes:
        # A fractional size keeps the holder interface of the next smaller stock ring.
        source = ROOT / 'reference' / f'kraken-spool-ring-{int(size)}-mm-100.3mf'
        v, t = load(source)
        shift = np.r_[(v.min(0)+v.max(0))[:2]/2, v[:, 2].min()]
        stock = manifold_of(v-shift, t)
        assert stock.status() == mf.Error.NoError and len(stock.decompose()) == 1
        pair, row = build_pair(stock, size)
        row.update(source=source.name, source_sha256=sha(source), parts=[])
        for side, body in pair.items():
            assert body.status() == mf.Error.NoError and len(body.decompose()) == 1 and body.volume() > 0
            name = f'kraken-spool-ring-{size:g}-mm-pentagon-{side}'
            stl, three = models/(name+'.stl'), models/(name+'.3mf')
            write_stl(stl, body, f'Kraken spool ring {size:g} mm pentagon {side}')
            write_3mf(three, body)
            delivered = read_stl(stl)
            vv, tt = load(three); precise = manifold_of(vv, tt)
            assert delivered.status() == precise.status() == mf.Error.NoError
            assert len(delivered.decompose()) == len(precise.decompose()) == 1
            error = symmetric_volume(body, delivered)
            assert error < 0.02
            assert symmetric_volume(body, precise) < 1e-6
            bounds = np.array(body.bounding_box()).reshape(2, 3)
            assert abs(bounds[0, 2]) < 1e-7
            target_height = row['source_height_mm'] + (P['gear_flange_thickness']-P['lip_thickness'] if side.startswith('gear') else 0)
            assert abs(bounds[1, 2]-target_height) < 1e-6
            # The exported source region is checked again after STL quantization.
            guard = mf.Manifold.cylinder(target_height+2, row['preserved_radius_mm']-0.01,
                row['preserved_radius_mm']-0.01, P['circular_segments']).translate((0, 0, -1))
            interface_error = symmetric_volume(body ^ guard, delivered ^ guard)
            assert interface_error < 0.01
            row['parts'].append(dict(stem=name, status='PASS', mesh_components=1,
                volume_mm3=body.volume(), bounds_mm=bounds.tolist(),
                exported_stl_symmetric_difference_mm3=error,
                exported_protected_region_difference_mm3=interface_error,
                files={p.name: sha(p) for p in [stl, three]}))
        rows.append(row)
        print(f'{size:g}', 'both parts PASS', flush=True)
        (args.output/'VALIDATION.json').write_text(json.dumps(dict(status='PASS' if len(rows)==len(args.sizes) else 'IN_PROGRESS', expected_sizes_mm=args.sizes, parameters=P, sizes=rows), indent=2)+'\n')


if __name__ == '__main__':
    main()
