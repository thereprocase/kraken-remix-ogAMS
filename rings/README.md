# 55.5 mm pentagon spool flange pair

These are the existing centering rings made for the Polymaker cardboard-spool setup used with Kraken. Use **one gear-side ring and one cap-side ring per spool**. They snap onto the Kraken holder and centre the spool through its centre hole; they are separate from the removable body front bars.

| Part | Download | Placement |
|---|---|---|
| Gear-side ring, 1.5 mm flange | [STL](models/kraken-spool-ring-55.5-mm-pentagon-gear-side-1.5mm-flange.stl) | Between the spool and large gear |
| Cap-side ring | [STL](models/kraken-spool-ring-55.5-mm-pentagon-cap-side.stl) | Between the spool and threaded holder cap |

On GitHub, open the file and select **Download raw file**. These are unchanged geometry downloads, with no slicer settings.

## Shape and fit

The design targets a **55.5 mm spool centre hole**. A round support surface of radius 27.65 mm centres the spool, while five pentagon corners extend to radius 28.45 mm to grip the cardboard. The corners stand 0.7 mm beyond the nominal hole radius. A tapered lead-in eases entry. Check the actual spool hole; this is not a claim that every Polymaker spool uses the same dimensions, or that the interference suits a rigid plastic spool.

The gear-side flange is **76 mm in outside diameter and 1.5 mm thick**. The cap-side ring retains the original 0.4 mm lip. Raising the gear-side insertion section by 1.1 mm preserves its insertion length while moving the spool's seating face away from the gear. This does not establish a corresponding increase in gear-to-body wall clearance: the installed holder and bearing positions determine that gap.

The holder-facing bore and snap details originate in humebeam's `kraken-spool-ring-55-mm-100.3mf`. The external centering profile and gear-side flange were modified for this pair. Follow the original holder assembly instructions and avoid overtightening the spool against the gear.

## Provenance

Original Kraken and spool-ring design: **[humebeam](https://www.printables.com/model/1788417-kraken-revolutionary-bambu-lab-ams)**. Remix: **thereprocase**. Distributed under [CC BY-NC 4.0](../LICENSE.md).

[File hashes](FILES.json) identify the two existing STL files. They were copied byte-for-byte from the previously served pair; this publication introduces no geometry changes. The body's 0.05 mm interface checks and gear stiffness comparisons do not qualify these rings.
