# Design and clearance notes

These notes explain the replacement Kraken bodies in the [README](../README.md). Each body supports two spool holders. The gear-clearance pocket is a shallow recess in the wall beside a holder’s large gear; the removable front bar is a separate end section of the body beside the filament feeders. The models retain the intended hardware locations and fits, checked digitally to 0.05 mm. Dimensions below are in millimetres.

![Sections of the actual released geometry](images/sections.png)

## What drives the body

| Driver | Nominal | Purpose |
|---|---:|---|
| Maximum spool width | 70.0 | Bay sizing |
| Design gear-disc allowance | 4.4 | Bay sizing; a design allowance, not a new measurement of every gear STL |
| Remaining running allowances | 2.6 total | 70 + 4.4 + 2.6 = 77.0 bay width |
| Bay pitch | 84.0 | Repeated walls, seats and feeder locations |
| Gear tip radius | 99.32 | Radial clearance envelope |
| Pocket coverage radius | 100.32 | Gear radius + 1.0 radial margin |
| Pocket nominal depth / taper | 0.6 / 6° | Additional axial rim clearance with a gradual transition |
| Peg-seat radius | 6.0 | Existing axle support |
| Holder float | 0.79 | Axial assembly allowance; not free clearance to spend twice |
| Feeder guide clear width | 37.1 | One width for identical stock feeders |
| Body print height | 244.9 | 5.0 shorter than the 249.9 original-height body |

In the CAD coordinate system, the spool-holder axle centre is Y−54.39/Z−24.18. The curved body floor beneath the spool is called the cradle. Its centre is deliberately offset from the axle to follow the reference design’s varying clearance. Hardware features use independent positioning datums: gear radius or cradle-clearance edits must not move screw pilots, board retainers or axle seats.

A **spool-centering ring** fits inside the filament spool’s centre hole and snaps onto the Kraken holder. A separate gear-side ring explored during development has a broader, thicker flange—the lip between the spool and the large gear—to support the spool’s clamping face. The [55.5 mm pentagon ring pair](../rings/README.md) is supplied separately; it is not a front bar and is not qualified by the body checks. Its thickness changes how the spool seats on the holder; it must not automatically be counted as moving the bearing-located gear away from the body wall. Any claimed extra wall clearance requires checking the actual assembled holder and bearing positions.

## Radial runout versus axial wobble

![Kinematic clearance illustration](images/runout-clearance.png)

**Radial excursion** increases the required radius in the plane of the gear. The nominal pocket coverage radius is R100.32 for an R99.32 gear: 1.0 mm of radial envelope allowance. An assumed 0.5 mm radial excursion would consume half that allowance. This arithmetic is not a measured runout value or a full bearing/spool tolerance stack. It does not establish clearance elsewhere in the assembly.

**Axial wobble** moves the rim toward the side wall. For a gear-axis tilt θ about a transverse axis through the gear centre, the rim's axial displacement component is approximately `R × sin(θ)`. At R99.32, 0.25° produces about 0.433 mm and 1° about 1.733 mm. Translation, end float and axial face runout add to the relevant direction of motion. Do not confuse these millimetres with radial radius allowance.

Pocket depth adds local axial clearance to the existing gap; it is not the total allowable wobble. The nominal cut is 0.6 mm, but **the bottom sector is wall-limited to 0.15 mm** in the delivered model. Actual exported right-body ray checks at Z−24.18 and radii 90, 97, 99.32, 99.82 and 100 all move the wall from X−82.27 to X−82.42. The sections above show that relief. The accepted full-rim gate checks the available wall sectors on both halves, including the bottom sector.

The material remaining in the body wall behind the recess measures about **1.23 mm** at the minimum sampled station, against the 1.2 mm design gate. That wall constraint explains why increasing the nominal pocket depth cannot supply the same gain at every azimuth. The separate cap-side locating-wall checks measured about 1.38 mm right / 1.67 mm left. These are sampled checks, not a proof of the minimum thickness at every mathematical point.

No total safe tilt, measured runout, maximum speed, or dynamic life is claimed. A full tolerance budget needs the installed ring's actual offset, axial gap, bearing/end float, gear face runout, spool geometry and load. The drawings make the clearance mechanism visible; they do not replace those measurements.

## Why the front bars fit this way

Each half has one bar, two repeated square keys and a broad seating shoulder. The keys are 6.0 mm wide/deep, on 84.0 mm centres, with a 0.4 mm tip lead and 0.8 mm, 45° root tapers. The body's shoulder is Z116.95; key tips end at Z119.95, making the body 244.9 mm tall. The bar restores the original Z124.95 feed end and prints flat as an 8 mm-tall part with its shoulder at Z0.

Two bar generations share those keys:

- **Slide-on bars (cad-library-2026-10-15, asa-print-2026-10-16):** blind 6.3 mm sockets, 0.15 mm running clearance per side, zero-gap root tapers on all four flanks. The bar slides on along the body's long axis (3.15 mm travel) and must be fitted before the front box tabs engage.
- **Drop-in bars (v5, [prints/pctg-2026-10-28-v5](../prints/pctg-2026-10-28-v5/README.md)):** each socket is a U-slot open to the bar's floor-side edge, 6.6 mm wide and 3.3 mm deep (0.30 mm per side, the clearance that slid by hand on the owner's P1S fit ladder), with zero-gap 45° tapers on the two side flanks only. The closed flank follows the key's root collar 0.70 mm above it, so the bar rests on the box floor and can be nudged past the key position by hand; it never hangs on the keys. The joined halves go into the box without the bars, each bar drops onto its keys from above, and a 3 mm forward slide puts the box front tabs into the bars' existing clip slots, which then hold bars and bodies down. The main board goes in after the bars and comes out first. A body with the released keys accepts either bar.

The key pockets have a 6.3 or 6.6 mm roof span, so bridge performance still needs practical checking. No full AMS-box solid was available, so whole-unit installation, the 3 mm slide allowance and hand/tool access remain unverified; the drop-in sequence assumes at least 3.3 mm of free box depth with the bars on.

## Modeling and evidence boundaries

The native builder uses named mechanical datums and repeated primitives: extrusions, slots, circles, tapers, chamfers and patterns. Original source meshes informed measurements and checks; they do not supply traced outlines to construct this CAD. The immutable RFID reference meshes are used only by the no-added-material export guard.

The RFID pocket remains under the original strict removal-only gate. A 0.05 mm digital interface check is not a promise of 0.05 mm printed accuracy; shrinkage, extrusion width, layer orientation and hardware variation remain physical variables.
