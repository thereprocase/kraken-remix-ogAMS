"""55.5 mm Kraken spool centering rings with a sharp pentagon spigot, for spools whose hole runs a hair over 55 mm.

Built from the designer's 55 mm ring so the bore and its snap ribs stay as modelled:
- the spigot is a round bearing body (BEARING_R, a sliding fit in a HOLE_D hole) with the five corners of a
  pentagon standing INTERFERENCE proud of the hole: the circle carries and centres the spool, the five sharp
  corners bite into the cardboard so the gear needs less tightening to stop it slipping; both taper by
  LEAD_R over the last LEAD_H as a lead-in;
- the cap-side ring keeps the stock 0.4 mm lip;
- the gear-side ring gets a FLANGE_T thick flange reaching FLANGE_REACH past the spigot, and its spigot
  rides FLANGE_T - lip higher so the insertion length is unchanged (the spool sits 1.1 mm further from the gear).
Usage: rings_555.py OUTDIR
"""
import struct
import sys
from pathlib import Path

import manifold3d as mf
import numpy as np

from mesh3mf import load

SRC = Path(__file__).resolve().parent / "reference/kraken-spool-ring-55-mm-100.3mf"
HOLE_D = 55.5                  # spool hole the ring is sized for
INTERFERENCE = 0.7             # pentagon corners stand this far outside the hole, radially
CORNER_R = HOLE_D / 2 + INTERFERENCE
BEARING_R = HOLE_D / 2 - 0.1   # round bearing body just inside the tips: a sliding fit that carries the spool
SPIGOT_D = HOLE_D              # flange/lip inner reference
LEAD_R, LEAD_H = 1.9, 2.0      # corners taper 1.9 mm over the last 2 mm: the tip starts inside the hole
BORE_KEEP_R = 22.5             # the stock bore and snap ribs live inside this radius
LIP_T = 0.4                    # stock lip thickness
FLANGE_T = 1.5                 # gear-side flange thickness
FLANGE_REACH = 10.25          # flange reach past the 55.5 hole: 76 mm OD, so 2 nuts and 4 pairs share one plate
SEGMENTS = 256


def manifold_of(v, t):
    m = mf.Mesh64(np.asarray(v, float), np.asarray(t, np.uint64))
    m.merge()
    return mf.Manifold(m)


def revolve(profile):
    """Solid of revolution about Z from an (r, z) polygon."""
    return mf.Manifold.revolve(mf.CrossSection([profile]), SEGMENTS)


def pentagon(radius):
    angles = np.radians(90 + 72 * np.arange(5))
    return mf.CrossSection([np.column_stack([radius * np.cos(angles), radius * np.sin(angles)])])


def spigot_section():
    return pentagon(CORNER_R) + mf.CrossSection.circle(BEARING_R, SEGMENTS)


def ring_555(stock):
    lo, hi = stock.bounding_box()[2], stock.bounding_box()[5]
    stock = stock.translate((0, 0, -lo))
    top = hi - lo
    straight = spigot_section().extrude(top - LEAD_H - LIP_T).translate((0, 0, LIP_T))
    lead = spigot_section().extrude(LEAD_H, scale_top=((CORNER_R - LEAD_R) / CORNER_R,) * 2)
    spigot = straight + lead.translate((0, 0, top - LEAD_H))
    keep = mf.Manifold.cylinder(top + 2, BORE_KEEP_R, BORE_KEEP_R, SEGMENTS).translate((0, 0, -1))
    lip = stock ^ mf.Manifold.cube((200, 200, LIP_T)).translate((-100, -100, 0))
    return (stock ^ keep) + (spigot - keep) + lip, top


def gear_side(ring):
    """Thicken the lip into a flange and raise the spigot so it inserts as deep as the stock ring."""
    rise = FLANGE_T - LIP_T
    raised = ring.translate((0, 0, rise))
    above = raised ^ mf.Manifold.cube((200, 200, 100)).translate((-100, -100, FLANGE_T))
    lip = ring.slice(LIP_T / 2)  # lip footprint, including its bore
    outer = mf.CrossSection.circle(SPIGOT_D / 2 + FLANGE_REACH, SEGMENTS)
    bore = mf.CrossSection.circle(SPIGOT_D / 2 - 0.01, SEGMENTS)
    flange = (lip + (outer - bore)).extrude(FLANGE_T)
    return above + flange


def write_stl(path, m, title):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("a", "<f4", 3), ("b", "<f4", 3), ("c", "<f4", 3), ("x", "<u2")])
    rec["n"], rec["a"], rec["b"], rec["c"] = n, a, b, c
    with open(path, "wb") as f:
        f.write(title.encode()[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        f.write(rec.tobytes())


def describe(name, m):
    lo = np.array(m.bounding_box()[:3])
    hi = np.array(m.bounding_box()[3:])
    print(f"{name}: OD {hi[0] - lo[0]:.2f}, height {hi[2] - lo[2]:.2f}, volume {m.volume():.0f} mm3, "
          f"genus {m.genus()}, status {m.status()}")


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    v, t = load(str(SRC), "1")
    c = (v.min(0) + v.max(0)) / 2
    stock = manifold_of(v - [c[0], c[1], 0], t)
    cap, _ = ring_555(stock)
    gear = gear_side(cap)
    for name, m in (("cap-side", cap), ("gear-side-1.5mm-flange", gear)):
        describe(name, m)
        write_stl(out / f"kraken-spool-ring-55.5-mm-pentagon-{name}.stl", m, f"Kraken spool ring 55.5 mm pentagon {name}")
    # Spigot check: diameter at mid height, and at the top of the lead-in.
    for name, m in (("cap-side", cap), ("gear-side", gear)):
        zmax = m.bounding_box()[5]
        for z in (zmax / 2, zmax - 0.05):
            pts = np.vstack([np.asarray(p) for p in m.slice(z).to_polygons()])
            print(f"  {name} z={z:5.2f}: corner radius {np.hypot(pts[:, 0], pts[:, 1]).max():.2f}"
                  f" (hole radius {HOLE_D / 2:.2f})")


if __name__ == "__main__":
    main(sys.argv[1])
