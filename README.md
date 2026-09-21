# TinyTPU

TinyTPU is a 4×4 INT6 matrix multiplication accelerator designed for Tiny Tapeout. This repository continues the [original team project](https://github.com/HynixCJR/ttsky-miniTPU) from the 2026 University of Toronto ASIC Hackathon.

## Explore the versions

| Branch | Purpose | Layout |
| --- | --- | --- |
| `main` | Comparison branch | No separate GDS preview |
| `version1` | Version 1 design | [PNG, SVG, GDS, OAS, and 3D viewer](https://riverawijaya.github.io/TinyTPU/version1/) |
| `version2` | Version 2 design | [PNG, SVG, GDS, OAS, and 3D viewer](https://riverawijaya.github.io/TinyTPU/version2/) |

The [layout homepage](https://riverawijaya.github.io/TinyTPU/) shows only Version 1 and Version 2. A successful GDS build updates that version's layout files and its preview in `docs/`.

## Project files

- [Project documentation](docs/info.md) explains the design and its interface.
- [Pages source](site/) builds the Version 1 and Version 2 comparison site.
- RTL sources and tests live on the [`version1`](../../tree/version1) and [`version2`](../../tree/version2) branches.
