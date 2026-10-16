"""Convert the supplied mesh to a single faceted STEP solid.

This conversion adds no geometric resolution and does not fit analytic curves.
A 0.00001 mm topology cleanup resolves mesh-export degeneracies; original
vertices remain fixed, and output surfaces are checked after STEP read-back.
Run with the repository's CAD dependencies: python rings/export_step.py OUTPUT
"""
from pathlib import Path
import gc
import hashlib
import json
import sys
import struct
import tempfile
import argparse
import concurrent.futures
import gzip
import multiprocessing

import numpy as np
import manifold3d as mf
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SHELL
from OCP.BRep import BRep_Tool
from build123d import Solid, export_step, import_step

CLEANUP_TOLERANCE_MM = 1e-5


def triangle_key(points):
    return tuple(sorted(tuple(np.round(p, 7)) for p in points))


def convert(path, out):
    records = np.frombuffer(path.read_bytes(), dtype=np.dtype([
        ('normal', '<f4', 3), ('points', '<f4', (3, 3)), ('attribute', '<u2')
    ]), offset=84)
    original_points = records['points'].astype(float)
    vertices, indices = np.unique(original_points.reshape(-1, 3), axis=0, return_inverse=True)
    mesh = mf.Mesh64(vertices, indices.reshape(-1, 3).astype(np.uint64))
    mesh.merge()
    original = mf.Manifold(mesh)
    assert original.status() == mf.Error.NoError
    cleaned = original.simplify(CLEANUP_TOLERANCE_MM)
    assert cleaned.status() == mf.Error.NoError
    clean_mesh = cleaned.to_mesh64()
    clean_vertices = np.asarray(clean_mesh.vert_properties)[:, :3]
    assert set(map(tuple, clean_vertices)) <= set(map(tuple, vertices))
    points = clean_vertices[np.asarray(clean_mesh.tri_verts)]
    volume = original.volume()
    difference_volume = (original - cleaned).volume() + (cleaned - original).volume()
    volume_budget = original.surface_area() * CLEANUP_TOLERANCE_MM
    assert abs(difference_volume) < volume_budget
    # Exporting a subset of original float32 vertices introduces no new rounding.
    clean_records = np.zeros(len(points), dtype=records.dtype)
    clean_records['points'] = points
    source = TopoDS_Shape()
    with tempfile.TemporaryDirectory() as temporary:
        prepared = Path(temporary) / 'prepared.stl'
        prepared.write_bytes(b'Numerical topology cleanup'.ljust(80, b' ') +
                             struct.pack('<I', len(points)) + clean_records.tobytes())
        assert StlAPI_Reader().Read(source, str(prepared))
    sewing = BRepBuilderAPI_Sewing(1e-7)
    sewing.Add(source)
    sewing.Perform()
    explorer = TopExp_Explorer(sewing.SewedShape(), TopAbs_SHELL)
    shells = []
    while explorer.More():
        shells.append(TopoDS.Shell(explorer.Current()))
        explorer.Next()
    assert len(shells) == 1 and BRep_Tool.IsClosed_s(shells[0])
    shape = Solid(BRepBuilderAPI_MakeSolid(shells[0]).Solid())
    assert shape.is_valid and len(shape.solids()) == 1
    destination = out / path.with_suffix('.step').name
    export_step(shape, destination)
    delivered = import_step(destination)
    assert delivered.is_valid and len(delivered.solids()) == 1
    expected = {triangle_key(t) for t in points}
    actual = {triangle_key([[v.X, v.Y, v.Z] for v in f.vertices()])
              for f in delivered.faces()}
    assert actual == expected and len(delivered.faces()) == len(points)
    volume_error = abs(delivered.volume - volume)
    assert volume_error < volume_budget
    bbox = delivered.bounding_box()
    bounds = np.array([[bbox.min.X, bbox.min.Y, bbox.min.Z],
                       [bbox.max.X, bbox.max.Y, bbox.max.Z]])
    mesh_bounds = np.array([original_points.min(axis=(0, 1)), original_points.max(axis=(0, 1))])
    bounds_error = float(np.max(abs(bounds - mesh_bounds)))
    assert bounds_error < 1e-6
    row = dict(file=destination.name, representation='faceted BRep with numerical topology cleanup; no smoothing or added resolution',
               valid=True, solids=1, faces=len(points), source_triangles=len(original_points),
               cleanup_tolerance_mm=CLEANUP_TOLERANCE_MM,
               all_exported_triangles_match_cleaned_mesh_to_mm=1e-7,
               cleaned_vertices_subset_of_original=True,
               source_cleanup_symmetric_difference_mm3=difference_volume,
               volume_comparison_budget_mm3=volume_budget,
               volume_mm3=delivered.volume, volume_difference_mm3=volume_error,
               bounds_mm=bounds.tolist(), bounds_difference_mm=bounds_error,
               stl_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
               step_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
    print(json.dumps(row), flush=True)
    return row


def batch_convert(arguments):
    path, out, compress = arguments
    checkpoint = Path(out)/(Path(path).stem+'-check.json')
    if checkpoint.exists():
        row = json.loads(checkpoint.read_text())
        assert row['stl_sha256'] == hashlib.sha256(Path(path).read_bytes()).hexdigest()
        saved = Path(out)/row['file']
        key = 'compressed_sha256' if compress else 'step_sha256'
        assert hashlib.sha256(saved.read_bytes()).hexdigest() == row[key]
        return row
    row = convert(Path(path), Path(out))
    if compress:
        step = Path(out) / row['file']
        packed = step.with_suffix('.step.gz')
        with packed.open('wb') as stream:
            with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0) as zipped:
                zipped.write(step.read_bytes())
        assert gzip.decompress(packed.read_bytes()) == step.read_bytes()
        row['file'] = packed.name
        row['compressed_sha256'] = hashlib.sha256(packed.read_bytes()).hexdigest()
        step.unlink()
    (Path(out)/(Path(path).stem+'-check.json')).write_text(json.dumps(row, indent=2)+'\n')
    gc.collect()
    return row


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--input', type=Path, default=Path(__file__).resolve().parent/'models')
    parser.add_argument('--gzip', action='store_true', help='Compress large faceted STEPs after read-back')
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--resume', action='store_true', help='Reuse only completed, hash-verified conversions')
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=args.resume)
    paths = sorted(args.input.glob('*.stl'))
    assert paths
    arguments = [(str(p), str(out), args.gzip) for p in paths]
    if args.workers == 1:
        rows = [batch_convert(a) for a in arguments]
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers,
                mp_context=multiprocessing.get_context('spawn')) as pool:
            rows = list(pool.map(batch_convert, arguments))
    (out / 'STEP-CHECKS.json').write_text(json.dumps(rows, indent=2) + '\n')
