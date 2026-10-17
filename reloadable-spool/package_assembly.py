"""Assembly-only mesh export. Individual added parts are the print files."""
from pathlib import Path
import json,zipfile,hashlib
import numpy as np
from source_mesh import ROOT,source,read_stl,write_stl

def main():
 meshes={'retained-eight-spoke-gear':read_stl(source('gear'))}
 for name,file in [('backing-sleeve','backing-sleeve-assembled.npz'),('removable-flange','removable-flange-assembled.npz'),('retained-stock-nut','nut-assembled.npz')]:
  d=np.load(ROOT/'artifacts'/file);meshes[name]=(d['v'],d['t'])
 objects=[];build=[];vv=[];tt=[];offset=0
 for i,(name,(v,t)) in enumerate(meshes.items(),1):
  vs=''.join(f'<vertex x="{x:.17g}" y="{y:.17g}" z="{z:.17g}"/>' for x,y,z in v)
  ts=''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in t)
  objects.append(f'<object id="{i}" type="model" name="{name}"><mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>');build.append(f'<item objectid="{i}"/>');vv.append(v);tt.append(t+offset);offset+=len(v)
 model='<?xml version="1.0"?><model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><metadata name="Title">ASSEMBLY REFERENCE ONLY - reloadable Kraken prototype</metadata><resources>'+''.join(objects)+'</resources><build>'+''.join(build)+'</build></model>'
 path=ROOT/'artifacts/assembly-reference-NOT-FOR-PRINT.3mf'
 with zipfile.ZipFile(ROOT/'artifacts/backing-sleeve.3mf') as inp,zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as out:
  for filename in ('[Content_Types].xml','_rels/.rels'):out.writestr(filename,inp.read(filename))
  out.writestr('3D/3dmodel.model',model)
 write_stl(np.vstack(vv),np.vstack(tt).astype(np.uint64),ROOT/'artifacts/assembly-reference-NOT-FOR-PRINT.stl')
 T=json.loads((ROOT/'analysis/thread.json').read_text())['configurations'][-1];I=json.loads((ROOT/'analysis/interfaces.json').read_text());ga=np.array(I['gear']['axis_xy']);na=np.array(I['nut']['axis_xy']);ph=T['nut_phase_deg']*np.pi/180
 R=np.array([[np.cos(ph),np.sin(ph),0],[np.sin(ph),-np.cos(ph),0],[0,0,-1]]);M=np.eye(4);M[:3,:3]=R;M[:3,3]=np.r_[ga,T['nut_outer_face_z']]-R@np.r_[na,0]
 out={'units':'mm','gear_source_sha256':hashlib.sha256(source('gear').read_bytes()).hexdigest(),'gear_assembly_transform':np.eye(4).tolist(),'nut_source_sha256':hashlib.sha256(source('nut').read_bytes()).hexdigest(),'nut_assembly_transform':M.tolist(),'native_step_scope':'added-parts-assembly.step contains the two new analytic parts. Retained gear STEP is linked from existing gear/models/gear-spokes.step.gz; no duplicate huge faceted gear STEP. Full display assembly is provided in 3MF/STL, not for printing as one part.','individual_print_files':['backing-sleeve.3mf','removable-flange.3mf'],'assembly_mesh_objects':list(meshes)}
 (ROOT/'analysis/assembly-placement.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
