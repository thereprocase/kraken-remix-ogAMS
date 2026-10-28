# 55.5 mm pentagon spool flange pair

These are the centering rings made for the Polymaker cardboard-spool setup used with Kraken. Use **one gear-side ring and one cap-side ring per spool**. They snap onto the Kraken holder and centre the spool through its centre hole; they are separate from the removable body front bars. The five pentagon points bite into cardboard; for hard plastic spools use the [spring pairs](hard-spool/README.md).

**Flange sets.** *Normal*: 2.2 mm gear-side flange and 0.6 mm cap-side lip. *Skinny*: 0.4 mm on both sides, for holders where the extra 2.0 mm of stack does not fit. humebeam's original 0.4 mm cap lip tends to break during bed removal and handling, which is why normal thickens it.

| Set | Gear side (between the spool and the large gear) | Cap side (between the spool and the threaded holder cap) |
|---|---|---|
| Normal | [3MF](models/kraken-spool-ring-55.5-mm-pentagon-gear-side-2.2mm-flange.3mf) · [STL](models/kraken-spool-ring-55.5-mm-pentagon-gear-side-2.2mm-flange.stl) · [STEP.gz](https://github.com/thereprocase/kraken-remix-ogAMS/releases/download/rings-2026-10-28/kraken-spool-ring-55.5-mm-pentagon-gear-side-2.2mm-flange.step.gz) | [3MF](models/kraken-spool-ring-55.5-mm-pentagon-cap-side-0.6mm-lip.3mf) · [STL](models/kraken-spool-ring-55.5-mm-pentagon-cap-side-0.6mm-lip.stl) · [STEP.gz](https://github.com/thereprocase/kraken-remix-ogAMS/releases/download/rings-2026-10-28/kraken-spool-ring-55.5-mm-pentagon-cap-side-0.6mm-lip.step.gz) |
| Skinny | [3MF](models-skinny/kraken-spool-ring-55.5-mm-pentagon-gear-side-0.4mm-flange.3mf) · [STL](models-skinny/kraken-spool-ring-55.5-mm-pentagon-gear-side-0.4mm-flange.stl) · [STEP.gz](https://github.com/thereprocase/kraken-remix-ogAMS/releases/download/rings-2026-10-28/kraken-spool-ring-55.5-mm-pentagon-gear-side-0.4mm-flange.step.gz) | [3MF](models-skinny/kraken-spool-ring-55.5-mm-pentagon-cap-side-0.4mm-lip.3mf) · [STL](models-skinny/kraken-spool-ring-55.5-mm-pentagon-cap-side-0.4mm-lip.stl) · [STEP.gz](https://github.com/thereprocase/kraken-remix-ogAMS/releases/download/rings-2026-10-28/kraken-spool-ring-55.5-mm-pentagon-cap-side-0.4mm-lip.step.gz) |

On GitHub, open the file and select **Download raw file**. 3MF and STL hold geometry only, flange or lip on Z0, with no slicer settings.

## STEP representation

The STEP downloads are **faceted solid conversions of the STL files**, not smooth native CAD. STEP conversion cannot add resolution that was absent from the source. No curves were refitted and no mating surfaces were smoothed.

Direct conversion encounters degenerate triangles and tiny edges in the STL export. Numerical topology cleanup at **0.00001 mm tolerance** makes valid CAD solids. It retains a subset of the original vertices in their original positions and retriangulates the affected surfaces.

The conversion imports each exported STEP again and compares every triangular face with the cleaned mesh, as well as validity and solid count. It also checks volume, bounds and Boolean volume difference against the original mesh. Results for every ring collection are in [STEP-CHECKS.json](STEP-CHECKS.json). To reproduce the conversion with the [repository CAD dependencies](../requirements.txt), run from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 python rings/export_step.py rings-step-build --input <folder of STL files> --gzip
```

Use a new output directory. This converts existing meshes; it does not regenerate or redesign the rings.

## Which size to print

The [Kraken ring generator](https://thereprocase.github.io/kraken-rings/) builds any size from 45 to 95 mm to 0.1 mm in the browser, with a to-scale diagram of the support circle and pentagon points.

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

[Pentagon pairs for all 45–95 mm stock sizes](stock-sizes/README.md), [specific-spool sizes such as 53.4 mm](brand-sizes/README.md), [spring pairs for hard plastic spools](hard-spool/README.md) and the [round ring family](round-flanges/README.md) are available separately, each in both flange sets. The [portable generators and original reference inputs](source/README.md) reproduce these designs.

## Shape and fit

The design targets a **55.5 mm spool centre hole**. A round support surface of radius 27.65 mm centres the spool, while five pentagon corners extend to radius 28.45 mm to grip the cardboard. The corners stand 0.7 mm beyond the nominal hole radius. A tapered lead-in eases entry. Check the actual spool hole; this is not a claim that every Polymaker spool uses the same dimensions.

The gear-side flange is **76 mm in outside diameter**: 2.2 mm thick in the normal set, 0.4 mm in the skinny set. The cap-side lip keeps the source ring's outline and is 0.6 or 0.4 mm thick. The source lip's section, including bore and snap ribs, runs straight through the thicker base, and the insertion section rises by the added thickness, so it inserts as deep as the stock ring. A thicker gear-side flange moves the spool's seating face away from the gear; it does not establish more gear-to-body wall clearance: the installed holder and bearing positions determine that gap.

The holder-facing bore and snap details originate in humebeam's `kraken-spool-ring-55-mm-100.3mf`. Follow the original holder assembly instructions and avoid overtightening the spool against the gear.

## Provenance

Original Kraken and spool-ring design: **[humebeam](https://www.printables.com/model/1788417-kraken-revolutionary-bambu-lab-ams)**. Remix: **thereprocase**. Distributed under [CC BY-NC 4.0](../LICENSE.md).

[File hashes](FILES.json) identify the 55.5 mm files. Until 2026-10-28 this pair had a 1.5 mm gear flange and humebeam's 0.4 mm cap lip; those files remain in the repository history, and `rings/source/rings_555.py` still reproduces them. With the same 1.5 / 0.4 mm thicknesses `generate_family.py` matches them within 0.0016 mm³. The body's 0.05 mm interface checks and gear stiffness comparisons do not qualify these rings.
