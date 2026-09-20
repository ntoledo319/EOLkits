"""Print or create a reviewable GitHub Actions workflow; never publish it."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def content() -> str:
    return (
        files("python_pivot")
        .joinpath("templates/python-compatibility.yml")
        .read_text(encoding="utf-8")
    )


def run(args) -> int:
    text = content()
    if args.apply:
        if not args.out:
            raise ValueError("--apply requires --out")
        path = Path(args.out)
        # An exclusive create avoids overwriting an existing workflow or following
        # a symlink. Parent directories must already exist for reviewability.
        root = Path.cwd().resolve()
        try:
            relative = path.absolute().relative_to(root)
        except ValueError as exc:
            raise ValueError("workflow output must stay within the current directory") from exc
        cursor = root
        for part in relative.parts:
            if part == "..":
                raise ValueError("workflow output must not traverse parent directories")
            cursor /= part
            if cursor.is_symlink():
                raise ValueError("workflow output path must not contain symlinks")
        if not path.parent.is_dir():
            raise ValueError("output parent must exist and output path must not contain symlinks")
        with path.open("x", encoding="utf-8") as stream:
            stream.write(text)
        print(f"Created {path}. Review the configured paths before enabling the workflow.")
    else:
        print(text, end="")
    return 0
