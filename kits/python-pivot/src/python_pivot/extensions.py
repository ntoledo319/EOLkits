"""Inspect extension entrypoints without running untrusted executables."""

from __future__ import annotations

import re
from pathlib import Path

from .compat import Archive, emit, finding, python_version, report
from .layers import native_findings

SOURCE = "https://docs.aws.amazon.com/lambda/latest/dg/runtimes-extensions-api.html"


def scan(path: Path, runtime: str, architecture: str) -> dict:
    python_version(runtime)
    archive = Archive(path)
    findings: list[dict] = []
    try:
        entries = sorted(
            name
            for name, info in archive.members.items()
            if name.startswith("extensions/") and name.count("/") == 1 and not info.is_dir()
        )
        if not entries:
            findings.append(
                finding(
                    "no-extension-entrypoint",
                    path.name,
                    "No top-level extensions/ executable was found.",
                    SOURCE,
                    "review",
                )
            )
        for name in entries:
            info = archive.members[name]
            if not (info.external_attr >> 16) & 0o111:
                findings.append(
                    finding(
                        "extension-not-executable",
                        name,
                        "Entrypoint has no executable permission bits.",
                        SOURCE,
                    )
                )
            header = archive.prefix(name)
            if header.startswith(b"\x7fELF"):
                findings.extend(native_findings(name, header, architecture))
                findings.append(
                    finding(
                        "extension-native-review",
                        name,
                        "External native extension does not use the function's Python interpreter; verify its OS libraries and vendor support separately.",
                        SOURCE,
                        "review",
                    )
                )
                continue
            text = header.decode("utf-8", errors="replace")
            first = text.splitlines()[0] if text else ""
            if not first.startswith("#!"):
                findings.append(
                    finding(
                        "extension-launcher-unknown",
                        name,
                        "Entrypoint is neither an ELF executable nor a recognized shebang script.",
                        SOURCE,
                        "review",
                    )
                )
                continue
            interpreter = first[2:].strip().split()[0] if first[2:].strip() else ""
            bundled = interpreter.removeprefix("/opt/") if interpreter.startswith("/opt/") else ""
            if bundled and bundled in archive.members:
                findings.append(
                    finding(
                        "bundled-interpreter-review",
                        name,
                        "Bundled interpreter found; its Python version and libraries cannot be proven from a filename. Verify the extension's own runtime independently.",
                        SOURCE,
                        "review",
                    )
                )
                continue
            # Inspect Python shebangs, including /usr/bin/env python3.x. A shell
            # launcher can compute its interpreter, so it must remain unknown.
            match = re.search(r"(?:^|[/\s])python(?P<version>\d+(?:\.\d+)?)?(?:\s|$)", first[2:])
            if match:
                declared = match["version"]
                target = runtime.removeprefix("python")
                if declared and "." in declared and declared != target:
                    findings.append(
                        finding(
                            "extension-python-version",
                            name,
                            f"Entrypoint requests Python {declared}; migration target is {target} and no bundled interpreter was found.",
                            SOURCE,
                        )
                    )
                elif declared and declared.split(".")[0] != "3":
                    findings.append(
                        finding(
                            "extension-python-version",
                            name,
                            "Entrypoint requests a non-Python-3 interpreter.",
                            SOURCE,
                        )
                    )
                findings.append(
                    finding(
                        "extension-unbundled-python",
                        name,
                        "Python launcher relies on an interpreter outside this archive. AWS recommends packaging a compatible runtime for interpreted external extensions.",
                        SOURCE,
                        "review",
                    )
                )
            else:
                findings.append(
                    finding(
                        "extension-launcher-review",
                        name,
                        "Shell or other launcher requires manual review of its Python invocation and bundled runtime; it was not executed.",
                        SOURCE,
                        "review",
                    )
                )
        return report(
            "extensions",
            findings,
            entrypoints=len(entries),
            runtime=runtime,
            architecture=architecture,
            limitations="External extension ZIP entrypoints only. Internal extensions, wrapper script evaluation, container images, vendor support and dynamic Python selection are not resolved. Review findings are not compatibility failures.",
        )
    finally:
        archive.close()


def run(args) -> int:
    return emit(scan(Path(args.archive), args.runtime, args.architecture), args)
