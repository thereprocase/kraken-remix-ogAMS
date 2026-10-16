# Body versions

All files here are copied from the accepted **0.05 mm digital-interface release**. There are two independent choices: a standard wall or a tapered gear-clearance pocket, and a full-height body or a shortened body with its matching removable bar. The same hardware locations and original fit clearances apply.

**Use one matching left/right configuration.** Cut5 bars are required to restore the assembled end; do not mix loose bars between variants on the assumption that their fit was checked. Full-height bodies are one-piece and need no bar.

| Configuration | Main-body print height | Parts per AMS |
|---|---:|---:|
| Pocket cut5 (selected) | 244.9 mm | Two bodies + two bars |
| Standard cut5 | 244.9 mm | Two bodies + two bars |
| Pocket full-height | 249.9 mm | Two bodies |
| Standard full-height | 249.9 mm | Two bodies |

## Pocket / shortened with bars

| Part | STEP | Geometry-only 3MF |
|---|---|---|
| Right body | [STEP](../models/right-body-pocket_cut5.step) | [3MF](../models/right-body-pocket_cut5.3mf) |
| Right front-bar | [STEP](../models/right-front-bar-pocket_cut5.step) | [3MF](../models/right-front-bar-pocket_cut5.3mf) |
| Left body | [STEP](../models/left-body-pocket_cut5.step) | [3MF](../models/left-body-pocket_cut5.3mf) |
| Left front-bar | [STEP](../models/left-front-bar-pocket_cut5.step) | [3MF](../models/left-front-bar-pocket_cut5.3mf) |

Rebuild in a new directory:

```sh
python rebuild.py --variant pocket --body-height cut5 --output build-pocket-cut5
python verify.py --build build-pocket-cut5
```

## Standard / shortened with bars

| Part | STEP | Geometry-only 3MF |
|---|---|---|
| Right body | [STEP](../models/right-body-standard_cut5.step) | [3MF](../models/right-body-standard_cut5.3mf) |
| Right front-bar | [STEP](../models/right-front-bar-standard_cut5.step) | [3MF](../models/right-front-bar-standard_cut5.3mf) |
| Left body | [STEP](../models/left-body-standard_cut5.step) | [3MF](../models/left-body-standard_cut5.3mf) |
| Left front-bar | [STEP](../models/left-front-bar-standard_cut5.step) | [3MF](../models/left-front-bar-standard_cut5.3mf) |

Rebuild in a new directory:

```sh
python rebuild.py --variant standard --body-height cut5 --output build-standard-cut5
python verify.py --build build-standard-cut5
```

## Pocket / full-height

| Part | STEP | Geometry-only 3MF |
|---|---|---|
| Right body | [STEP](../models/right-body-pocket_full.step) | [3MF](../models/right-body-pocket_full.3mf) |
| Left body | [STEP](../models/left-body-pocket_full.step) | [3MF](../models/left-body-pocket_full.3mf) |

Rebuild in a new directory:

```sh
python rebuild.py --variant pocket --body-height full --output build-pocket-full
python verify.py --build build-pocket-full
```

## Standard / full-height

| Part | STEP | Geometry-only 3MF |
|---|---|---|
| Right body | [STEP](../models/right-body-standard_full.step) | [3MF](../models/right-body-standard_full.3mf) |
| Left body | [STEP](../models/left-body-standard_full.step) | [3MF](../models/left-body-standard_full.3mf) |

Rebuild in a new directory:

```sh
python rebuild.py --variant standard --body-height full --output build-standard-full
python verify.py --build build-standard-full
```

[Download all body variants as one ZIP](https://github.com/thereprocase/kraken-remix-ogAMS/releases/download/cad-library-2026-10-15/all-body-variants-step-3mf.zip). It contains the 24 STEP/3MF files, attribution and file hashes.

## Evidence and limits

[Release identities](RELEASE.json) map every download to the accepted artifact and original manifest. [Primary reproduction](REPRODUCTION.json) and [additional reproduction](REPRODUCTION-ADDITIONAL.json) compare fresh builds with the supplied solids and print meshes. The [validation notes](VALIDATION.md) state the hardware, wall and installation limits.

The 0.02 mm investigation is not part of this release. Physical manufacture, complete box installation and every possible spool assembly remain outside the digital acceptance claim. For orientation and bar installation, follow the [main README](../README.md).
