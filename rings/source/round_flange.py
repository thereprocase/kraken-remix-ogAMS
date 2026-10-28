"""Round Kraken spool ring pairs: humebeam's 0.4 mm lip is thickened per flange set.

Gear side: the lip becomes a flange reaching 20 mm past the spool hole. Cap side: the lip keeps
its 2.5 mm reach and only gets thicker. Flange sets match generate_family.FLANGE_SETS
(normal: gear 2.2, cap 0.6; skinny: 0.4 on both).
The designer's mesh is remapped in place, so the bore snap ribs and every edge stay as modelled:
height 0..0.4 stretches to 0..T and everything above moves up T - 0.4; lip vertices move
outward by the extra flange width. Topology is unchanged, so the result stays watertight.
Usage: round_flange.py SOURCE_DIR OUT_DIR [normal|skinny]
"""
import re
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np

from mesh3mf import load  # noqa: E402

LIP_T = 0.4                  # original lip thickness
REACH = 20.0                 # gear-side flange reaches this far past the spool hole edge
LIP_W = 2.5                  # original lip reach past the hole edge
FLANGE_SETS = {'normal': dict(cap=0.6, gear=2.2), 'skinny': dict(cap=0.4, gear=0.4)}


def signed_areas_xy(v, t):
    a, b, c = v[t[:, 0], :2], v[t[:, 1], :2], v[t[:, 2], :2]
    return 0.5 * ((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0]))


def remap(v, hole_r, new_t, reach):
    v = v.copy()
    c = (v.min(0) + v.max(0)) / 2
    z = v[:, 2] - v[:, 2].min()
    r = np.hypot(v[:, 0] - c[0], v[:, 1] - c[1])
    lip = (r > hole_r + 0.05) & (z <= LIP_T + 1e-3)
    if ((r > hole_r + 0.05) & (z > LIP_T + 1e-3)).any():
        raise ValueError("material outside the hole radius above the lip")
    # scale the distance past the hole edge (8x for 2.5 -> 20 mm, 1x on the cap side); an affine stretch near the edge keeps faces from folding
    scale = np.where(lip, (hole_r + (r - hole_r) * reach / LIP_W) / np.maximum(r, 1e-9), 1.0)
    v[:, 0] = c[0] + (v[:, 0] - c[0]) * scale
    v[:, 1] = c[1] + (v[:, 1] - c[1]) * scale
    z_new = np.where(z <= LIP_T, z * new_t / LIP_T, z + (new_t - LIP_T))
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


def main(src_dir, out_dir, flange_set="normal"):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    flanges = FLANGE_SETS[flange_set]
    sides = [(f"gear-side-{flanges['gear']:g}mm-flange", flanges["gear"], REACH),
             (f"cap-side-{flanges['cap']:g}mm-lip", flanges["cap"], LIP_W)]
    for f in sorted(Path(src_dir).glob("kraken-spool-ring-*-mm-100.3mf")):
        size = int(re.search(r"ring-(\d+)-mm", f.name).group(1))
        v, t = load(str(f), 1)
        c = (v.min(0) + v.max(0)) / 2
        zz = v[:, 2] - v[:, 2].min()
        hole_r = float(np.hypot(v[:, 0] - c[0], v[:, 1] - c[1])[(zz > 2) & (zz < 9)].max())
        for side, new_t, reach in sides:
            nv = remap(v, hole_r, new_t, reach)
            # no flipped or collapsed faces among the flat (top/bottom) faces
            before, after = signed_areas_xy(v, t), signed_areas_xy(nv, t)
            flat = np.abs(before) > 1e-9
            flips = int((np.sign(before[flat]) != np.sign(after[flat])).sum())
            e = np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1)
            _, cnt = np.unique(e, axis=0, return_counts=True)
            assert flips == 0 and int((cnt != 2).sum()) == 0, (f.name, side)
            a, b, cc = nv[t[:, 0]], nv[t[:, 1]], nv[t[:, 2]]
            vol = np.einsum("ij,ij->i", a, np.cross(b, cc)).sum() / 6
            name = f"kraken-spool-ring-{size}-mm-round-{side}.stl"
            write_stl(out / name, nv, t, f"Kraken spool ring {size} mm round {side}")
            ext = nv.max(0) - nv.min(0)
            print(f"{name}: OD {ext[0]:.1f} x {ext[1]:.1f}, height {ext[2]:.2f}, volume {abs(vol):.0f} mm3")
    with zipfile.ZipFile(out / f"kraken-spool-rings-round-{flange_set}-stl.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for s in sorted(out.glob("kraken-spool-ring-*-mm-round-*.stl")):
            z.write(s, s.name)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *sys.argv[3:4])
