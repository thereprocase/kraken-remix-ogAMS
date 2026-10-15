"""Retain source interface facets; connect them with planar analytic-web caps.

Mesh Booleans can simplify nearly coplanar hub facets. Avoid that operation:
retain the original nonplanar tooth/hub/bore triangles, instance only the new
window sidewalls, and triangulate the two flat disc faces using their existing
boundary vertices. No interface vertex is fitted, rounded or reconstructed.
"""
import numpy as np
import manifold3d as mf

def boundary_loops(v,t):
    directed=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]])
    keys=np.sort(directed,axis=1);_,inverse,count=np.unique(keys,axis=0,return_inverse=True,return_counts=True)
    edges=directed[count[inverse]==1][:,::-1]  # cap opposes retained sidewall
    assert count.max()<=2
    follow={int(a):int(b) for a,b in edges};assert len(follow)==len(edges)
    loops=[]
    while follow:
        first=next(iter(follow));loop=[];current=first
        while True:
            loop.append(current);current=follow.pop(current)
            if current==first:break
        loops.append(np.array(loop,dtype=np.uint64))
    return loops

def assemble(v,t,window_meshes,disc_top=4.,tooth_inner=95.):
    tri=v[t];rad=np.linalg.norm(tri[:,:,:2],axis=2);span=np.ptp(tri[:,:,2],axis=1)
    kept=((rad.min(1)>=tooth_inner)&(span>1e-7)) | (tri[:,:,2].max(1)>disc_top) | ((rad.max(1)<=14.)&(span>1e-7))
    triangles=[tri[kept]]
    for a,b in window_meshes:
        q=a[b];side=np.ptp(q[:,:,2],axis=1)>1e-7
        triangles.append(q[side][:,[0,2,1]])
    triangles=np.concatenate(triangles)
    # Source coordinates already are float32. Only new non-mating windows
    # acquire float32 STL precision here, before closure/validity checks.
    vv,tt=np.unique(triangles.astype(np.float32).astype(float).reshape(-1,3),axis=0,return_inverse=True)
    tt=tt.reshape(-1,3).astype(np.uint64);loops=boundary_loops(vv,tt);caps=[]
    for z in [0.,disc_top]:
        rings=[]
        for loop in loops:
            heights=vv[loop,2]
            assert np.ptp(heights)<1e-7 and (abs(heights[0])<1e-7 or abs(heights[0]-disc_top)<1e-7),'Unexpected interface opening'
            if abs(heights[0]-z)<1e-7:rings.append(loop if z>0 else loop[::-1])
        ids=np.concatenate(rings);points=[vv[r,:2].copy() for r in rings]
        local=np.asarray(mf.triangulate(points,epsilon=0.,allow_convex=False),dtype=np.uint64)
        face=ids[local]
        if z==0:face=face[:,[0,2,1]]
        caps.append(face)
    out=np.concatenate([tt,*caps]);mesh=mf.Manifold(mf.Mesh64(vv,out))
    assert mesh.status()==mf.Error.NoError,mesh.status()
    assert len(mesh.decompose())==1
    return vv,out,dict(source_retained_triangles=int(kept.sum()),new_window_side_triangles=int(len(tt)-kept.sum()),
                       cap_boundary_loops=len(loops),method='Exact original interface facets plus planar caps; no Boolean simplification of retained interfaces')
