"""Shared native CAD features. This module never reads a source mesh."""
from pathlib import Path
import zipfile
import numpy as np
from build123d import Edge,Wire,Face,Solid,Plane,Compound,export_step
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepTools import BRepTools

def sketch_wire(edges,axis='X',position=0):
 def p(q):
  return {'X':(position,q[0],q[1]),'Y':(q[0],position,q[1]),'Z':(q[0],q[1],position)}[axis]
 result=[]
 for e in edges:
  if e['kind']=='line':result.append(Edge.make_line(p(e['start']),p(e['end'])))
  else:result.append(Edge.make_three_point_arc(p(e['start']),p(e['mid']),p(e['end'])))
 return Wire(result)

def profile_extrusion(edges,start,end,axis='X',holes=()):
 outer=sketch_wire(edges,axis,start)
 inners=[sketch_wire(h,axis,start) for h in holes]
 face=Face(outer,inners)
 direction={'X':(end-start,0,0),'Y':(0,end-start,0),'Z':(0,0,end-start)}[axis]
 s=Solid.extrude(face,direction)
 assert s.is_valid,'Invalid profile extrusion'
 return s

def box_bounds(x0,x1,y0,y1,z0,z1):
 return Solid.make_box(x1-x0,y1-y0,z1-z0,Plane(origin=(x0,y0,z0)))

def triangulate(shape,linear=.01,angular=.025):
 BRepTools.Clean_s(shape.wrapped)
 BRepMesh_IncrementalMesh(shape.wrapped,linear,False,angular,False)
 vv,tt=shape.tessellate(linear,angular)
 v=np.array([[q.X,q.Y,q.Z] for q in vv]);t=np.array(tt,dtype=np.uint64)
 # Weld face seams by distance BEFORE decimal quantization: rounding alone can
 # split one OCCT seam across adjacent bins and leave a three-edge needle hole.
 # The 0.00001 mm tolerance is 5000 times below the interface tolerance.
 from scipy.spatial import cKDTree
 v,inverse=np.unique(v,axis=0,return_inverse=True);t=inverse[t]
 parent=np.arange(len(v))
 def root(i):
  while parent[i]!=i:
   parent[i]=parent[parent[i]];i=parent[i]
  return i
 for a,b in cKDTree(v).query_pairs(1e-5):
  a,b=root(a),root(b)
  if a!=b:parent[max(a,b)]=min(a,b)
 mapping=np.array([root(i) for i in range(len(v))]);t=mapping[t]
 v,inverse=np.unique(np.round(v,5),axis=0,return_inverse=True);t=inverse[t]
 t=t[(t[:,0]!=t[:,1])&(t[:,1]!=t[:,2])&(t[:,2]!=t[:,0])]

 return v,t.astype(np.uint64)

def export_3mf(shape,path,mesh=None):
 v,t=triangulate(shape) if mesh is None else mesh
 vertices=''.join(f'<vertex x="{x:.9g}" y="{y:.9g}" z="{z:.9g}"/>' for x,y,z in v)
 triangles=''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in t)
 model='<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources><object id="1" type="model"><mesh><vertices>'+vertices+'</vertices><triangles>'+triangles+'</triangles></mesh></object></resources><build><item objectid="1"/></build></model>'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
  z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
  z.writestr('3D/3dmodel.model',model)
 return v,t

def export_stage(shape,root,side,stage):
 assert shape.is_valid, 'Refusing to export an invalid native body'
 assert len(shape.solids())==1, ('Refusing to export disconnected body parts',[(s.volume,str(s.bounding_box())) for s in shape.solids()])
 bounds=shape.bounding_box();length=bounds.max.Z-bounds.min.Z
 assert length<=249.90001, f'Print length exceeds 249.9 mm: {length}'
 path=Path(root)/'artifacts'/f'{side}_{stage}'
 v,t=triangulate(shape)
 from export_guards import rfid_no_addition
 try:
  gate=rfid_no_addition(root,side,stage,v,t)
 except Exception:
  np.savez(Path(root)/'analysis'/f'{side}_{stage}_rejected_export_candidate.npz',v=v,t=t)
  raise
 export_step(shape,str(path)+'.step')
 v,t=export_3mf(shape,str(path)+'.3mf',mesh=(v,t))
 np.savez(str(path)+'_display.npz',v=v,t=t)
 from validation_metadata import provenance
 return dict(provenance=provenance(side,stage),step=str(path)+'.step',three_mf=str(path)+'.3mf',volume_mm3=shape.volume,valid=shape.is_valid,solids=len(shape.solids()),faces=len(shape.faces()),length_mm=length,rfid_export_gate=gate)


def normalize_native_topology(shape):
 """Repair OCCT edge parameterizations using only the generated analytic solid.

 The STEP transfer stays in memory. No files, reference model or mesh are read.
 Validity, solid count and volume guard this kernel normalization.
 """
 from io import BytesIO
 from OCP.STEPControl import STEPControl_Reader
 from OCP.IFSelect import IFSelect_RetDone
 before=shape.volume;stream=BytesIO();export_step(shape,stream);stream.seek(0)
 reader=STEPControl_Reader()
 assert reader.ReadStream('native',stream)==IFSelect_RetDone
 reader.TransferRoots();result=Compound.cast(reader.OneShape())
 assert result.is_valid and len(result.solids())==len(shape.solids())
 if abs(result.volume-before)>=.01:
  # Normalization is optional for an already valid native solid. Never accept
  # a STEP-transfer candidate that changes its volume: retain the original
  # analytic geometry instead. Invalid inputs still fail the same guard.
  assert shape.is_valid, f'Native topology normalization changed volume: {before:.9f} -> {result.volume:.9f} mm3'
  return shape
 return result
