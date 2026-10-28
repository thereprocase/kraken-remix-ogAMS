# Spring pairs for hard plastic spools

Pentagon corners bite into cardboard, but a hard plastic hub does not give. These rings have a **round spigot 0.2 mm under the hole** (a friction fit) and **four spring fingers** that bow out **0.2 mm past the hole wall** and flex back as the ring goes in. The fingers hold the ring in the hub when the gear shaft is pulled out.

| Feature | Value |
|---|---:|
| Support radius | Nominal hole radius − 0.20 mm |
| Fingers | 4, each 30° wide, 1.3 mm thick, in 1.0 mm slots |
| Finger peak | Nominal hole radius + 0.20 mm, at 75 % of the way from the finger root to the lead-in |
| Finger root | 1.6 mm above the flange or lip |
| Lead-in | Last 2.0 mm, 1.9 mm radial, as the pentagon rings |
| Holder core | humebeam's ring of the next smaller whole size, kept inside the same core cylinder as the pentagon pairs |
| Smallest hole | 51.6 mm: below that the finger slots would leave less than 0.8 mm of wall in front of humebeam's holder core |

**Flange sets.** *Normal*: 2.2 mm gear-side flange and 0.6 mm cap-side lip. *Skinny*: 0.4 mm on both sides, for holders where the extra 2.0 mm of stack does not fit. humebeam's original 0.4 mm cap lip tends to break during bed removal and handling, which is why normal thickens it. The spigot of each side rises by the added base thickness, so it still inserts as deep as the stock ring.

| Spool hole · set | Gear side | Cap side |
|---|---|---|
| 52.1 mm · normal | [3MF](models/kraken-spool-ring-52.1-mm-spring-gear-side-2.2mm-flange.3mf) · [STL](models/kraken-spool-ring-52.1-mm-spring-gear-side-2.2mm-flange.stl) · [STEP.gz](https://github.com/thereprocase/kraken-remix-ogAMS/releases/download/rings-2026-10-28/kraken-spool-ring-52.1-mm-spring-gear-side-2.2mm-flange.step.gz) | [3MF](models/kraken-spool-ring-52.1-mm-spring-cap-side-0.6mm-lip.3mf) · [STL](models/kraken-spool-ring-52.1-mm-spring-cap-side-0.6mm-lip.stl) · [STEP.gz](https://github.com/thereprocase/kraken-remix-ogAMS/releases/download/rings-2026-10-28/kraken-spool-ring-52.1-mm-spring-cap-side-0.6mm-lip.step.gz) |
| 52.1 mm · skinny | [3MF](models-skinny/kraken-spool-ring-52.1-mm-spring-gear-side-0.4mm-flange.3mf) · [STL](models-skinny/kraken-spool-ring-52.1-mm-spring-gear-side-0.4mm-flange.stl) · [STEP.gz](https://github.com/thereprocase/kraken-remix-ogAMS/releases/download/rings-2026-10-28/kraken-spool-ring-52.1-mm-spring-gear-side-0.4mm-flange.step.gz) | [3MF](models-skinny/kraken-spool-ring-52.1-mm-spring-cap-side-0.4mm-lip.3mf) · [STL](models-skinny/kraken-spool-ring-52.1-mm-spring-cap-side-0.4mm-lip.stl) · [STEP.gz](https://github.com/thereprocase/kraken-remix-ogAMS/releases/download/rings-2026-10-28/kraken-spool-ring-52.1-mm-spring-cap-side-0.4mm-lip.step.gz) |

52.1 mm is a measured hard plastic hub. Generate other holes from 51.6 to 95 mm with the [Kraken ring generator](https://thereprocase.github.io/kraken-rings/) (choose *Hard plastic · spring fingers*) or with

```sh
python rings/source/generate_family.py --output spring-build --core spring --sizes 52.1 [--set skinny]
```

The first spring rings (52.1 mm, with the earlier 1.5 mm / 0.4 mm flanges) were printed in PCTG on 2026-10-28; their fit had not been reported when these files were published. Geometry checks: [normal](VALIDATION.json), [skinny](VALIDATION-skinny.json).

Original Kraken and stock ring design: **[humebeam](https://www.printables.com/model/1788417-kraken-revolutionary-bambu-lab-ams)**. Remix: **thereprocase**, under [CC BY-NC 4.0](../../LICENSE.md).
