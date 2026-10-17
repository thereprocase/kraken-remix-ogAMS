"""Pack unchanged NPZ/binary-STL geometry into the reusable cel renderer."""
from pathlib import Path
import argparse,hashlib,json,shutil,struct
import numpy as np
from mesh_style import feature_edges,smooth_normals

def read(path):
 if path.suffix.lower()=='.npz':
  with np.load(path,allow_pickle=False) as d:return d['v'].astype(float),d['t'].astype(np.uint32)
 raw=path.read_bytes()
 if path.suffix.lower()!='.stl' or len(raw)<84:raise ValueError('Use NPZ with v/t arrays or binary STL')
 n=struct.unpack_from('<I',raw,80)[0]
 if len(raw)!=84+50*n:raise ValueError('STL must be binary')
 a=np.ndarray(n,dtype=np.dtype([('n','<f4',3),('v','<f4',(3,3)),('attr','<u2')]),buffer=raw,offset=84)
 v,t=np.unique(a['v'].reshape(-1,3),axis=0,return_inverse=True);return v.astype(float),t.reshape(-1,3).astype(np.uint32)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('scene',type=Path);ap.add_argument('out',type=Path);args=ap.parse_args()
 spec=json.loads(args.scene.read_text());args.out.mkdir(parents=True,exist_ok=True);parts=[];inputs=[]
 for i,part in enumerate(spec['parts']):
  path=(args.scene.parent/part['mesh']).resolve();v,t=read(path)
  if v.ndim!=2 or v.shape[1]!=3 or t.ndim!=2 or t.shape[1]!=3 or not np.isfinite(v).all() or t.max()>=len(v):raise ValueError('Invalid mesh arrays')
  transform=np.asarray(part.get('transform',np.eye(4)),dtype=float)
  if transform.shape!=(4,4) or not np.allclose(transform[3],[0,0,0,1]):raise ValueError('Expected affine4x4 transform')
  if np.linalg.det(transform[:3,:3])<=0:raise ValueError('Reflections require explicit mesh winding handling before rendering')
  v=(np.c_[v,np.ones(len(v))]@transform.T)[:,:3];e=feature_edges(v,t);n=smooth_normals(v,t)
  name=f'part-{i}.bin';blob=v.astype('<f4').tobytes()+t.astype('<u4').tobytes()+n.astype('<f4').tobytes()+e.astype('<u4').tobytes();(args.out/name).write_bytes(blob)
  parts.append(dict(file=name,vertices=len(v),triangles=len(t),edges=len(e),color=part.get('color',[.36,.64,.69])))
  inputs.append(dict(mesh=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),transform=transform.tolist(),vertices=len(v),triangles=len(t)))
 scene={k:spec[k] for k in ['title','subtitle','caption','camera'] if k in spec};scene['parts']=parts
 (args.out/'scene.json').write_text(json.dumps(scene,indent=2));(args.out/'inputs.json').write_text(json.dumps(inputs,indent=2))
 shutil.copy2(Path(__file__).resolve().parents[1]/'assets/viewer.html',args.out/'index.html')
 print(args.out.resolve())
if __name__=='__main__':main()
