# Ring source and provenance

The 51 geometry-only 3MF files under `reference/` are humebeam's original `kraken-spool-ring-45-mm-100.3mf` through `kraken-spool-ring-95-mm-100.3mf`, supplied with [Kraken](https://www.printables.com/model/1788417-kraken-revolutionary-bambu-lab-ams). They retain the original bore, snap ribs and other holder interfaces. Original and derivative files share the repository's [CC BY-NC 4.0 license](../../LICENSE.md).

| Generator | Purpose |
|---|---|
| `rings_555.py` | Reproduce the earlier 55.5 mm pentagon pair (1.5 mm gear flange, 0.4 mm cap lip, published until 2026-10-28) from the original 55 mm input |
| `generate_family.py` | Build pentagon pairs (cardboard hubs) or spring pairs (`--core spring`, hard plastic hubs) for any size, each using its own source interface; a fractional size such as 53.4 uses the next smaller stock interface. `--set normal` (2.2 mm gear flange, 0.6 mm cap lip) or `--set skinny` (0.4 mm both) |
| `round_flange.py` | Build the round ring pairs in either flange set |
| `mesh3mf.py` | Read the source geometry; no printing presets or machine integration |

From the repository root with its CAD dependencies:

```sh
python rings/source/rings_555.py ring-555-build
python rings/source/generate_family.py --output pentagon-build [--set skinny]
python rings/source/generate_family.py --output brand-build --sizes 53.4 55.5 [--set skinny]
python rings/source/generate_family.py --output spring-build --core spring --sizes 52.1 [--set skinny]
python rings/source/round_flange.py rings/source/reference round-build [normal|skinny]
```

Use fresh output directories. The [55.5 mm reproduction evidence](REPRODUCTION-555.json) proves byte identity with the earlier 1.5 / 0.4 mm pair. Since 2026-10-28 the published 55.5 mm pair comes from `generate_family.py`, which matches that earlier pair within 0.0016 mm³ when given the same thicknesses. Each collection has its own geometry checks. [Reference interface envelopes](INTERFACE-ENVELOPES.json) record the inward-facing source surfaces used to confirm that the preserved core encloses the holder interface.

The generators retain source mesh surfaces at the holder interface and build the changed outside profiles procedurally. They are editable mesh construction, not a reconstruction of the unavailable original analytic CAD. The separate [STEP converter](../export_step.py) creates checked faceted solids. See the collection READMEs for numerical cleanup and physical-fit limits.

The family illustration is rendered from the actual STL facets by `render_family.py` (optional Matplotlib 3.11.2 and NumPy). It does not substitute an idealized drawing for the downloaded geometry.
