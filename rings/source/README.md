# Ring source and provenance

The 51 geometry-only 3MF files under `reference/` are humebeam's original `kraken-spool-ring-45-mm-100.3mf` through `kraken-spool-ring-95-mm-100.3mf`, supplied with [Kraken](https://www.printables.com/model/1788417-kraken-revolutionary-bambu-lab-ams). They retain the original bore, snap ribs and other holder interfaces. Original and derivative files share the repository's [CC BY-NC 4.0 license](../../LICENSE.md).

| Generator | Purpose |
|---|---|
| `rings_555.py` | Reproduce the existing 55.5 mm pentagon pair from the original 55 mm input |
| `generate_family.py` | Build pentagon pairs for all 51 stock sizes, each using its own source interface |
| `round_flange.py` | Reproduce the earlier round gear-side flange family |
| `mesh3mf.py` | Read the source geometry; no printing presets or machine integration |

From the repository root with its CAD dependencies:

```sh
python rings/source/rings_555.py ring-555-build
python rings/source/generate_family.py --output pentagon-build
python rings/source/round_flange.py rings/source/reference round-flange-build
```

Use fresh output directories. The [55.5 mm reproduction evidence](REPRODUCTION-555.json) proves byte identity with the existing pair. The generalized stock-size family has its own [geometry checks](../stock-sizes/VALIDATION.json); it does not replace the 55.5 mm downloads. [Reference interface envelopes](INTERFACE-ENVELOPES.json) record the inward-facing source surfaces used to confirm that the preserved core encloses the holder interface.

The generators retain source mesh surfaces at the holder interface and build the changed outside profiles procedurally. They are editable mesh construction, not a reconstruction of the unavailable original analytic CAD. The separate [STEP converter](../export_step.py) creates checked faceted solids. See the collection READMEs for numerical cleanup and physical-fit limits.

The family illustration is rendered from the actual STL facets by `render_family.py` (optional Matplotlib 3.11.2 and NumPy). It does not substitute an idealized drawing for the downloaded geometry.
