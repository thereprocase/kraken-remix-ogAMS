"""Verify the release hashes and, optionally, a fresh native rebuild.

This is a reproduction check against accepted exports, not new hardware or
physical-fit qualification. The original source-based checks are documented.
"""
from pathlib import Path
import argparse,hashlib,json,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent

def mesh(path):
 import numpy as np
 import manifold3d as mf
 with zipfile.ZipFile(path) as archive:doc=ET.fromstring(archive.read('3D/3dmodel.model'))
 ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
 assert doc.get('unit')=='millimeter'
 assert all(item.get('transform') is None for item in doc.findall('.//m:item',ns))
 v=np.array([[float(e.get(k)) for k in ['x','y','z']] for e in doc.findall('.//m:vertex',ns)])
 t=np.array([[int(e.get(k)) for k in ['v1','v2','v3']] for e in doc.findall('.//m:triangle',ns)],dtype=np.uint64)
 raw=mf.Mesh64(v,t);raw.merge();shape=mf.Manifold(raw)
 assert shape.status()==mf.Error.NoError and len(shape.decompose())==1
 return shape

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path)
 p.add_argument('--download',type=Path,action='append',default=[],help='Verify a downloaded GitHub Release asset; may be repeated')
 args=p.parse_args()
 count=0
 for line in (ROOT/'SHA256SUMS').read_text().splitlines():
  digest,name=line.split(None,1);path=ROOT/name
  assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,f'Hash mismatch: {name}';count+=1
 print(f'{count} release file hashes PASS',flush=True)
 if args.download:
  assets={r['file']:r for r in json.loads((ROOT/'docs/DOWNLOADS.json').read_text())['assets']}
  for path in args.download:
   assert path.name in assets,f'Unknown release asset: {path.name}'
   assert hashlib.sha256(path.read_bytes()).hexdigest()==assets[path.name]['sha256'],f'Download hash mismatch: {path.name}'
   print('Download hash PASS:',path.name,flush=True)
 if args.build is None:return
 import numpy as np
 from scipy.spatial import cKDTree
 from build123d import import_step
 rows=[]
 rebuilt_files=sorted((args.build/'models').glob('*.3mf'))
 assert len(rebuilt_files) in (2,4),'Expected a complete two-body or four-part set'
 for rebuilt in rebuilt_files:
  original=ROOT/'models'/rebuilt.name
  assert original.exists(),f'Unknown release model: {rebuilt.name}'
  name=original.stem
  a,b=mesh(original),mesh(rebuilt);sym=abs((a-b).volume())+abs((b-a).volume())
  assert sym<.1,(name,'print mesh difference',sym)
  ref=import_step(original.with_suffix('.step'));got=import_step(rebuilt.with_suffix('.step'))
  assert ref.is_valid and got.is_valid and len(ref.solids())==len(got.solids())==1
  volume_delta=abs(ref.volume-got.volume);assert volume_delta<.01,(name,volume_delta)
  av=np.array([[q.X,q.Y,q.Z] for q in ref.vertices()]);bv=np.array([[q.X,q.Y,q.Z] for q in got.vertices()])
  vertices_delta=max(cKDTree(av).query(bv)[0].max(),cKDTree(bv).query(av)[0].max())
  assert vertices_delta<1e-5,(name,vertices_delta)
  assert len(ref.faces())==len(got.faces()),(name,'native topology changed')
  row=dict(part=name,status='PASS',native_valid=True,native_solids=1,native_volume_difference_mm3=volume_delta,native_vertex_hausdorff_mm=float(vertices_delta),native_faces=len(got.faces()),print_mesh_symmetric_difference_mm3=sym)
  rows.append(row);print(row,flush=True)
 (args.build/'REPRODUCTION.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
