"""Gear-side Kraken spool rings: the 0.4 mm lip becomes a 1.5 mm thick flange reaching 20 mm past the spool hole.

The designer's mesh is remapped in place, so the bore snap ribs and every edge stay as modelled:
height 0..0.4 stretches to 0..1.5 and everything above moves up 1.1 mm; lip vertices move
outward by the extra flange width. Topology is unchanged, so the result stays watertight.
"""
import re
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np

from mesh3mf import load  # noqa: E402

LIP_T, NEW_T = 0.4, 1.5      # original lip thickness, new flange thickness
REACH = 20.0                 # flange reaches this far past the spool hole edge
LIP_W = 2.5                  # original lip reach past the hole edge


def signed_areas_xy(v, t):
    a, b, c = v[t[:, 0], :2], v[t[:, 1], :2], v[t[:, 2], :2]
    return 0.5 * ((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0]))


def remap(v, hole_r):
    v = v.copy()
    c = (v.min(0) + v.max(0)) / 2
    z = v[:, 2] - v[:, 2].min()
    r = np.hypot(v[:, 0] - c[0], v[:, 1] - c[1])
    lip = (r > hole_r + 0.05) & (z <= LIP_T + 1e-3)
    if ((r > hole_r + 0.05) & (z > LIP_T + 1e-3)).any():
        raise ValueError("material outside the hole radius above the lip")
    # scale the distance past the hole edge (8x for 2.5 -> 20 mm); an affine stretch near the edge keeps faces from folding
    scale = np.where(lip, (hole_r + (r - hole_r) * REACH / LIP_W) / np.maximum(r, 1e-9), 1.0)
    v[:, 0] = c[0] + (v[:, 0] - c[0]) * scale
    v[:, 1] = c[1] + (v[:, 1] - c[1]) * scale
    z_new = np.where(z <= LIP_T, z * NEW_T / LIP_T, z + (NEW_T - LIP_T))
    v[:, 2] = v[:, 2].min() + z_new
    return v


def write_stl(path, v, t, title):
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
    rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
    with open(path, "wb") as f:
        f.write(title.encode()[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        f.write(rec.tobytes())


def main(src_dir, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted(Path(src_dir).glob("kraken-spool-ring-*-mm-100.3mf")):
        size = int(re.search(r"ring-(\d+)-mm", f.name).group(1))
        v, t = load(str(f), 1)
        c = (v.min(0) + v.max(0)) / 2
        zz = v[:, 2] - v[:, 2].min()
        hole_r = float(np.hypot(v[:, 0] - c[0], v[:, 1] - c[1])[(zz > 2) & (zz < 9)].max())
        nv = remap(v, hole_r)
        # no flipped or collapsed faces among the flat (top/bottom) faces
        before, after = signed_areas_xy(v, t), signed_areas_xy(nv, t)
        flat = np.abs(before) > 1e-9
        flips = int((np.sign(before[flat]) != np.sign(after[flat])).sum())
        e = np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1)
        _, cnt = np.unique(e, axis=0, return_counts=True)
        a, b, c = nv[t[:, 0]], nv[t[:, 1]], nv[t[:, 2]]
        vol = np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6
        name = f"kraken-spool-ring-{size}-mm-gear-side-1.5mm-flange.stl"
        write_stl(out / name, nv, t, f"Kraken spool ring {size} mm, gear side, 1.5 mm flange")
        ext = nv.max(0) - nv.min(0)
        print(f"{name}: OD {ext[0]:.1f} x {ext[1]:.1f}, height {ext[2]:.2f}, flips {flips}, "
              f"non-manifold edges {int((cnt != 2).sum())}, volume {abs(vol):.0f} mm3")
    with zipfile.ZipFile(out / "kraken-spool-rings-gear-side-1.5mm-flange.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for s in sorted(out.glob("kraken-spool-ring-*-gear-side-1.5mm-flange.stl")):
            z.write(s, s.name)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
