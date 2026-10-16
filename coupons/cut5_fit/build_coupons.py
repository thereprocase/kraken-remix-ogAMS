"""Isolated cut5 fit samples; never writes accepted bodies or their manifest."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "cad"))

from build123d import export_step
from feed_end_insert import INSERT, key_pair
from mechanical_body import cut, union
from native_features import box_bounds, export_3mf

P = dict(width=20.0, depth=16.0, base_height=3.0,
         notch_width=1.0, notch_depth=1.0, notch_pitch=3.0)
CASES = [('socket_1_c010', 0.10, 1), ('socket_2_c015_nominal', 0.15, 2),
         ('socket_3_c020', 0.20, 3)]
EXPECTED_MANIFEST = '2e871508576ca4e7b8b694b8358af0eb499309b51a7f0e5eb1364f91ecc76cdb'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_release():
    record=json.loads((ROOT/'docs/RELEASE.json').read_text())
    for row in record['files']:
        assert sha(ROOT/row['file'])==row['sha256'], row['file']
    return dict(status='PASS', checked_files=len(record['files']),
                source_manifest_sha256=record['source_manifest_sha256'])


def make_samples():
    d = dict(INSERT)
    datum = dict(platform_y=-P['depth']/2, platform_depth=P['depth'],
                 z_feed=P['base_height']+d['rail_engagement']+d['cut_height'])
    half_x, half_y = P['width']/2, P['depth']/2
    key, _ = key_pair(0., datum, d)
    base = box_bounds(-half_x, half_x, -half_y, half_y, 0., P['base_height'])
    samples = {'key_common': union([base, key])}
    insert_height = d['rail_engagement']+d['cut_height']
    for name, clearance, marks in CASES:
        _, socket = key_pair(0., datum, {**d, 'fit_clearance': clearance})
        stock = box_bounds(-half_x, half_x, -half_y, half_y, 0., insert_height)
        sample = cut(stock, socket.translate((0., 0., -P['base_height'])))
        # Countable edge notches identify the test without fonts or bed-side text.
        # They lie outside the joint and do not change its shoulder or stiffness locally.
        for i in range(marks):
            x = (i-(marks-1)/2)*P['notch_pitch']
            notch = box_bounds(x-P['notch_width']/2, x+P['notch_width']/2,
                               half_y-P['notch_depth'], half_y+P['notch_depth'],
                               0., insert_height)
            sample = cut(sample, notch)
        samples[name] = sample
    return samples


def main():
    before = audit_release()
    outputs = HERE / 'artifacts'
    outputs.mkdir(exist_ok=True)
    parts = []
    for name, shape in make_samples().items():
        assert shape.is_valid and len(shape.solids()) == 1, name
        path = outputs / name
        export_step(shape, str(path)+'.step')
        export_3mf(shape, str(path)+'.3mf')
        parts.append(dict(name=name, native_volume_mm3=shape.volume,
                          valid=True, solids=1))
    report = dict(parts=parts, coupon_parameters=P, joint_parameters=INSERT,
                  cases=CASES, accepted_release_before=before,
                  accepted_release_after=audit_release(),
                  joint_source_sha256=sha(ROOT/'cad/feed_end_insert.py'))
    (HERE/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
