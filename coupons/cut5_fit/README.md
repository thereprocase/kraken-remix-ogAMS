# Cut5 fit-test coupons

Four separate local coupons assess the existing joint before printing full bodies. **CAD checks pass; nothing has been printed.** Accepted body files, source and root manifest are unchanged; the original release hashes were verified before and after generation and during validation.

## Downloads

| Part | STEP | 3MF |
|---|---|---|
| key_common | [STEP](artifacts/key_common.step) | [3MF](artifacts/key_common.3mf) |
| socket_1_c010 | [STEP](artifacts/socket_1_c010.step) | [3MF](artifacts/socket_1_c010.3mf) |
| socket_2_c015_nominal | [STEP](artifacts/socket_2_c015_nominal.step) | [3MF](artifacts/socket_2_c015_nominal.3mf) |
| socket_3_c020 | [STEP](artifacts/socket_3_c020.step) | [3MF](artifacts/socket_3_c020.3mf) |

## Files and dimensions

All STEP and 3MF files are in `artifacts/`. Print one common key and each socket. The two-notch socket is the production nominal. The comparison parts are experiments, not replacement body designs.

| File stem | Edge ID | Running clearance per side | Running opening | Pocket depth / roof |
|---|---|---:|---:|---:|
| `key_common` | No notches | Common 6 × 6 mm key | — | Key engagement 3 mm |
| `socket_1_c010` | 1 notch | 0.10 mm | 6.20 × 6.20 mm | 3.10 / 4.90 mm |
| `socket_2_c015_nominal` | 2 notches | **0.15 mm** | **6.30 × 6.30 mm** | **3.15 / 4.85 mm** |
| `socket_3_c020` | 3 notches | 0.20 mm | 6.40 × 6.40 mm | 3.20 / 4.80 mm |

Every footprint is 20 × 16 mm. The male base is 3 mm thick and total key coupon height is 6 mm. Socket blocks are 8 mm high, matching the production insert's local thickness. Each identification notch is 1 mm wide/deep on one outer edge, clear of the joint. Total native material volume is 8.314 cm³ before slicer infill decisions.

All variants directly reuse `feed_end_insert.key_pair`, including the 0.4 mm tip lead, 7.6 mm square root and 0.8 mm 45° seating collar. The comparison changes the existing `fit_clearance` parameter, which affects **both side and tip gap**. The seating taper remains zero-gap in all three cases; this is not a taper-clearance experiment. Larger running clearance does not cure a tight seating taper.

## Print orientation and material assumptions

Use each 3MF as supplied, with Z0 on the bed. Print the male coupon with its broad base down and key up. Print sockets with the **open pocket mouth down**, broad shoulder on the bed and closed roof above. Do not flip them to avoid bridging: the intended orientation reproduces the production insert's mouth, taper and ceiling. The 6.2/6.3/6.4 mm ceilings are short enclosed bridges. Geometric checks require no support islands; physical bridge quality remains untested.

These are geometry-only 3MFs, without printer, material or bridge-setting overrides. No bridge settings were changed. Use the intended full-body material and existing printer/profile/nozzle/layer settings for the comparison, and record them. Unfilled PETG is a provisional material assumption from the project context, not a newly selected or qualified material; if the body uses another material, test that material instead. No shrink compensation is built into the coupon geometry. The 0.2 mm layer audit below is a geometric test, not a prescribed slicer setting.

## Proposed physical test

1. Print the four parts together under the intended body/insert process. Keep the edge-notch IDs visible. Record material, nozzle, layer height, profile and any existing compensation settings. No print job has been submitted by this work.
2. Let the parts cool. Inspect bridge roofs, pocket mouths, key leads and shoulder flatness. Remove only loose strings initially; record elephant foot or other defects before sanding or reaming any fit surface.
3. Measure the key's straight section, socket mouth/accessible straight opening and overall heights with available tools. Note that the 7.6 mm flared mouth is larger than the running opening, and the closed pocket limits caliper access.
4. Start with the three-notch 0.20 mm socket, then nominal two-notch, then one-notch 0.10 mm. Keep the male base flat; lower each socket over the key without twist or clamping. Note free travel, where resistance starts, whether the shoulder seats flush on all sides, and whether it withdraws with a straight pull. Stop rather than force a binding sample.
5. At full seating, check rocking/lateral motion and look for a shoulder gap against a light. Record any gap with a suitable gauge. Repeat each fit five times, then retry nominal to reveal wear or polishing. Do not treat a coupon's friction grip as retention: the production insert is held by the AMS tab after final seating.
6. Return observations before changing production parameters. Tightness only at final seating across all three suggests taper/first-layer fit; differences during travel suggest running clearance. Poor ceilings suggest a print-process result. None of these observations alone authorizes a production redesign or bridge-setting change.

Suggested log:

| ID | Free travel | Seats flush / measured gap | Rocking | Withdrawal | After 5 cycles | Visible defects |
|---|---|---|---|---|---|---|
| 3 / 0.20 | | | | | | |
| 2 / 0.15 nominal | | | | | | |
| 1 / 0.10 | | | | | | |

## Validation and limits

`ORIGINAL-VALIDATION.json` records PASS for all four delivered STEP/3MF pairs: one valid native solid and one closed manifold mesh per part, millimeter units, expected bounds, bed at Z0, matching native/mesh volumes, broad first-layer contact and no disconnected islands at 0.2 mm layer sampling. Bridge ceiling layers are recorded explicitly.

Independent rays through delivered meshes recover all four intended running gaps per socket and zero taper gap at the seated collar. Five native STEP path positions have zero intersection volume. Forty-one mesh path samples per socket pass the production 0.001 mm³ intersection tolerance. Nominal coincident seating facets leave 0.00001475 mm³ mesh residue; native overlap is zero. Each seated socket obstructs ±0.05 mm lateral movement and downward shoulder penetration. A deliberately misaligned 0.5 mm socket produces 6.785 mm³ collision and is correctly rejected by the collision criterion.

This is a **single-key local fit test**. It does not reproduce the 84 mm two-key spacing, full platform stiffness, 244.9 mm tall body printing history, original thin local walls, AMS clip retention, seam interactions, installed feeder clearances or full-box installation. The socket coupon's surrounding stock is thicker than the thinnest production socket wall. Body and insert warp, multi-key alignment, zero-gap taper fit and physical bridge performance still require assessment. Existing cut5 loose-seating installation assumptions remain unchanged.


## Reproduce this set

Run `python coupons/rebuild.py --output coupon-build` from the repository root with the [CAD dependencies](../../requirements.txt). The wrapper builds in a new directory and compares against these accepted coupon exports. The included validation JSON records the original complete local fit/path checks. No printer settings or submitted jobs are included.
