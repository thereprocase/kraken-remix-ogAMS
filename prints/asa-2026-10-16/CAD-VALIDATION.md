# Printable underside candidate — v4

Ready for Coordinator's final paired slicing and physical fit review; not published and not physically qualified. Right v4 removes the unnecessary added ferrite braces from v3. The holder retains its existing tray/seam roots. Left is the exact frozen v3 geometry. Accepted release and reinforcement files are unchanged.

## Geometry and purpose

- Cable entry: retain its15mm width and add a45° gabled roof with0.8mm crown. Removal only, outside the RFID skin.
- Deep tray: one45° underside ramp, preserving the full cradle backing cylinder, walls and complete right ferrite rails. Removes the former broad unsupported roof. No added ferrite brace or refill of its cable approach.
- Feeder noses: one constant-width oblique slot per bay,10mm/11mm, replacing the unnecessarily wide flare. Retains full stock feeder seats and mounting geometry. This supplies continuous backing beneath the former unsupported nose corners.
- Platform depth step: a2mm45° underside chamfer across both bays, stopping at the broad box-seating strip. Removes the abrupt ledge at nativeZ81.12 without trimming the seating land.

All constructions use existing named mechanical datums and simple cuts/extrudes. Net native material reduction: right5.793cm³, left6.730cm³. Original print orientation, cut5 height244.9mm, keys and accepted separate front bars retained.

## Checks

| Check | Right | Left |
|---|---|---|
| Exported native solid | Valid, one | Valid, one |
| Hardware contacts,0.05mm |109/109 PASS |101/101 PASS |
| Strict protected-baseline RFID no-addition |PASS |PASS |
| Existing installation checks, including RFID backing/connector and feeder noses |PASS |PASS |
|4mm PTFE corridors,10mm/20mm bend radius |PASS |PASS |
| Existing15mm main cable entry: native added obstruction |0 |0 |
| Whole-body sampled wall screen |PASS |PASS |
| Ordinary continuous wall minimum sampled |1.00003mm |1.00003mm |
| STEP/checked-mesh sampled bidirectional error |0.04810mm or less |0.04965mm or less |
| Delivered3MF vs checked vertices/triangles |PASS |PASS |
| Native geometry aboveZ84 vs accepted |0 changed volume |0 changed volume |
| Full outer cap locating wall and broad box seating strip |Native identical |Native identical |
| Insert axial removal,49 sampled positions |PASS |PASS |
| Cross-half insert path and seam slide |PASS |PASS |
| Reinforcement mask native containment |PASS; unchanged files |PASS; unchanged files |

Evidence: `reports/*-hardware-route.json`, `*-revalidation.json`, `*-walls.json`, `*-masks.json`, `loadpaths-joint.json`, and `*_export_gate.json`. Left v3 results carried forward only where delivered files are byte-identical; `left-retained.json` records this. The existing source-matched0.65mm roller blind-stop exception remains separately recorded by the wall screen; the1mm ordinary-wall figure does not erase it. Sampling is not a mathematical minimum-wall or Hausdorff proof.

The native20mm-wide shaft and roller load-analysis strips are exactly unchanged, as are their reinforcement masks. The earlier bounded net-section evidence therefore remains applicable to those strips. No new whole-body FEA or new absolute stiffness claim is made. Existing load assumptions and ASA anisotropy/creep limitations remain in `../../../reinforcement_20261016/readiness/READINESS.md`.

## Routing and printability

Humebeam's original assembly photos, PDF pages13,21,24,31 and34, informed the routing review: PTFE under the feeders toward the hub, black feeder cables toward the board, and hub cables through the middle-wall-adjacent entry. Main cable-entry clearance is preserved; its roof only opens further. Both cap-tube corridor checks pass. Actual flexible cable bundle dimensions, connector poses and tube bend ratings were not supplied; dry routing remains a physical acceptance check.

Coordinator's actual right-v2 slice, geometrically identical to right v3, removed the former9mm ledge outlier; remaining straight free span5.95mm with both geometric anchors. Left v3 actual slice removed its66mm outlier and also reports5.95mm maximum, both anchored. Left v4 retains those exact files. Right v4 removes added brace stock, so it still needs its own final slice/anchor screen; do not infer that its full toolpaths are identical to v2/v3.

The0.2mm full-height contour scan finds no new floating contour starts relative to the accepted bodies. The right-v3 extra ferrite island at printZ124.2 is gone. Remaining tiny starts are the same board-retainer/post features as baseline: right printZ200.6(area0.538mm²) and207.2(area0.252mm²), left200.6(area0.538mm²). Bounds match baseline and areas agree within0.000001mm². Coordinator reported no nearby emitted right paths at those flagged start layers or the following layer; final v4 path review remains controlling. Geometry growth screens alone do not qualify ASA bridging.

Support-free printing is the intent, pending the final slice review. No blanket internal support is recommended: it could trap support in routes, sockets or pockets. If a confirmed free roof remains, use accessible local support as the fallback, with removal checked against the actual routing. Original-geometry support-enforcer request remains parked; none are included in this candidate.

## Placement and recipe

Bodies and modifiers share their exact original raw coordinates. Apply the same transform to each parent and all its masks: identity rotation, Z+124.95 to bed, plus Coordinator's common XY placement. Do not independently center, rotate or drop modifiers. Body mask manifests include the4×4 matrix; resulting body Z is0..244.9. The P1S profile's carriage/tool offset must be included in G-code comparison: Coordinator established add2mm to emitted G-codeY before mapping back to mesh coordinates. That offset is not a CAD transform.

Local body recipe remains2walls/15% base, dense masks4walls/100%, wall masks4walls/15%. All four STEP/STL/NPZ mask files are unchanged byte-for-byte. Separate accepted flat bars remain uniform4walls/30%, with no bar masks. Polymaker ASA assumed. Coordinator's planned outer-only8mm body brim with0.15mm gap addresses adhesion, not unsupported roofs or whole-body warp. Its efficacy is not physically qualified.

Install the halves, route hardware/cables loosely, seat the bars fully on their shoulders, then complete box seating/capture and fastening. Verify the84mm two-key coupon in the actual ASA process first. Check cooled flatness, locating faces, screw starts, free spool/gear motion and cable slack before final tightening. Full AMS-box solid is unavailable; box-tab retention uses the existing local proxy. Whole-unit install sequence, thermal distortion, long-term creep and physical fit remain unqualified.

## Reproduction

Use the existing `WORKSPACE/venvs/kraken-cad/bin/python`; no installs. The frozen scripts are in `source/`. Copy that folder to a new sibling under `full/` before running (their `FULL` path is the script directory's parent), or use the matching originals in `full/printable_bottom_20261016/`.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 WORKSPACE/venvs/kraken-cad/bin/python full/printable_bottom_20261016/build_candidate.py right --mode channel --out /tmp/kraken-bottom-rebuild
# Same command with left rebuilds the retained geometry; archival left export files remain frozen.
```

For each side run `check_candidate.py SIDE OUT`, `revalidate.py SIDE OUT`, `revalidate.py SIDE OUT --walls`, and `reclip_masks.py SIDE OUT`; then `check_loadpaths_joint.py OUT`. `check_candidate.py` must precede `revalidate.py` because it writes the checked assembly mesh. The build refuses export on RFID addition. Layer screen uses existing remote `ANALYSIS_WORKSPACE/fdm/py` with `{right,left}-body.npz` inputs, script `layer_screen.py`, and an output JSON path. No packages installed.

`DELIVERY.json` binds parent/mask/bar files, hashes, placement and carried checks. `SHA256SUMS` freezes this candidate's deliverables and evidence. Accepted release manifest SHA256 remains `2e871508576ca4e7b8b694b8358af0eb499309b51a7f0e5eb1364f91ecc76cdb`;457 entries and37 selected-mask entries verified unchanged in `reports/PRESERVATION.json`.
