"""Lambda layer declarations and local artifact compatibility evidence."""

from __future__ import annotations

import re
from pathlib import Path

from .compat import Archive, emit, finding, python_version, read_json, report

SOURCE = "https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html"
API_SOURCE = "https://docs.aws.amazon.com/lambda/latest/api/API_GetLayerVersionByArn.html"


def native_findings(name: str, header: bytes, architecture: str) -> list[dict]:
    findings = []
    if header.startswith(b"\x7fELF"):
        if len(header) < 20 or header[4] not in (1, 2) or header[5] not in (1, 2):
            return [finding("invalid-elf", name, "ELF header is truncated or invalid.", SOURCE)]
        machine = int.from_bytes(header[18:20], "little" if header[5] == 1 else "big")
        expected = {"x86_64": 62, "arm64": 183}[architecture]
        if machine != expected or header[4] != 2:
            findings.append(
                finding(
                    "native-architecture",
                    name,
                    f"ELF machine {machine}, class {header[4]} does not match {architecture} (64-bit).",
                    SOURCE,
                )
            )
    elif name.endswith((".so", ".pyd", ".dll", ".dylib")):
        findings.append(
            finding(
                "non-linux-native",
                name,
                "Native library lacks an ELF header; verify Linux packaging.",
                SOURCE,
            )
        )
    return findings


def scan_archive(path: Path, runtime: str, architecture: str) -> dict:
    version = python_version(runtime)
    abi = f"{version[0]}{version[1]}"
    archive = Archive(path)
    findings: list[dict] = []
    native = 0
    try:
        files = sorted(name for name, info in archive.members.items() if not info.is_dir())
        if not any(name.startswith("python/") for name in files):
            findings.append(
                finding(
                    "missing-python-directory",
                    path.name,
                    "Python layer ZIP needs a top-level python/ directory.",
                    SOURCE,
                )
            )
        for name in files:
            match = re.search(r"(?:^|/)python/lib/python(3\.\d+)/site-packages/", name)
            if match and "python" + match[1] != runtime:
                findings.append(
                    finding(
                        "python-library-path",
                        name,
                        f"Version-specific import path targets python{match[1]}, not {runtime}.",
                        SOURCE,
                    )
                )
            match = re.search(r"\.(?:cpython-|cp)(\d{2,3})(?:[-.]|$)", name)
            if match and match[1] != abi:
                findings.append(
                    finding(
                        "cpython-abi",
                        name,
                        f"Filename declares CPython {match[1]}; target is {abi}.",
                        SOURCE,
                    )
                )
            if name.endswith((".so", ".pyd", ".dll", ".dylib")):
                native += 1
                findings.extend(native_findings(name, archive.prefix(name, 64), architecture))
        return report(
            "layers",
            findings,
            files=len(files),
            native_libraries=native,
            runtime=runtime,
            architecture=architecture,
            limitations="Static paths, named CPython ABIs and ELF headers only; no dependency resolution, GLIBC symbol check, imports or runtime execution. A matching declaration is not proof of compatibility.",
        )
    finally:
        archive.close()


def scan_metadata(data: dict, runtime: str, architecture: str) -> dict:
    python_version(runtime)
    rows = data.get("layers")
    if not isinstance(rows, list) or len(rows) > 1000:
        raise ValueError("fixture needs a layers array (at most 1000 entries)")
    findings = []
    for index, layer in enumerate(rows):
        if not isinstance(layer, dict):
            raise ValueError("each layer must be an object")
        name = layer.get("LayerVersionArn", f"layer[{index}]")
        if not isinstance(name, str) or not name:
            raise ValueError("LayerVersionArn must be a nonempty string")
        for field, target, code in (
            ("CompatibleRuntimes", runtime, "declared-runtime"),
            ("CompatibleArchitectures", architecture, "declared-architecture"),
        ):
            values = layer.get(field, [])
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                raise ValueError(f"{field} must be an array of strings")
            if not values:
                findings.append(
                    finding(
                        code + "-unknown",
                        name,
                        f"{field} is absent or empty; compatibility is undeclared.",
                        API_SOURCE,
                        "review",
                    )
                )
            elif target not in values:
                findings.append(
                    finding(
                        code + "-mismatch",
                        name,
                        f"{target} is not in {field}: {', '.join(values)}. This metadata is a declaration, not a runtime test.",
                        API_SOURCE,
                    )
                )
    return report(
        "layers",
        findings,
        layers=len(rows),
        runtime=runtime,
        architecture=architecture,
        limitations="Publisher metadata only. Content is not downloaded or executed; omitted declarations remain unknown.",
    )


def live_metadata(function: str, region: str, profile: str | None = None) -> dict:
    try:
        import boto3
    except ImportError as exc:
        raise ValueError("live lookup requires python-pivot[aws]") from exc
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    client = session.client("lambda", region_name=region)
    configuration = client.get_function_configuration(FunctionName=function)
    # Do not return environment values, presigned content URLs or unrelated data.
    rows = []
    for attached in configuration.get("Layers", []):
        layer = client.get_layer_version_by_arn(Arn=attached["Arn"])
        rows.append(
            {
                key: layer[key]
                for key in ("LayerVersionArn", "CompatibleRuntimes", "CompatibleArchitectures")
                if key in layer
            }
        )
    return {"layers": rows}


def run(args) -> int:
    python_version(args.runtime)
    if not args.live and (args.function or args.region or args.profile):
        raise ValueError("AWS lookup arguments require --live")
    if args.archive:
        result = scan_archive(Path(args.archive), args.runtime, args.architecture)
    else:
        if args.live:
            if not args.function or not args.region:
                raise ValueError("--live requires --function and --region")
            data = live_metadata(args.function, args.region, args.profile)
        else:
            data = read_json(Path(args.fixture))
        result = scan_metadata(data, args.runtime, args.architecture)
    return emit(result, args)
