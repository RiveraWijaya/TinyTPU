#!/usr/bin/env python3
"""Validate and summarize the TinyTPU implementation branches."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def ref_exists(ref: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def resolve_ref(branch: str) -> str:
    for candidate in (branch, f"origin/{branch}"):
        if ref_exists(candidate):
            return candidate
    raise RuntimeError(
        f"Cannot find {branch!r}; fetch it with "
        f"'git fetch origin {branch}:refs/remotes/origin/{branch}'."
    )


def load_yaml_from_ref(ref: str, path: str) -> dict[str, Any]:
    content = git("show", f"{ref}:{path}")
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError(f"{ref}:{path} must contain a YAML mapping")
    return data


def path_exists(ref: str, path: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{ref}:{path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def nested_value(data: dict[str, Any], dotted_path: str) -> Any:
    value: Any = data
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(dotted_path)
        value = value[part]
    return value


def tracked_files(ref: str, prefix: str) -> list[str]:
    return [
        path
        for path in git("ls-tree", "-r", "--name-only", ref, "--", prefix).splitlines()
        if path
    ]


def escape_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("comparison-report.md"),
        help="Markdown report path (default: comparison-report.md)",
    )
    args = parser.parse_args()

    config = yaml.safe_load((ROOT / "info.yaml").read_text(encoding="utf-8"))
    branch_entries = config.get("branches", [])
    if len(branch_entries) != 2:
        raise ValueError("info.yaml must define exactly two comparison branches")

    branches = [entry["name"] for entry in branch_entries]
    refs = {branch: resolve_ref(branch) for branch in branches}
    manifests: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    required_paths = config.get("required_paths", [])
    for branch in branches:
        ref = refs[branch]
        for path in required_paths:
            if not path_exists(ref, path):
                errors.append(f"{branch} is missing required path `{path}`")

        try:
            manifest = load_yaml_from_ref(ref, "info.yaml")
            manifests[branch] = manifest
        except (RuntimeError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"Could not read {branch} manifest: {exc}")
            continue

        source_files = manifest.get("project", {}).get("source_files", [])
        if not isinstance(source_files, list) or not source_files:
            errors.append(f"{branch} has no project.source_files list")
        else:
            for source in source_files:
                source_path = f"src/{source}"
                if not path_exists(ref, source_path):
                    errors.append(
                        f"{branch} manifest references missing source `{source_path}`"
                    )

    field_rows: list[tuple[str, Any, Any, bool]] = []
    if len(manifests) == len(branches):
        left, right = branches
        for field in config.get("compatible_fields", []):
            try:
                left_value = nested_value(manifests[left], field)
                right_value = nested_value(manifests[right], field)
                matches = left_value == right_value
                field_rows.append((field, left_value, right_value, matches))
                if not matches:
                    errors.append(f"Interface field `{field}` differs between branches")
            except KeyError:
                errors.append(f"Interface field `{field}` is missing from a manifest")

    left, right = branches
    diff_lines = git(
        "diff",
        "--name-status",
        refs[left],
        refs[right],
        "--",
        "src",
        "test",
        "info.yaml",
        "docs/info.md",
    ).splitlines()

    report = [
        "# TinyTPU branch comparison",
        "",
        "## Branch snapshots",
        "",
        "| Branch | Commit | RTL files | Test files |",
        "| --- | --- | ---: | ---: |",
    ]
    for branch in branches:
        ref = refs[branch]
        sha = git("rev-parse", "--short=12", ref).strip()
        report.append(
            f"| `{branch}` | `{sha}` | {len(tracked_files(ref, 'src'))} | "
            f"{len(tracked_files(ref, 'test'))} |"
        )

    report.extend(
        [
            "",
            "## Interface compatibility",
            "",
            f"Result: **{'PASS' if not errors else 'FAIL'}**",
            "",
            "| Field | Version 1 | Version 2 | Match |",
            "| --- | --- | --- | :---: |",
        ]
    )
    for field, left_value, right_value, matches in field_rows:
        left_text = "mapping" if isinstance(left_value, dict) else escape_cell(left_value)
        right_text = "mapping" if isinstance(right_value, dict) else escape_cell(right_value)
        report.append(
            f"| `{field}` | {left_text} | {right_text} | "
            f"{'yes' if matches else 'no'} |"
        )

    report.extend(["", "## Changed implementation files", ""])
    if diff_lines:
        report.extend(["| Status | Path |", "| --- | --- |"])
        for line in diff_lines:
            parts = line.split("\t")
            status = parts[0]
            path = " -> ".join(parts[1:])
            report.append(f"| `{escape_cell(status)}` | `{escape_cell(path)}` |")
    else:
        report.append("No implementation files differ between the two branch snapshots.")

    if errors:
        report.extend(["", "## Validation errors", ""])
        report.extend(f"- {error}" for error in errors)

    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
