# TinyTPU version comparison

The `main` branch is the common comparison branch for TinyTPU. The buildable hardware implementations live on `version1` and `version2`, including their RTL, Tiny Tapeout manifests, simulation tests, documentation, and generated layout previews.

## Branches

| Branch | Contents | Layout |
| --- | --- | --- |
| `version1` | Version 1 RTL and tests | [Open Version 1](https://riverawijaya.github.io/TinyTPU/version1/) |
| `version2` | Version 2 RTL and tests | [Open Version 2](https://riverawijaya.github.io/TinyTPU/version2/) |

The [layout homepage](https://riverawijaya.github.io/TinyTPU/) displays both versions. Each version page provides its PNG and SVG render, GDS and OAS downloads, and a 3D viewer link.

## Automated comparison

The comparison workflow runs `test/compare_branches.py` on updates to `main`. It checks that:

- both implementation branches contain their manifest, top module, documentation, and test entry points;
- every source listed in each branch's Tiny Tapeout manifest exists;
- the top module, clock frequency, tile size, and pinout match between versions.

It also records changed files without treating implementation differences as failures. The generated `comparison-report.md` is shown in the workflow summary and uploaded as the `comparison-report` artifact.

Run the same check locally from a clone that has both branches:

```console
python -m pip install -r test/requirements.txt
python test/compare_branches.py --output comparison-report.md
```
