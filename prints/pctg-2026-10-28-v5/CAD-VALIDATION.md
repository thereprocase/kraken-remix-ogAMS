# v5 bodies and drop-in bars: CAD checks

Checked 2026-10-28 on the files in this folder, with the release check scripts of the 2026-10-16 workspace (copied,
not modified, except the load-path check noted below) and two new scripts in `source/`. Evidence JSON is in `evidence/`.
Nothing here is a physical fit or print certificate.

## Bodies

| Check | Left | Right |
|---|---|---|
| Exported native solid | valid, one solid, STEP re-import volume error 1e-8 mm3 | valid, one, 8e-9 mm3 |
| Hardware contacts, 0.05 mm (`check_candidate.py`) | 101/101 PASS, max probe error 0.0499 mm | 109/109 PASS, 0.0500 mm |
| Cap PTFE corridors, 10 and 20 mm bend | PASS (overlap 3e-4 / 6e-5 mm3) | PASS (0 / 0) |
| RFID no-addition export gate | PASS | PASS |
| Export integrity, installation, STEP-vs-mesh sampled error (`revalidate.py`) | PASS, 0.0491 mm | PASS, 0.0487 mm |
| Feed end above native Z 84 identical to the accepted body | 0 mm3 | 0 mm3 |
| Whole-body sampled wall screen (`revalidate.py --walls`) | PASS, minimum 1.00002 mm | PASS, 1.00003 mm |
| Reinforcement masks (`reclip_masks.py`) | dense and walls unchanged, 0 mm3 outside the solid | same |
| Load strips, box lands, cable entry (`check_loadpaths_joint_v5.py`) | shaft and roller sections outside the two fill zones, seating land, wall above the foot zone: 0 mm3 change; reported zones: end-wall foot 862.5 mm3, widened web, seam fill | same; foot zone 926.8 mm3 |
| Seam slide and cross-half bar insertion (v5 bars) | 0 overlap at all sampled positions | same |
| Layer screen, 0.2 mm contours (`layer_screen.py`) | 1 island, identical to the v4 baseline (board retainer, 0.54 mm2 at Z 200.6) | 2 islands, identical to baseline |
| Added / removed against the v4 body | +10.4 cm3 / 0 (tessellation noise only) | +9.6 cm3 / 0 |

The load-path script is the 2026-10-16 `check_loadpaths_joint.py` with one region split: the cap box locating wall is
checked for identity above native Z -91 and the v5 foot zone below it is reported as a volume. Everything else in that
script is unchanged; it now takes the v5 bars for the cross-half insertion path.

## Bed face

| Print Z | Left v4 | Left v5 | Right v4 | Right v5 |
|---:|---:|---:|---:|---:|
| 0.15 | 1415 mm2, 5 islands | 2026 mm2, 1 region | 1016 mm2, 5 islands | 1516 mm2, 1 region |
| 3 | 1799 | 1987 | 1376 | 1564 |
| 6 | 2133 | 2277 | 1681 | 1825 |
| 10 | 2511 | 2629 | 2019 | 2136 |

humebeam's bodies: 1640 (left) and 1249 (right) mm2 at the bed, one region each. The v5 layers between 0.15 and 3 mm shrink
by 39 and 48 mm2 as the web flanges taper at 45 degrees; nothing above that is smaller than the layer below it except
where the v4 geometry already was.

## Deviation gate against humebeam's bodies

`source/deviation_check.py` (owner's release rule, 2026-10-28): registration by bounding-box minimum X and Y, bed ends
at Z 0; 1224 layers at 0.2 mm; every region thicker than 0.3 mm matched against the allow-list in the script.

| | Left | Right |
|---|---:|---:|
| Status | PASS, 0 unmatched of 9470 listed regions | PASS, 0 unmatched of 9225 |
| Largest explained families (area summed over layers) | A3b v4 deep-tray ramp 49460 mm2; A7c seam wall and joints 37736; A7f trough 37988; B1 deep-tray bay 33957; A2 bar region 23242; A4 v5 feet 9558 his-minus-ours and 20141 ours-minus-his | A3b 48762; A7d cap end wall 37051; B1 30940; A7f 28040; A2 22287; A4 10741 / 14221 |
| Thin skin offsets under 0.3 mm | summed per layer in the JSON, never listed | same |

The allow-list has 22 entries; each names the CAD features behind it (`source/deviation_check.py`, `allow_list`). Entries
that describe skins carry a thickness cap (A7g 1.5 mm, A7h 0.6 mm, B4 2.0 mm, B7 2.5 mm) so a missing wall foot like the
v4 bed face could not hide under them. Reviewers should read the bounds as the audit's scope, not as approval of every
difference inside them.

## Drop-in bars

| Check | Left | Right |
|---|---|---|
| Keys unchanged: split body equals the accepted cut5 body | 1.38 mm3 symmetric difference (mirror tessellation) | 0.0 mm3 |
| Bar material under each key in the slot | 0 mm3, 0 mm3 | 0 mm3, 0 mm3 |
| Key swept 20 mm along the drop from 0.05 mm lift | max 2e-5 mm3 interference | 1e-5 mm3 |
| Vertical float: free at 0.65 mm, stopped at 1.0 mm | 1e-5 mm3 / 5.13 mm3 contact | same |
| Bar volume | 12840 mm3 | 12813 mm3 |
| Repository rebuild (`cad/feed_end_insert.py left pocket --fit-clearance 0.30 --drop-in 0.70`) | 0.0 mm3 against the released bar; its body 0.0 mm3 against the accepted body | not run |

## Test slice (lead's PCTG recipe plus the safety brim)

`source/prepare_v5.py`: the released sliced project with the v5 body swapped in, bar removed, humebeam's support boxes
kept, outer brim 0.5 mm gap 5 mm wide, 0.3 mm layers, 0.6 mm nozzle, 30 mm/s first layer.

| | Left | Right |
|---|---:|---:|
| Estimated time | 10 h 37 min | 10 h 34 min |
| PCTG | 497.8 g | 494.1 g |
| Brim / support | yes / none | yes / none |
| First layer | body in one island (2165 mm2 of 0.8 mm-wide paths) plus the two support boxes; brim 5 mm at 0.5 mm gap confirmed in the G-code header ([image](images/left-firstlayer.png)) | body in one island (2164 mm2) plus the two boxes ([image](images/right-firstlayer.png)) |

The lead's own slice remains controlling for the print; this slice only confirms the first layer and that the recipe
accepts the v5 files.

## Not verified

AMS box depth slack for the 3 mm forward slide (owner's measurement pending), the box rear wall under the widened web
flanges, physical PCTG fit of the 0.30 mm slots and 0.70 mm float, printed accuracy of any 0.05 mm figure, and full
assembly in a box.
