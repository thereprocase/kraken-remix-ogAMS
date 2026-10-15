# Design and clearance notes

This is the accepted **0.05 mm digital-interface** release. Dimensions are in millimetres. The clearance-pocket variant retains the interface locations and the existing hardware fits. It removes material from the gear-facing wall where the gear rim needs more room, then splits the feed end into a shorter body and a removable front bar.

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

The true axle datum is Y−54.39/Z−24.18. The cradle uses a deliberately offset centre; the offset accommodates the source's varying clearance rather than forcing an arbitrary concentric silhouette. Hardware features hang from independent datums: gear radius or cradle-clearance edits must not move screw pilots, board retainers or axle seats.

The gear-pocket design is intended to work with the **flange-ring approach**. The flange ring is a separate component and is not included or newly qualified by this repository. A ring's actual seating offset, spool position, bearing fit and end float must all be considered together.

## Radial runout versus axial wobble

![Kinematic clearance illustration](images/runout-clearance.png)

**Radial excursion** increases the required radius in the plane of the gear. The nominal pocket coverage radius is R100.32 for an R99.32 gear: 1.0 mm of radial envelope allowance. An assumed 0.5 mm radial excursion would consume half that allowance. This arithmetic is not a measured runout value or a full bearing/spool tolerance stack. It does not establish clearance elsewhere in the assembly.

**Axial wobble** moves the rim toward the side wall. For a gear-axis tilt θ about a transverse axis through the gear centre, the rim's axial displacement component is approximately `R × sin(θ)`. At R99.32, 0.25° produces about 0.433 mm and 1° about 1.733 mm. Translation, end float and axial face runout add to the relevant direction of motion. Do not confuse these millimetres with radial radius allowance.

Pocket depth adds local axial clearance to the existing gap; it is not the total allowable wobble. The nominal cut is 0.6 mm, but **the bottom sector is wall-limited to 0.15 mm** in the delivered model. Actual exported right-body ray checks at Z−24.18 and radii 90, 97, 99.32, 99.82 and 100 all move the wall from X−82.27 to X−82.42. The sections above show that relief. The accepted full-rim gate checks the available wall sectors on both halves, including the bottom sector.

The retained pocket-adjacent web measures about **1.23 mm** at the minimum sampled station, against the 1.2 mm design gate. That wall constraint explains why increasing the nominal pocket depth cannot supply the same gain at every azimuth. The separate cap-side locating-wall checks measured about 1.38 mm right / 1.67 mm left. These are sampled checks, not a proof of the minimum thickness at every mathematical point.

No total safe tilt, measured runout, maximum speed, or dynamic life is claimed. A full tolerance budget needs the installed ring's actual offset, axial gap, bearing/end float, gear face runout, spool geometry and load. The drawings make the clearance mechanism visible; they do not replace those measurements.

## Why the front bars fit this way

Each half has one bar, two repeated square keys and a broad seating shoulder. The keys are 6.0 mm wide/deep, on 84.0 mm centres; sockets are 6.3 mm for 0.15 mm running clearance per side. A 0.4 mm tip lead guides entry. Matching 0.8 mm, 45° root tapers register X/Y with zero nominal seated taper gap. The shoulder sets Z.

The body's shoulder is Z116.95; key tips end at Z119.95, making the body 244.9 mm tall. The bar restores the original Z124.95 feed end, with 3 mm overlap below the key-tip plane. It prints flat as an 8 mm-tall part; the supplied print model places its shoulder at Z0. The key pockets have a 6.3 mm roof span, so bridge performance still needs practical checking.

Final retention uses the original AMS front-tab capture, not a new fastener. Fit the bars while the joined bodies are loosely placed, **before final front-tab engagement and body-screw tightening**. Removal requires releasing that capture and any PCB retention crossing the split. The local path checks support a 3.15 mm lift to clear the keys; no full AMS-box solid was available, so whole-unit installation and hand/tool access remain unverified.

## Modeling and evidence boundaries

The native builder uses named mechanical datums and repeated primitives: extrusions, slots, circles, tapers, chamfers and patterns. Original source meshes informed measurements and checks; they do not supply traced outlines to construct this CAD. The immutable RFID reference meshes are used only by the no-added-material export guard.

The RFID pocket remains under the original strict removal-only gate. A 0.05 mm digital interface check is not a promise of 0.05 mm printed accuracy; shrinkage, extrusion width, layer orientation and hardware variation remain physical variables.
