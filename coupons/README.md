# Small fit checks before the body prints

These coupons reproduce the removable front-bar joint described in the [main README](../README.md). They let you assess the chosen material and printing process without first making the two large bodies. They are separate test pieces, not body replacements.

| Set | Download page | What it checks |
|---|---|---|
| Single key + three sockets | [Files and instructions](cut5_fit/README.md) | 0.10, 0.15 and 0.20 mm running clearance; the 0.15 mm socket is production nominal |
| Two keys at 84 mm pitch, both sides | [Files and instructions](cut5_alignment84/README.md) | Simultaneous seating with actual local socket walls and shoulder shapes |

[Download both coupon sets as one ZIP](https://github.com/thereprocase/kraken-remix-ogAMS/releases/download/cad-library-2026-10-15/front-bar-fit-coupons.zip).

All eight parts have STEP and geometry-only 3MF files in their set's `artifacts` folder. The socket coupons print mouth-down, as the actual bars do; their short roof spans require bridging. Use the intended production material and profile. No print settings or machine actions are included.

The seating tapers have zero nominal gap in every coupon. More running clearance does not change that final seating fit. Two-key strips are more flexible than the body and have a different cooling/warp history; a successful coupon fit does not certify the complete assembly. Record the initial fit before altering surfaces or production dimensions.

[Release hashes](RELEASE.json), [independent rebuild results](REPRODUCTION.json), and each set's original and rebuilt validation reports accompany the files. All parts pass native validity, export and local insertion/registration checks. Physical fit remains untested by these CAD checks.

## Reproduction

With the repository's CAD dependencies, run from its root:

```sh
python coupons/rebuild.py --output coupon-build
```

This uses a new directory, rebuilds both sets from the native joint and accepted body/bar solids, runs the fit/path checks, and compares all eight parts with the downloads. The public files are left unchanged.
