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
         flange_radial_reach=10.25,
         maximum_preserved_radius=22.5, preserved_region_overlap=0.1,
         circular_segments=256, corners=5, phase_degrees=90.0)
# Flange sets in mm: the cap-side lip and the gear-side flange are both printed on Z0.
# humebeam's 0.4 mm source lip is too thin to survive bed removal and handling on the cap
# side, so "normal" thickens both; "skinny" keeps 0.4 mm on both sides for tight holders.
FLANGE_SETS = {'normal': dict(cap=0.6, gear=2.2), 'skinny': dict(cap=0.4, gear=0.4)}
# Hard plastic hubs: pentagon corners cannot bite a rigid hub, so the spigot is round at a
# friction clearance and four axial fingers bow out past the hole wall and press on it.
# The fingers hold the ring in the hub when the gear shaft is pulled.
SPRING = dict(clearance=0.20, fingers=4, finger_degrees=30.0, slot=1.0, finger_thickness=1.3,
              bow=0.20, root_above_base=1.6, root_overlap=0.3, peak_fraction=0.75, minimum_core_wall=0.8)
ROOT = Path(__file__).resolve().parent


def side_names(flanges):
    return f"gear-side-{flanges['gear']:g}mm-flange", f"cap-side-{flanges['cap']:g}mm-lip"


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


def thicken(cap, base_t, preserve, reach_radius=None):
    """Grow the Z0 lip of `cap` to `base_t` and optionally widen it to `reach_radius`.

    Everything above the lip moves up by base_t - lip; the new base keeps the
    source-lip section (bore, snap ribs) as a constant prism, as the accepted
    1.5 mm gear-side flange did.
    """
    lip_t = P['lip_thickness']
    rise = base_t - lip_t
    if abs(rise) < 1e-9 and reach_radius is None:
        return cap
    box = cap.bounding_box()
    half = max(abs(x) for x in box[:2] + box[3:5]) + 30
    above = mf.Manifold.cube((2*half, 2*half, box[5]+rise+2)).translate((-half, -half, base_t))
    section = cap.slice(lip_t/2)
    if reach_radius is not None:
        section = section + (mf.CrossSection.circle(reach_radius, P['circular_segments'])
                             - mf.CrossSection.circle(reach_radius - P['flange_radial_reach'] - 0.01,
                                                      P['circular_segments']))
    body = (cap.translate((0, 0, rise)) ^ above) + section.extrude(base_t)
    # Below the shoulder the bore is the source-lip section carried through the base.
    collar = mf.Manifold.cylinder(base_t, preserve, preserve, P['circular_segments'])
    expected = cap.slice(lip_t/2).extrude(base_t) ^ collar
    assert symmetric_volume(body ^ collar, expected) < 1e-6
    return body


def build_pair(stock, size, flanges):
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
    source_cap = (stock ^ keep) + ((straight+lead)-keep) + (stock ^ lip_mask)
    assert symmetric_volume(source_cap ^ keep, stock ^ keep) < 1e-6
    gear_name, cap_name = side_names(flanges)
    parts = {gear_name: thicken(source_cap, flanges['gear'], preserve, radius+P['flange_radial_reach']),
             cap_name: thicken(source_cap, flanges['cap'], preserve)}
    for name, base_t in [(gear_name, flanges['gear']), (cap_name, flanges['cap'])]:
        rise = base_t - lip_t
        above = mf.Manifold.cube((2*(radius+15), 2*(radius+15), height+2)).translate((-radius-15, -radius-15, base_t))
        elevated_keep = keep.translate((0, 0, rise)) ^ above
        assert symmetric_volume(parts[name] ^ elevated_keep, stock.translate((0, 0, rise)) ^ elevated_keep) < 1e-6
    # Independent section radii: five corners, support circle and top lead-in.
    section = np.vstack([np.asarray(q) for q in source_cap.slice(height-lead_h-0.1).to_polygons()])
    assert abs(np.hypot(section[:, 0], section[:, 1]).max()-corner) < 1e-6
    return parts, dict(
        target_hole_mm=size, source_height_mm=height, preserved_radius_mm=preserve,
        corner_radius_mm=corner, support_radius_mm=support, top_scale=scale,
        gear_flange_od_mm=2*(radius+P['flange_radial_reach']),
        gear_flange_thickness_mm=flanges['gear'], cap_lip_thickness_mm=flanges['cap'],
        source_cap_interface_pass=True, source_interface_above_base_pass=True,
        source_base_bore_section_pass=True)


def wedge(half_degrees, r, z0, z1, phase):
    a = np.radians(np.linspace(phase - half_degrees, phase + half_degrees, 48))
    pts = np.vstack([[0, 0], np.column_stack([r*np.cos(a), r*np.sin(a)])])
    return mf.CrossSection([pts]).extrude(z1 - z0).translate((0, 0, z0))


def spring_pair(stock, size, flanges):
    """Round friction spigot with spring fingers, on the same holder core and flange sets as the pentagon pairs."""
    S, lip_t, lead_h = SPRING, P['lip_thickness'], P['lead_height']
    height = stock.bounding_box()[5]
    radius = size / 2
    support = radius - S['clearance']
    scale = (support - P['lead_radial_reduction']) / support
    preserve = min(P['maximum_preserved_radius'], support * scale - P['preserved_region_overlap'])
    r_in = support - S['finger_thickness']
    core_wall = r_in - S['slot'] - preserve
    assert core_wall >= S['minimum_core_wall'], f'{size:g} mm: no room for spring fingers outside the holder core'
    outline = mf.CrossSection.circle(support, P['circular_segments'])
    straight = outline.extrude(height-lead_h-lip_t).translate((0, 0, lip_t))
    lead = outline.extrude(lead_h, scale_top=(scale, scale)).translate((0, 0, height-lead_h))
    keep = mf.Manifold.cylinder(height+2, preserve, preserve, P['circular_segments']).translate((0, 0, -1))
    lip_mask = mf.Manifold.cube((2*(radius+5), 2*(radius+5), lip_t)).translate((-radius-5, -radius-5, 0))
    source_cap = (stock ^ keep) + ((straight+lead)-keep) + (stock ^ lip_mask)
    gear_name, cap_name = side_names(flanges)
    parts, info = {}, {}
    for name, base_t, reach in [(gear_name, flanges['gear'], radius+P['flange_radial_reach']), (cap_name, flanges['cap'], None)]:
        ring = thicken(source_cap, base_t, preserve, reach)
        top = height + base_t - lip_t
        z_root = base_t + S['root_above_base']
        lead_start = top - lead_h
        peak = radius + S['bow']
        z_peak = z_root + S['peak_fraction'] * (lead_start - z_root)
        # Finger section (r, z): straight at the root, bowing out to the peak, then down the lead-in.
        # It starts root_overlap inside the base so it joins as one solid, not along a plane.
        z0 = z_root - S['root_overlap']
        profile = [(r_in, z0), (support, z0), (support, z_root), (peak, z_peak), (peak, lead_start),
                   (support - P['lead_radial_reduction'] + 0.2, top), (r_in, top)]
        finger = mf.Manifold.revolve(mf.CrossSection([np.asarray(profile, float)]), P['circular_segments'])
        span = S['finger_degrees']/2 + np.degrees(S['slot']/support)
        behind = mf.Manifold.cylinder(top+2, r_in-S['slot'], r_in-S['slot'], P['circular_segments'])
        for i in range(S['fingers']):
            phase = 45 + 360/S['fingers']*i
            ring = ring - (wedge(span, support+2, z_root, top+1, phase) - behind)
            ring = ring + (finger ^ wedge(S['finger_degrees']/2, peak+2, z0, top, phase))
        # The holder core and snap ribs come through the finger cuts untouched.
        guard = mf.Manifold.cylinder(top+2, preserve-0.01, preserve-0.01, P['circular_segments']).translate((0, 0, -1))
        assert symmetric_volume(ring ^ guard, thicken(source_cap, base_t, preserve, reach) ^ guard) < 1e-6
        # Keep only real solids: the reference mesh can leave zero-volume slivers at the core boundary.
        pieces = [q for q in ring.decompose() if q.volume() > 1e-3]
        assert len(pieces) == 1, [q.volume() for q in pieces]
        ring = pieces[0]
        section = np.vstack([np.asarray(q) for q in ring.slice(z_peak).to_polygons()])
        assert abs(np.hypot(section[:, 0], section[:, 1]).max() - peak) < 1e-3
        parts[name] = ring
        info[name] = dict(top_mm=top, finger_root_z_mm=z_root, finger_peak_z_mm=z_peak)
    return parts, dict(target_hole_mm=size, source_height_mm=height, preserved_radius_mm=preserve,
        support_radius_mm=support, finger_peak_diameter_mm=2*(radius+S['bow']), finger_inner_radius_mm=r_in,
        core_wall_behind_slot_mm=core_wall, top_scale=scale, gear_flange_od_mm=2*(radius+P['flange_radial_reach']),
        gear_flange_thickness_mm=flanges['gear'], cap_lip_thickness_mm=flanges['cap'], fingers=info)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sizes', nargs='+', type=float, default=list(range(45, 96)))
    parser.add_argument('--set', choices=sorted(FLANGE_SETS), default='normal',
                        help='normal: 0.6 mm cap lip, 2.2 mm gear flange; skinny: 0.4 mm on both')
    parser.add_argument('--core', choices=['pentagon', 'spring'], default='pentagon',
                        help='pentagon: corners bite a cardboard hub; spring: fingers hold a hard plastic hub')
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
        flanges = FLANGE_SETS[args.set]
        pair, row = (build_pair if args.core == 'pentagon' else spring_pair)(stock, size, flanges)
        row.update(source=source.name, source_sha256=sha(source), parts=[])
        for side, body in pair.items():
            assert body.status() == mf.Error.NoError and len(body.decompose()) == 1 and body.volume() > 0
            name = f'kraken-spool-ring-{size:g}-mm-{args.core}-{side}'
            stl, three = models/(name+'.stl'), models/(name+'.3mf')
            write_stl(stl, body, f'Kraken spool ring {size:g} mm {args.core} {side}')
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
            base_t = flanges['gear'] if side.startswith('gear') else flanges['cap']
            target_height = row['source_height_mm'] + base_t - P['lip_thickness']
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
        (args.output/'VALIDATION.json').write_text(json.dumps(dict(status='PASS' if len(rows)==len(args.sizes) else 'IN_PROGRESS', expected_sizes_mm=args.sizes, core=args.core, flange_set=args.set, spring=SPRING if args.core == 'spring' else None, flanges_mm=FLANGE_SETS[args.set], parameters=P, sizes=rows), indent=2)+'\n')


if __name__ == '__main__':
    main()
