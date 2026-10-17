from pathlib import Path
import sys,json,hashlib
import numpy as np
from build123d import import_step,Compound,Plane,Solid
R=Path(__file__).resolve().parent;B=R.parents[1];sys.path.insert(0,str(B))
from mesh_tools import triangulate,make_manifold
p=json.loads((B/'parameters.json').read_text());build=json.loads((B/'analysis/build.json').read_text());a=R/'artifacts'
report={}
for part in ['backing-sleeve-keyless','removable-flange-stiff-annulus']:
 data=np.load(a/(part+'.npz'));v,t=data['v'],data['t'];edges=np.sort(np.concatenate((t[:,[0,1]],t[:,[1,2]],t[:,[2,0]])),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True);assert (counts==2).all()
 report[part]={'triangles':len(t),'closed_edges':True,'bed_min_z':float(v[:,2].min())}
upper=import_step(a/'removable-flange-stiff-annulus-installed.step');v,t=triangulate(upper);shift=np.array(build['removable-flange']['assembly_translation']);m=make_manifold(v+shift,t)
np.savez_compressed(a/'removable-flange-stiff-annulus-assembled.npz',v=v+shift,t=t)
collisions={}
for name,path in [('nut',R.parent/'keyless-stiff-annulus/reference/nut-assembled.npz'),('tool',R.parent/'keyless-stiff-annulus/reference/tool-assembled.npz')]:
 d=np.load(path);other=make_manifold(d['v']+np.array([0,0,.85]),d['t']);volume=(m^other).volume();collisions[name]=volume
 # Source mesh nut/plate contact has a pre-existing float32 artefact.
 assert volume<.02,(name,volume)
from source_mesh import source,read_stl
gv,gt=read_stl(source('gear'));gear=make_manifold(gv,gt)
collisions['gear']=float((m^gear).volume());assert collisions['gear']<1e-6
lv,lt=triangulate(import_step(a/'backing-sleeve-keyless-installed.step'))
lower=make_manifold(lv+np.array(build['backing-sleeve']['assembly_translation']),lt)
collisions['lower_gear']=float((lower^gear).volume());assert collisions['lower_gear']<1e-6
report['assembly_overlap_mm3']=collisions
report['limits']='Physical clamp/friction and stiffness not measured; CAD thickening is not strength certification.'
(R/'EXPORT-CHECKS.json').write_text(json.dumps(report,indent=2)+'\n')
(R/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(R))+'\n' for f in sorted(a.iterdir()) if f.is_file()))
print(json.dumps(report))
