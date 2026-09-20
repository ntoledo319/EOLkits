"""Small, deterministic artifact helpers shared by the additive roadmap commands."""

from __future__ import annotations

import json
from pathlib import Path


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    source = Path(path)
    if source.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("JSON input exceeds the 64 MiB limit")
    return json.loads(source.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)


def json_text(value):
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def write_bundle(directory, files):
    """Create a private, previously absent directory; never overwrite user files."""
    target = Path(directory)
    if target.exists() or target.is_symlink():
        raise ValueError("Output directory already exists; choose a new bundle directory")
    target.mkdir(mode=0o700, parents=True)
    for name, content in files.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe artifact filename")
        path = target / relative
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(content if isinstance(content, bytes) else content.encode("utf-8"))
        path.chmod(0o700 if name.endswith(".sh") else 0o600)


def emit_report(report, out=None):
    text = json_text(report)
    if out:
        with Path(out).open("x", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text, end="")
