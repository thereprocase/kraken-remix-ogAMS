# Kraken remix for the original AMS

A native, parametric body remix of [**Kraken – Revolutionary Bambu Lab AMS** by **humebeam**](https://www.printables.com/model/1788417-kraken-revolutionary-bambu-lab-ams), for the original Bambu Lab AMS. Please start with the original designer's parts list and assembly instructions. This repository contains the replacement bodies and removable front bars; it is not the complete Kraken kit or an AMS 2 Pro conversion.

This version combines the **tapered gear-clearance pocket** with **5 mm shorter bodies and separate feed-end bars**. The pocket works with the flange-ring approach; the separate spool flange ring is not included here. Hardware diameters and intended running clearances are retained. The native builder uses mechanical datums, extrusions, circles, slots, tapers and patterns.

![Cel-shaded render of the released bodies and removable front bars](docs/images/body-overview.png)

Blue: shortened bodies. Orange: front bars, lifted for illustration. These renders use the actual released geometry.

## Models

Print one of each part. STEP and 3MF represent the same geometry; the 3MF files contain geometry only, without printer settings or toolpaths.

| Part | Print mesh | Native CAD |
|---|---|---|
| Right body, pocket cut5 | [3MF](models/right-body-pocket_cut5.3mf) | [STEP](models/right-body-pocket_cut5.step) |
| Left body, pocket cut5 | [3MF](models/left-body-pocket_cut5.3mf) | [STEP](models/left-body-pocket_cut5.step) |
| Right front bar, flat | [3MF](models/right-front-bar-pocket_cut5.3mf) | [STEP](models/right-front-bar-pocket_cut5.step) |
| Left front bar, flat | [3MF](models/left-front-bar-pocket_cut5.3mf) | [STEP](models/left-front-bar-pocket_cut5.step) |

Body height is **244.9 mm**, down from 249.9 mm. The feed end is the top of the upright print. Each bar restores the removed end geometry and overlaps the body by 3 mm, making the bar 8 mm tall in its supplied flat pose. Bodies are modeled upright; place their lowest face on the build plate. The bars are already translated onto their broad shoulder at Z=0.

Two keys per half have **84 mm spacing**, **6 mm nominal width/depth**, **6.3 mm running sockets** and **0.15 mm clearance per side**. The 0.8 mm seating tapers have zero nominal seated gap; the shoulder sets height. These fits need a physical check before committing to the bodies.

The gear pocket uses a gear-tip radius of 99.32 mm plus 1.0 mm radial margin, 0.6 mm nominal depth and a 6° taper. Its bottom sector becomes shallower where needed to retain the wall. The main cradle's running clearance is a separate parameter.

![Feed-end joint detail](docs/images/front-bar-detail.png)

## Installation condition

The bars install while the bodies are **loosely placed in the AMS, before the front tabs are engaged and the body screws tightened**. They are captured by the restored box interfaces after final seating. They cannot be removed with the whole unit fully locked into the box.

1. Check the seam dovetail and the bar keys, tapers and shoulders with the intended material and printer settings. Clean first-layer flare and burrs without changing the locating geometry.
2. Join the shortened bodies and install the stock feeders, rollers and hardware with the bars absent. Route tubes and cables.
3. Place the assembly loosely into the AMS. Keep the front tabs disengaged, body screws loose and PCB unfastened.
4. Lower each bar onto its keys and shoulder. Either order clears the modeled local envelopes.
5. Engage the restored front clips, finish seating, secure the PCB and tighten the body screws using the original designer's instructions.
6. For removal, release the box capture and any PCB retention spanning the split, then lift the bar. A 3.15 mm lift clears the keys.

This sequence is a design assumption awaiting a complete physical assembly. Local retention uses a box-tab proxy: no full AMS box solid or complete stock-feeder CAD was available. Whole-unit lowering, tilt, tool access and cable management remain unverified. Board dimensions were inferred from the existing cavities; actual board and connector fits need hardware confirmation.

## Accuracy and validation

This is the accepted **0.05 mm digital-interface release**. The distributed models are byte-for-byte copies of the accepted clearance-pocket cut5 exports. Hardware fits and the strict RFID **no-added-material** gate are retained.

The accepted cut5 suite covers both standard and pocket variants: 420/420 original hardware checks across four configurations, plus split-part, insert-path, seam and print-orientation checks. This repository distributes the two pocket configurations. See [validation and limits](docs/VALIDATION.md) and the [release file identities](docs/RELEASE.json).

![Sections through the keys and gear pocket](docs/images/sections.png)

[Engineering notes](docs/ENGINEERING.md) explain the joint dimensions, radial runout versus axial wobble, wall-limited pocket depth and the assumptions behind the checks. They include a clearance diagram, not a claim of measured runout or a completed physical installation.

![Radial runout and axial wobble explained](docs/images/runout-clearance.png)

## Reproduce the models

The source was exercised with Python 3.12 on Linux and the versions in [requirements.txt](requirements.txt). In your own environment:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python rebuild.py --output build
```

`build/models/` contains the four pocket cut5 parts as STEP and 3MF. The script refuses to overwrite an existing output directory. It builds and splits the native bodies directly with the reusable key/socket primitive, checks native validity and the strict RFID no-added-material gate, and writes a separate build manifest. Logs and intermediate geometry remain in the ignored build directory.

To reproduce the same cut5 design without the gear pocket:

```sh
OPENBLAS_NUM_THREADS=1 python rebuild.py --variant standard --output build-standard
```

Shared dimensions are in [cad/right.py](cad/right.py); the left half is mirrored with functional overrides in [cad/left.py](cad/left.py). The removable-bar dimensions are in [cad/feed_end_insert.py](cad/feed_end_insert.py). The two NPZ files under `cad/reference/` are immutable export-guard fixtures, not printable parts; no reference mesh outlines construct the CAD.

Check the distributed files with:

```sh
sha256sum -c SHA256SUMS
python verify.py --build build
```

`verify.py --build build` compares the regenerated STEP solids and print meshes with the distributed models. STEP headers and ZIP timestamps can vary on regeneration, so fresh file hashes need not equal the release hashes. Geometry and the checked dimensions are the reproduction criteria. Parameter edits require renewed geometry, hardware and installation validation.

## Credit and license

Original design: **humebeam**, [Kraken – Revolutionary Bambu Lab AMS](https://www.printables.com/model/1788417-kraken-revolutionary-bambu-lab-ams). Remix: **thereprocase**. Changes include the native parametric reconstruction, tapered pockets, removable front bars and preserved hardware interfaces. This remix is not endorsed by the original designer.

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/), with attribution and noncommercial use required. See [LICENSE.md](LICENSE.md).
