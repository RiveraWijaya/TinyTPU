# TinyTPU branch comparison

## Branch snapshots

| Branch | Commit | RTL files | Test files |
| --- | --- | ---: | ---: |
| `version1` | `f653e9b34ad4` | 10 | 39 |
| `version2` | `5533e103326c` | 10 | 39 |

## Interface compatibility

Result: **PASS**

| Field | Version 1 | Version 2 | Match |
| --- | --- | --- | :---: |
| `project.top_module` | tt_um_4x4TPU | tt_um_4x4TPU | yes |
| `project.clock_hz` | 33000000 | 33000000 | yes |
| `project.tiles` | 3x2 | 3x2 | yes |
| `pinout` | mapping | mapping | yes |

## Changed implementation files

| Status | Path |
| --- | --- |
| `M` | `docs/info.md` |
| `M` | `info.yaml` |
