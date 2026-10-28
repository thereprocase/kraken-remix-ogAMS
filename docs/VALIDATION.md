# Validation scope

The distributed bodies are the accepted **0.05 mm** standard and clearance-pocket releases, in full-height and cut5 forms. The table below describes the primary pocket cut5 pair; all variants are indexed in [body versions](BODY-VARIANTS.md). Their hashes and original artifact identities are in [RELEASE.json](RELEASE.json). No acceptance is inferred from image appearance or a global volume-match percentage.

| Gate | Evidence / result |
|---|---|
| Critical hardware interfaces | **109 right + 101 left, all PASS**, on the restored cut5 assemblies; maximum delivered probe distance 0.049886 mm |
| Interface families | AMS locating/mounting faces; feeder seats, noses, stops and screws; peg/axle seats; rollers; hub lands/pilots; seam; board retainers; RFID pocket/access; ferrite slot |
| Cut5-specific checks | Both pocket configurations PASS; [per-gate results](CUT5-CHECKS.json) |
| Split parts | Native-valid single solids; negligible numerical body/bar intersection; assembled exports agree with the separate parts |
| Print height | Bodies 244.9 mm; bars 8 mm in their flat print pose |
| Insert fit | 6 mm keys, 6.3 mm sockets, 0.15 mm running clearance per side; 84 mm pitch; shoulder and seated tapers checked |
| Registration and access | Mis-seating negative check; local axial insertion/removal; both insertion orders with opposite half/bar in place |
| Seam | Both assembled and shortened pairs pass the sampled slide checks |
| RFID | Strict no-added-material export guard against unchanged prior-pocket fixtures; 1e−6 mm³ numerical volume limit |
| Gear pocket | Removal only; native 6° taper; R100.32 coverage checks including bottom azimuth; minimum sampled adjoining web about 1.23 mm |
| Printability checks | Flat-bar layer connectivity, socket side/roof stock, cable-ledge chamfer, nose feet and whole-body thin-patch screening |

[INTERFACE-CHECKS.json](INTERFACE-CHECKS.json) lists each interface's purpose, received part, dimensions, sample count, source and CAD probe deviations, and result. The evidence is a curated copy of the accepted checks with source-report hashes, excluding local paths and development logs. The full accepted cut5 study also covered the standard configuration: 420 hardware checks across four configurations. All four cut5 configurations and the four accepted full-height configurations are now distributed. [Additional reproduction evidence](REPRODUCTION-ADDITIONAL.json) covers the newly packaged sets. No body geometry was revised for this expansion.

The accepted uncut parameter matrix exercised radial clearance 3.0/3.5/4.0 mm, gear radius 98.32/100.32 mm and combined maximum 100.32 + clearance 4.0 on both halves. Hardware datums remain independent of those changes. A separate 72 mm spool-width regression moved the related bay features together. These checks support the original parameter ranges; they do not qualify arbitrary future edits.

## Whole-body deviation gate (v5 bodies and later)

Since the v5 bodies (2026-10-28) every released body is compared with humebeam's original body of the same side, taken from his support-box ASA project (left: part 52 of assembly 53; right: part 56 of assembly 57). `prints/pctg-2026-10-28-v5/source/deviation_check.py` registers his body to ours by bounding-box minimum X and Y with both bed ends at print Z 0, slices both at every 0.2 mm, reports his-minus-ours and ours-minus-his area per layer, and lists every connected region whose surfaces differ by more than 0.3 mm (the region survives a 0.15 mm erosion) with its height, bounds, area and thickness class. Each listed region must fall inside an allow-list entry carrying a reason: the gear pocket, the cut5 split and keys, the v4 underside cuts, the v5 rear feet, the cable-bundle entry, the trough cable exit, and the accepted-release features whose bounds are named in the script. Any unmatched region fails the gate. Regions thinner than 0.3 mm are the native rebuild's skin offsets; they are summed per layer and never block. The JSON for both sides is kept with the release evidence (`prints/pctg-2026-10-28-v5/evidence/<side>-deviation.json`). Registration by bounding box and 0.2 mm sampling make this a geometric audit of where the remix departs from the original, not a box-fit certificate.

## Reproduction

The published package is rebuilt independently before publication. `rebuild.py` creates a fresh output directory, runs the native body builder and the insert split directly without an intermediate STEP round-trip, and applies the strict RFID gate. `verify.py --build build` compares the generated parts against the distributed STEP/3MF files. [REPRODUCTION.json](REPRODUCTION.json) records that comparison.

The reproduction check requires valid one-solid STEP parts, matching native face count and vertices, native volume difference below 0.01 mm³, and print-mesh symmetric difference below 0.1 mm³. These are reproducibility tests against the accepted files, not an independent repeat of every original-source hardware measurement. The two immutable mesh fixtures under `cad/reference/` are validation inputs only; they do not generate the CAD outlines.

## What PASS does not mean

- **Physical accuracy:** 0.05 mm is the digital interface comparison gate. It does not promise printed accuracy, thermal-shrink compensation or a successful hardware fit in every material.
- **Whole-machine installation:** no full AMS-box solid or complete stock-feeder solid was available. Retention uses a local box-tab proxy and feeder clearance envelopes. The loose-placement installation sequence, full-unit tilt/lowering, hand/tool access and actual cable routing need physical confirmation.
- **Continuous collision proof:** path checks sample positions. Straight keys support the local axial withdrawal argument, but sampling is not a proof for every arbitrary motion.
- **Global minimum wall:** wall screening samples opposed surface patches, supplemented with explicit socket side/roof rays. It is not a mathematical global minimum-thickness proof. The original source-matched roller blind-stop is a recorded thin-feature exception.
- **Board specification:** board and connector dimensions were inferred from the existing cavities; actual hardware drawings were unavailable.
- **Runout and strength:** pocket envelope checks do not certify dynamic runout, spool-clamp loads, creep, fatigue or maximum operating speed. See [engineering notes](ENGINEERING.md).

Check the seam and front-bar fit before committing to the large body prints. The zero-gap seated tapers, first-layer flare and 6.3 mm socket-roof bridges need the chosen printer/material to behave as intended. No complete body print or complete AMS installation is certified by this release.

## Separate rings and fit coupons

The stock-size pentagon ring family has its own source-interface and mesh/STEP export checks. It does not inherit the body's 0.05 mm hardware acceptance or a claim of physical fit across all sizes. The original 55.5 mm pair and earlier round flanges are preserved byte-for-byte. Coupon acceptance covers only the local joint and print orientation; their complete reports and isolated reproduction results are under [coupons](../coupons/README.md).
