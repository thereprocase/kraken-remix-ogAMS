"""Real geometry, display-only exploded transforms and capped axial section."""
import sys,json
from pathlib import Path
import numpy as np
import manifold3d as mf
ROOT=Path(__file__).resolve().parent;
from source_mesh import read_stl,source
from mesh_tools import make_manifold
parts={'gear':source('gear'),'backing-sleeve':ROOT/'artifacts/backing-sleeve-assembled.npz','removable-flange':ROOT/'artifacts/removable-flange-assembled.npz','stock-nut':ROOT/'artifacts/nut-assembled.npz'}
for mode in ('assembled','exploded','section'):
 entries=[]
 for name,path in parts.items():
  if mode=='section':
   if path.suffix=='.stl':v,t=read_stl(path)
   else:d=np.load(path);v,t=d['v'],d['t']
   m=make_manifold(v,t)^mf.Manifold.cube((240,120,160)).translate((-120,0,-20))
   mesh=m.to_mesh64();dest=ROOT/'renders'/f'{name}-section.npz';np.savez_compressed(dest,v=np.asarray(mesh.vert_properties)[:,:3],t=mesh.tri_verts);path=dest
  dz={'gear':0,'backing-sleeve':20,'removable-flange':90,'stock-nut':120}[name] if mode=='exploded' else 0
  color=[.98,.63,.28] if name in ('backing-sleeve','removable-flange') else [.36,.64,.69]
  entries.append({'mesh':str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),'color':color,'transform':[[1,0,0,0],[0,0,-1,-dz],[0,1,0,0],[0,0,0,1]]})
 scene={'title':'Reloadable Kraken spool — '+mode,'subtitle':'Two added parts • unchanged eight-spoke gear and stock nut','caption':('Display-only axial separation; refill cardboard omitted for clarity.' if mode=='exploded' else 'Nominal 62.4 mm refill gap. Concept verification; physical core fit unverified.'),'camera':{'yaw':-.75,'pitch':.6,'zoom':.92},'parts':entries}
 if mode=='section':scene['subtitle']='Capped half-section through the axis; actual retained thread geometry'
 (ROOT/f'{mode}.scene.json').write_text(json.dumps(scene,indent=2)+'\n')
