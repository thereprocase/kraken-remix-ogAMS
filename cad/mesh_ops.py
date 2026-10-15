"""Mesh Boolean utilities used only by export guards and assembled exports."""
import numpy as np
import manifold3d as mf

def make_manifold(v,t):
    mesh=mf.Mesh64(np.asarray(v,dtype=np.float64),np.asarray(t,dtype=np.uint64));mesh.merge()
    shape=mf.Manifold(mesh)
    if shape.status()!=mf.Error.NoError:raise ValueError(str(shape.status()))
    return shape

def boxclip(shape,lo,hi):
    box=mf.Manifold.cube(tuple(np.array(hi)-lo)).translate(lo)
    return shape^box
