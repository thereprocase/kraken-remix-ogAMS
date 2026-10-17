"""Exact source STL I/O and explicit input discovery; no mesh fitting."""
from pathlib import Path
import os
import numpy as np
ROOT=Path(__file__).resolve().parent
def source(name):
 candidates={
  "gear":[ROOT.parent/"gear/models/gear-spokes.stl",ROOT.parent/"gear_web_20261015/artifacts/gear-spokes.stl"],
  "nut":[ROOT/"reference/nut.stl"],
  "tool":[ROOT/"reference/tool.npz"]
 }[name]
 if os.environ.get("KRAKEN_"+name.upper()):return Path(os.environ["KRAKEN_"+name.upper()])
 for p in candidates:
  if p.exists():return p
 raise FileNotFoundError("Set KRAKEN_"+name.upper()+" to the retained source; see SOURCES.json")

def write_stl(v,t,path):
    tri=v[t];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-30)
    data=np.zeros(len(t),dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')]))
    data['normal']=norm;data['vertices']=tri
    header=b'Kraken reloadable spool prototype; added or assembled geometry'.ljust(80,b' ')
    path.write_bytes(header+len(t).to_bytes(4,'little')+data.tobytes())

def read_stl(path):
    raw=Path(path).read_bytes();n=int.from_bytes(raw[80:84],'little')
    d=np.frombuffer(raw,dtype=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]),count=n,offset=84)
    v,t=np.unique(d['v'].reshape(-1,3).astype(float),axis=0,return_inverse=True)
    return v,t.reshape(-1,3)
