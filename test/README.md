# Comparison test

This directory belongs to the `main` comparison branch. The implementation branches keep their cocotb and RTL simulation tests in their own `test/` directories.

`compare_branches.py` reads the comparison rules from the root `info.yaml`, resolves `version1` and `version2` from local or `origin/*` refs, validates their required files and compatible interface metadata, and writes a changed-file report.

```console
python -m pip install -r test/requirements.txt
python test/compare_branches.py --output comparison-report.md
```
