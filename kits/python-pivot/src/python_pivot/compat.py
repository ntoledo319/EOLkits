"""Shared bounded, read-only inputs and explicit coverage for compatibility checks."""

from __future__ import annotations

import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

MAX_INPUT = 32 * 1024 * 1024
MAX_MEMBERS = 10000
MAX_EXPANDED = 250 * 1024 * 1024


def read_bytes(path: Path, limit: int = MAX_INPUT) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"expected a regular, non-symlink file: {path}")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"input exceeds {limit} bytes: {path}")
    return data


def read_json(path: Path) -> dict:
    value = json.loads(read_bytes(path))
    if not isinstance(value, dict):
        raise ValueError("JSON input must be an object")
    return value


def python_version(runtime: str) -> tuple[int, int]:
    match = re.fullmatch(r"python(3)\.(\d{1,2})", runtime)
    if not match:
        raise ValueError("target runtime must be python3.MINOR (for example python3.12)")
    return int(match[1]), int(match[2])


def finding(code: str, subject: str, message: str, source: str, severity: str = "high") -> dict:
    return dict(code=code, subject=subject, severity=severity, message=message, source=source)


def report(kind: str, findings: list[dict], **coverage) -> dict:
    return dict(schema_version=1, kind=kind, findings=findings, coverage=coverage)


def emit(result: dict, args) -> int:
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{result['kind']}: {len(result['findings'])} finding(s)")
        for item in result["findings"]:
            print(f"[{item['severity']}] {item['subject']} — {item['code']}: {item['message']}")
        print("Coverage: " + json.dumps(result["coverage"], sort_keys=True))
    return int(bool(args.strict and result["findings"]))


class Archive:
    """Inspect ZIP members in place; never extract or execute them."""

    def __init__(self, path: Path):
        import io

        self.zip = zipfile.ZipFile(io.BytesIO(read_bytes(path)))
        self.members: dict[str, zipfile.ZipInfo] = {}
        infos = self.zip.infolist()
        if len(infos) > MAX_MEMBERS:
            raise ValueError(f"archive exceeds {MAX_MEMBERS} entries")
        total = 0
        for info in infos:
            name = info.filename
            parts = PurePosixPath(name).parts
            if (
                not name
                or name.startswith("/")
                or "\\" in name
                or ".." in parts
                or any(ord(char) < 32 for char in name)
                or ":" in name
                or str(PurePosixPath(name)) != name.rstrip("/")
            ):
                raise ValueError("archive contains an unsafe or ambiguous path")
            if name in self.members:
                raise ValueError("archive contains duplicate member names")
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)):
                raise ValueError("archive contains a link or special file")
            if info.flag_bits & 1:
                raise ValueError("encrypted archives are not supported")
            if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError("only stored and deflated ZIP members are supported")
            total += info.file_size
            if total > MAX_EXPANDED or info.file_size > max(1, info.compress_size) * 200:
                raise ValueError("archive exceeds expanded size or compression ratio limits")
            self.members[name] = info
        if not any(not item.is_dir() for item in infos):
            raise ValueError("archive has no files to inspect")

    def prefix(self, name: str, limit: int = 4096) -> bytes:
        with self.zip.open(self.members[name]) as stream:
            return stream.read(limit)

    def close(self) -> None:
        self.zip.close()
