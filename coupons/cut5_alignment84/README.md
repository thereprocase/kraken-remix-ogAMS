# Two-key alignment coupons — production 84 mm pitch

**Both handed pairs pass CAD checks. Physical fit is untested.** These separate coupons test simultaneous seating of two nominal cut5 keys without printing the full body. Accepted bodies, root release manifest and the completed single-key set are preserved and hash-checked. No production geometry or printer settings were changed.

## Downloads

| Part | STEP | 3MF |
|---|---|---|
| left_keys_84_nominal | [STEP](artifacts/left_keys_84_nominal.step) | [3MF](artifacts/left_keys_84_nominal.3mf) |
| left_sockets_84_nominal | [STEP](artifacts/left_sockets_84_nominal.step) | [3MF](artifacts/left_sockets_84_nominal.3mf) |
| right_keys_84_nominal | [STEP](artifacts/right_keys_84_nominal.step) | [3MF](artifacts/right_keys_84_nominal.3mf) |
| right_sockets_84_nominal | [STEP](artifacts/right_sockets_84_nominal.step) | [3MF](artifacts/right_sockets_84_nominal.3mf) |

## Artifacts and dimensions

Each stem below has a native STEP and a geometry-only 3MF under `artifacts/`. Print matching handed pairs; do not cross-pair left/right. One edge notch identifies right, two identify left, on both pieces. Notches are in the middle of the connecting strip, away from the actual joint pads.

| File stem | Footprint bounds, mm | Print height |
|---|---|---:|
| `right_keys_84_nominal` | X −10..94; Y −5.20..5.20 | 6 mm |
| `right_sockets_84_nominal` | X −10..94; Y −5.20..7.154 | 8 mm |
| `left_keys_84_nominal` | X −10..94; Y −5.20..7.20 | 6 mm |
| `left_sockets_84_nominal` | X −10..94; Y −5.20..7.20 | 8 mm |

All parts start at print Z0. Each has two joint centers at local **X0 and X84, Y0**. Keys are 6 × 6 × 3 mm above a 3 mm base. Sockets have 6.3 mm running opening, 3.15 mm depth and 4.85 mm roof. Per-side and tip clearance is 0.15 mm. Production 0.8 mm, 45° zero-gap root tapers and 0.4 mm key-tip leads are unchanged. Socket roof bridges remain 6.3 mm.

## What is retained from production

The geometry is a native Boolean crop of the accepted right M3 and left M4 cut5 STEP parts, not a mesh trace or a reconstruction of their walls. Each local crop window is 20 × 16 mm around a key/socket. A 4 mm-wide strip joins the windows, leaving a 64 mm span between their edges. Original geometry can occupy less than the window; the crop never adds stock to fill it.

The local shoulder faces, socket shape, thin skins, curved outer surfaces and roof are retained. Native production coordinates are recorded in `ORIGINAL-BUILD.json`: right centers X−13.07/+70.93; left X−73.83/+10.17, all at Y48.88 and shoulder Z116.95. Parts are translated into print coordinates without rotation or scaling.

Every measured production wall whose exit lies inside a local window is compared against the coupon. Long spans of original material outside a window are intentionally truncated and listed separately in the validation data. The left outer pad also retains its nearby X-facing production skin; it is not replaced by a symmetric block.

| Pair / local key X | Minimum retained wall | Roof | Shoulder contact area |
|---|---:|---:|---:|
| Right / 0 | 1.401 mm | 4.850 mm | 150.270 mm² |
| Right / 84 | 1.401 mm | 4.850 mm | 150.270 mm² |
| Left / 0 | 1.401 mm | 4.850 mm | 120.570 mm² |
| Left / 84 | 1.401 mm | 4.850 mm | 190.270 mm² |

Shoulder section footprints inside all four windows match production within 0.001 mm². The reported retained-wall surface differences are below 0.000001 mm. The 0.05 mm comparison tolerance was not relaxed.

## Comparison with the single-key set

The earlier single-key coupons isolate running-clearance sensitivity using 0.10/0.15/0.20 mm sockets and thicker surrounding blocks. This set uses only nominal 0.15 mm fit, actual local walls and two interfaces at production pitch. It can expose spacing mismatch, asymmetric seating and rocking that a single key cannot.

The narrow strips are deliberately more compliant than a full body/platform. Away from identification notches, an ideal rectangular 4 × 3 mm male strip has out-of-plane second moment of area 9 mm⁴; the 4 × 8 mm female strip has 170.7 mm⁴. Those are section properties, not a full-part stiffness simulation. The notches locally reduce strip width to 3.4 mm. The male strip can flex to accommodate a pitch/height mismatch that a full body might resist; avoid squeezing or bending it into place during the test.

Conversely, the long narrow coupon may bow or twist differently from the broad production platform. It has different mass, cooling and restraint, and prints its keys after a 3 mm base rather than near the top of a 244.9 mm body. It does not reproduce whole-body shrink, warp, rigidity, two-half seam constraint or AMS-tab capture. Passing these coupons supports a later physical test; it does not certify the production assembly.

## Proposed physical comparison

Print each pair in the supplied orientation: male base down with keys up; female shoulder/open socket mouths down. No supports are modeled. Keep the intended body material/profile and existing bridge settings; record them. No material profile is embedded and no shrink compensation is added. PETG remains a provisional project assumption, not a material qualification.

Inspect and measure both printed center spacings and strip flatness before assembly. Compare nominal single-key fit first, then lower each matching two-key socket strip straight onto both keys together. Record whether both shoulders contact simultaneously, any gap at each pad, rocking and withdrawal force by feel. Repeat five times without forcing or flexing the strip; compare left/right and recheck flatness. A coupon that seats only while bent is not a clean fit result. Do not sand the tapers or change production dimensions before recording the initial result and obtaining owner direction.

## Validation

`ORIGINAL-VALIDATION.json` records four valid one-solid native STEPs and four closed one-component 3MF meshes. Print bounds and Z0 placement pass. Layer sections at 0.2 mm have broad bed contact and no disconnected islands; roof bridge layers are recorded. This is a geometric screen, not a prescribed layer setting or a physical bridge test.

Independent delivered-mesh sections recover **84.000 mm pitch for keys and sockets**, 6.000/6.300 mm straight widths, 0.150 mm per-side clearance and zero seated-taper gap. Retained wall/roof probes and shoulder sections compare directly with accepted production meshes. Far-field crop faces are explicitly excluded from claims of original wall thickness.

Five native STEP insertion positions have zero overlap for both pairs. Forty-one mesh positions pass the same 0.001 mm³ numerical intersection budget as production cut5; maximum coincident-facet residue is 0.000026 mm³. Seated tapers obstruct ±0.05 mm X/Y displacement, and shoulders obstruct downward motion. Moving only the second key by +0.30 mm creates 3.250 mm³ collision while the first key/base stay fixed, demonstrating that the gate detects a pitch error.

These are local standard-part coupons. They do not requalify any full-body variant, installation path, clip retention or print job. This set supports a future owner-approved physical test; none has been performed by this work.


## Reproduce this set

Run `python coupons/rebuild.py --output coupon-build` from the repository root with the [CAD dependencies](../../requirements.txt). The wrapper builds in a new directory and compares against these accepted coupon exports. The included validation JSON records the original complete local fit/path checks. No printer settings or submitted jobs are included.
