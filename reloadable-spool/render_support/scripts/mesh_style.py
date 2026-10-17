"""Original Kraken render preprocessing: geometry unchanged, crease threshold30deg."""
import numpy as np
CREASE_DEG=30.0

def weld(v, t, tol=1e-4):
    """Vertex ids shared by coincident positions; CAD tessellations split vertices per face."""
    _, inv = np.unique(np.round(v / tol).astype(np.int64), axis=0, return_inverse=True)
    return inv.ravel()[t]


def smooth_normals(v, t):
    wt = weld(v, t)
    fn = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
    acc = np.zeros((wt.max() + 1, 3))
    for k in range(3):
        np.add.at(acc, wt[:, k], fn)
    acc /= np.linalg.norm(acc, axis=1, keepdims=True) + 1e-12
    n = np.zeros_like(v)
    for k in range(3):
        n[t[:, k]] = acc[wt[:, k]]
    return n


def feature_edges(v, t, crease_deg=CREASE_DEG):
    """Edges whose two faces meet sharper than crease_deg, plus open boundaries."""
    wt = weld(v, t)
    fn = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
    fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    e_w = np.vstack([wt[:, [0, 1]], wt[:, [1, 2]], wt[:, [2, 0]]])
    e_v = np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]])
    face = np.tile(np.arange(len(t)), 3)
    key = np.sort(e_w, axis=1)
    order = np.lexsort((key[:, 1], key[:, 0]))
    key, e_v, face = key[order], e_v[order], face[order]
    same = np.all(key[1:] == key[:-1], axis=1)
    first = np.ones(len(key), bool)
    first[1:] = ~same
    starts = np.flatnonzero(first)
    counts = np.diff(np.append(starts, len(key)))
    keep = []
    cos_lim = np.cos(np.radians(crease_deg))
    pair = starts[counts == 2]
    sharp = np.einsum("ij,ij->i", fn[face[pair]], fn[face[pair + 1]]) < cos_lim
    keep.append(pair[sharp])
    keep.append(starts[counts != 2])
    sel = np.concatenate(keep)
    return e_v[sel]


