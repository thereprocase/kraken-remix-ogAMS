# 55.5 mm pentagon spool flange pair

These are the existing centering rings made for the Polymaker cardboard-spool setup used with Kraken. Use **one gear-side ring and one cap-side ring per spool**. They snap onto the Kraken holder and centre the spool through its centre hole; they are separate from the removable body front bars.

| Part | STL | STEP solid | Placement |
|---|---|---|---|
| Gear-side ring, 1.5 mm flange | [STL](models/kraken-spool-ring-55.5-mm-pentagon-gear-side-1.5mm-flange.stl) | [STEP](models/kraken-spool-ring-55.5-mm-pentagon-gear-side-1.5mm-flange.step) | Between the spool and large gear |
| Cap-side ring | [STL](models/kraken-spool-ring-55.5-mm-pentagon-cap-side.stl) | [STEP](models/kraken-spool-ring-55.5-mm-pentagon-cap-side.step) | Between the spool and threaded holder cap |

On GitHub, open the file and select **Download raw file**. The STL files are unchanged downloads, with no slicer settings. See the STEP conversion details below.

## STEP representation

The STEP downloads are **faceted solid conversions of the existing STL files**, not smooth native CAD. STEP conversion cannot add resolution that was absent from the source. No curves were refitted and no mating surfaces were smoothed.

Direct conversion encountered degenerate triangles and tiny edges in the STL export. Numerical topology cleanup at **0.00001 mm tolerance** makes valid CAD solids. It retains a subset of the original vertices in their original positions and retriangulates the affected surfaces. This is an explicitly bounded conversion, not a claim of byte-for-byte or triangle-for-triangle identity with the original STL. The STL downloads remain unchanged.

The conversion imports each exported STEP again and compares every triangular face with the cleaned mesh, as well as validity and solid count. It also checks volume, bounds and Boolean volume difference against the original mesh. Results are in [STEP-CHECKS.json](STEP-CHECKS.json). To reproduce the conversion with the [repository CAD dependencies](../requirements.txt), run from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 python rings/export_step.py rings-step-build
```

Use a new output directory. This converts the existing meshes; it does not regenerate or redesign the rings.

## Which size to print

Measure the spool's centre hole with calipers in a few directions and use the smallest reading. Print the nominal size **equal to that reading or up to 0.9 mm below it**. The round support surface sits 0.1 mm inside the nominal radius, so a ring larger than the hole will not enter; the five corners stand 0.7 mm proud of the nominal radius, so they still grip a hole up to about 1 mm wider than the nominal size.

| Cardboard spool | Centre hole | Ring to print | Where the figure comes from |
|---|---:|---|---|
| Polymaker | 55.5 mm | [55.5 mm pair](#555-mm-pentagon-spool-flange-pair) | Measured for this remix |
| Elegoo Rapid PETG | 53.4 mm | [53.4 mm pair](brand-sizes/README.md) | Measured for this remix |
| Bambu Lab | about 55 mm | [55 mm](stock-sizes/README.md) | [Community report](https://forum.bambulab.com/t/bambu-spool-dimensions/123480) |
| eSun | 52–54.3 mm, varies | Measure; [52 or 54 mm](stock-sizes/README.md) | Community reports disagree ([52 mm](https://community.ultimaker.com/topic/22434-ultimaker-question-help-us-help-you/), [54.3 mm](https://www.printables.com/model/1506017-ams-cardboard-spool-adapter-esun-anycubic)) |
| Overture, Duramic | about 53.5 mm | [53 mm](stock-sizes/README.md) or the 53.4 mm pair | Inferred from a [bushing designed for them](https://www.printables.com/model/596930-filament-spool-bushing) |
| Other brands | 52–58 mm is typical | Measure first | — |

Spool makers change cores between batches, so treat the brand column as a starting point and the caliper reading as the deciding figure.

## More sizes and source

[Matched pentagon pairs for all 45–95 mm stock sizes](stock-sizes/README.md) and [specific-spool sizes such as 53.4 mm](brand-sizes/README.md) are available separately, along with the [earlier round flange family](round-flanges/README.md). The [portable generators and original reference inputs](source/README.md) reproduce these designs; the existing 55.5 mm pair regenerates byte-for-byte.

## Shape and fit

The design targets a **55.5 mm spool centre hole**. A round support surface of radius 27.65 mm centres the spool, while five pentagon corners extend to radius 28.45 mm to grip the cardboard. The corners stand 0.7 mm beyond the nominal hole radius. A tapered lead-in eases entry. Check the actual spool hole; this is not a claim that every Polymaker spool uses the same dimensions, or that the interference suits a rigid plastic spool.

The gear-side flange is **76 mm in outside diameter and 1.5 mm thick**. The cap-side ring retains the original 0.4 mm lip. Raising the gear-side insertion section by 1.1 mm preserves its insertion length while moving the spool's seating face away from the gear. This does not establish a corresponding increase in gear-to-body wall clearance: the installed holder and bearing positions determine that gap.

The holder-facing bore and snap details originate in humebeam's `kraken-spool-ring-55-mm-100.3mf`. The external centering profile and gear-side flange were modified for this pair. Follow the original holder assembly instructions and avoid overtightening the spool against the gear.

## Provenance

Original Kraken and spool-ring design: **[humebeam](https://www.printables.com/model/1788417-kraken-revolutionary-bambu-lab-ams)**. Remix: **thereprocase**. Distributed under [CC BY-NC 4.0](../LICENSE.md).

[File hashes](FILES.json) identify the two existing STL files. The STL files were copied byte-for-byte from the previously served pair. The STEP conversion and its numerical cleanup are documented above. The body's 0.05 mm interface checks and gear stiffness comparisons do not qualify these rings.
