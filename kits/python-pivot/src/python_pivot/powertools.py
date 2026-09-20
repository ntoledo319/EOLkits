"""Exact-release Powertools metadata matrix, with explicit unsupported coverage."""

from __future__ import annotations

import re
from pathlib import Path

from . import audit
from .compat import emit, finding, python_version, read_json, report

# Exact PyPI publisher metadata retrieved 2026-09-10. These are release snapshots,
# not claims that every release in a major version has the same Python support.
RELEASES = {
    "2.43.1": {
        "requires_python": "<4.0.0,>=3.8",
        "python_versions": ["3.8", "3.9", "3.10", "3.11", "3.12"],
    },
    "3.0.0": {
        "requires_python": "<4.0.0,>=3.8",
        "python_versions": ["3.8", "3.9", "3.10", "3.11", "3.12"],
    },
    "3.15.1": {
        "requires_python": "<4.0.0,>=3.9",
        "python_versions": ["3.9", "3.10", "3.11", "3.12", "3.13"],
    },
    "3.34.0": {
        "requires_python": "<4.0.0,>=3.10",
        "python_versions": ["3.10", "3.11", "3.12", "3.13", "3.14"],
    },
}
SOURCE = "https://pypi.org/project/aws-lambda-powertools/"
UPGRADE = "https://docs.aws.amazon.com/powertools/python/latest/upgrade/"


def permits(spec: str, runtime: str | None) -> bool:
    target = python_version(runtime) + (0,) if runtime else None
    allowed = True
    for part in spec.split(","):
        match = re.fullmatch(r"\s*(>=|<=|==|!=|>|<)\s*(\d+)\.(\d+)(?:\.(\d+))?\s*", part)
        if not match:
            raise ValueError("Requires-Python must use numeric ==, !=, <, <=, > or >= clauses")
        bound = tuple(int(value or 0) for value in match.groups()[1:])
        if target is None:
            continue
        if bound[:2] == target[:2] and (bound[2] != 0 or match[1] in (">", "<=", "==", "!=")):
            raise ValueError(
                "Requires-Python needs an exact interpreter patch version; this command targets Python minor versions"
            )
        checks = {
            ">=": target >= bound,
            "<=": target <= bound,
            "==": target == bound,
            "!=": target != bound,
            ">": target > bound,
            "<": target < bound,
        }
        allowed = allowed and checks[match[1]]
    return allowed


def metadata(path: Path | None = None) -> dict:
    records = {version: dict(row) for version, row in RELEASES.items()}
    if path:
        data = read_json(path)
        info = data.get("info")
        if (
            not isinstance(info, dict)
            or not isinstance(info.get("name"), str)
            or info["name"].replace("_", "-").lower() != "aws-lambda-powertools"
        ):
            raise ValueError("metadata must be the PyPI JSON response for aws-lambda-powertools")
        version = info.get("version")
        requires = info.get("requires_python")
        classifiers = info.get("classifiers", [])
        if (
            not isinstance(version, str)
            or not re.fullmatch(r"\d+\.\d+\.\d+", version)
            or not isinstance(requires, str)
            or not isinstance(classifiers, list)
            or not all(isinstance(item, str) for item in classifiers)
        ):
            raise ValueError(
                "metadata needs a stable version, Requires-Python and string classifiers"
            )
        permits(requires, None)  # Validate syntax without assuming the selected runtime.
        records[version] = {
            "requires_python": requires,
            "python_versions": [
                item.removeprefix("Programming Language :: Python :: ")
                for item in classifiers
                if re.fullmatch(r"Programming Language :: Python :: 3\.\d+", item)
            ],
        }
    return records


def check(version: str, runtime: str, records: dict) -> list[dict]:
    python_version(runtime)
    row = records.get(version)
    if row is None:
        return [
            finding(
                "powertools-release-unknown",
                version,
                "Exact release is absent from the snapshot. Supply its PyPI JSON via --metadata; no major-version inference was made.",
                SOURCE,
                "review",
            )
        ]
    source = SOURCE + version + "/"
    if not permits(row["requires_python"], runtime):
        return [
            finding(
                "powertools-python-requirement",
                version,
                f"{runtime} does not meet publisher Requires-Python {row['requires_python']}.",
                source,
            )
        ]
    if runtime.removeprefix("python") not in row["python_versions"]:
        return [
            finding(
                "powertools-python-unadvertised",
                version,
                f"Requires-Python permits {runtime}, but this release does not advertise that minor version in its classifiers; test it explicitly.",
                source,
                "review",
            )
        ]
    return []


def run(args) -> int:
    if sum(bool(value) for value in (args.matrix, args.package_version, args.path)) != 1:
        raise ValueError(
            "choose exactly one of --matrix, --package-version or a dependency-file path"
        )
    python_version(args.runtime)
    records = metadata(Path(args.metadata) if args.metadata else None)
    rows = []
    findings = []
    if args.matrix:
        versions = sorted(records, key=lambda value: tuple(map(int, value.split("."))))
    elif args.package_version:
        versions = [args.package_version]
    else:
        path = Path(args.path)
        parser = (
            audit.parse_pipfile
            if path.name == "Pipfile"
            else (audit.parse_pyproject if path.suffix == ".toml" else audit.parse_requirements)
        )
        versions = []
        entries = [(name, spec) for name, spec in parser(path) if name == "aws-lambda-powertools"]
        if not entries:
            findings.append(
                finding(
                    "powertools-not-declared",
                    path.name,
                    "No Powertools requirement was found in the supported dependency tables.",
                    SOURCE,
                    "review",
                )
            )
        for _, spec in entries:
            match = re.fullmatch(r"==\s*(\d+\.\d+\.\d+)", spec or "")
            if not match:
                findings.append(
                    finding(
                        "powertools-unresolved-version",
                        path.name,
                        "A non-exact requirement cannot identify a release. Supply the resolved --package-version.",
                        SOURCE,
                        "review",
                    )
                )
            else:
                versions.append(match[1])
    for version in versions:
        issues = check(version, args.runtime, records)
        findings.extend(issues)
        rows.append(
            {
                "version": version,
                **records.get(version, {}),
                "target": args.runtime,
                "result": "review" if issues else "declared-compatible",
                "source": SOURCE + version + "/",
            }
        )
    result = report(
        "powertools",
        findings,
        runtime=args.runtime,
        matrix=rows,
        snapshot_date="2026-09-10",
        supplied_metadata=args.metadata is not None,
        limitations="Exact release metadata only; Python classifiers are publisher declarations, not tests of extras, native dependencies, Lambda layers or migration behavior. Review the v3 upgrade guide separately.",
        upgrade_guide=UPGRADE,
    )
    return emit(result, args)
