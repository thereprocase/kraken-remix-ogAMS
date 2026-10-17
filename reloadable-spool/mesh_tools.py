"""Local mesh export utilities; no body-model imports."""
import zipfile
import numpy as np
import manifold3d as mf
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepTools import BRepTools

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

def make_manifold(v,t):
 mesh=mf.Mesh64(np.asarray(v,dtype=np.float64),np.asarray(t,dtype=np.uint64));mesh.merge()
 s=mf.Manifold(mesh)
 if s.status()!=mf.Error.NoError:raise ValueError(str(s.status()))
 return s
