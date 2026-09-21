# TinyTPU

TinyTPU is a 4×4 INT6 matrix multiplication accelerator designed for Tiny Tapeout. This repository continues the [original team project](https://github.com/HynixCJR/ttsky-miniTPU) from the 2026 University of Toronto ASIC Hackathon.

## Explore the versions

| Branch | Purpose | Layout |
| --- | --- | --- |
| `main` | Comparison site, metadata, and branch checks | No separate GDS preview |
| `version1` | Version 1 implementation | [PNG, SVG, GDS, OAS, and 3D viewer](https://riverawijaya.github.io/TinyTPU/version1/) |
| `version2` | Version 2 implementation | [PNG, SVG, GDS, OAS, and 3D viewer](https://riverawijaya.github.io/TinyTPU/version2/) |

The [layout homepage](https://riverawijaya.github.io/TinyTPU/) shows only Version 1 and Version 2. A successful GDS build updates only that version's layout artifacts and preview. The main branch has no RTL implementation or GDS preview of its own.

## Comparison files

- [Comparison documentation](docs/comparison.md) explains the branch layout and automated checks.
- [Comparison test](test/README.md) validates both implementation branches and generates a Markdown report.
- [Pages source](site/) builds the Version 1 and Version 2 layout site.
- RTL sources, design documentation, and simulation tests live on the [`version1`](../../tree/version1) and [`version2`](../../tree/version2) branches.
