"""Runtime compatibility evidence is bounded, read-only and never a clean guess."""

from __future__ import annotations

import json
import stat
import sys
import types
import zipfile
from pathlib import Path

import pytest
from python_pivot import action_template, extensions, layers, powertools
from python_pivot.cli import main
from python_pivot.compat import Archive


def make_zip(tmp_path, files):
    path = tmp_path / "layer.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for name, body, mode in files:
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = mode << 16
            archive.writestr(info, body)
    return path


def elf(machine=62):
    header = bytearray(64)
    header[:6] = b"\x7fELF\x02\x01"
    header[18:20] = machine.to_bytes(2, "little")
    return bytes(header)


def codes(result):
    return {item["code"] for item in result["findings"]}


def test_layer_pure_python_and_matching_native_are_inspected_without_execution(tmp_path):
    path = make_zip(
        tmp_path,
        [
            ("python/danger.py", "raise RuntimeError('must not execute')", 0o100644),
            ("python/pkg.cpython-312-x86_64-linux-gnu.so", elf(), 0o100755),
        ],
    )
    result = layers.scan_archive(path, "python3.12", "x86_64")
    assert result["findings"] == []
    assert result["coverage"]["native_libraries"] == 1
    assert sorted(item.name for item in tmp_path.iterdir()) == ["layer.zip"]


def test_layer_mismatched_abi_architecture_and_library_directory(tmp_path):
    path = make_zip(
        tmp_path,
        [
            (
                "python/lib/python3.11/site-packages/ext.cpython-311-x86_64-linux-gnu.so",
                elf(),
                0o100755,
            )
        ],
    )
    assert codes(layers.scan_archive(path, "python3.12", "arm64")) == {
        "cpython-abi",
        "native-architecture",
        "python-library-path",
    }


def test_layer_non_linux_and_missing_python_directory(tmp_path):
    path = make_zip(tmp_path, [("lib/example.pyd", b"MZ", 0o100644)])
    assert codes(layers.scan_archive(path, "python3.12", "x86_64")) == {
        "missing-python-directory",
        "non-linux-native",
    }


@pytest.mark.parametrize(
    "name",
    [
        "../escape.py",
        "/absolute.py",
        "python\\escape.py",
        "python/./escape.py",
        "python//escape.py",
        "C:/escape.py",
    ],
)
def test_archive_rejects_ambiguous_or_traversing_paths(tmp_path, name):
    with pytest.raises(ValueError, match="unsafe|ambiguous"):
        Archive(make_zip(tmp_path, [(name, "not extracted", 0o100644)]))


def test_archive_rejects_links_duplicates_and_size_limit(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="link"):
        Archive(make_zip(tmp_path, [("python/link", "outside", stat.S_IFLNK | 0o777)]))
    with pytest.warns(UserWarning, match="Duplicate"):
        path = make_zip(tmp_path, [("python/a.py", "x", 0o100644), ("python/a.py", "y", 0o100644)])
    with pytest.raises(ValueError, match="duplicate"):
        Archive(path)
    monkeypatch.setattr("python_pivot.compat.MAX_MEMBERS", 1)
    with pytest.raises(ValueError, match="entries"):
        Archive(make_zip(tmp_path, [("python/a", "a", 0o100644), ("python/b", "b", 0o100644)]))


def test_metadata_declarations_are_not_assumed_when_missing():
    assert (
        layers.scan_metadata(
            {
                "layers": [
                    {"CompatibleRuntimes": ["python3.12"], "CompatibleArchitectures": ["arm64"]}
                ]
            },
            "python3.12",
            "arm64",
        )["findings"]
        == []
    )
    assert codes(layers.scan_metadata({"layers": [{}]}, "python3.12", "arm64")) == {
        "declared-runtime-unknown",
        "declared-architecture-unknown",
    }
    assert "declared-runtime-mismatch" in codes(
        layers.scan_metadata(
            {"layers": [{"CompatibleRuntimes": ["python3.11"]}]}, "python3.12", "arm64"
        )
    )
    with pytest.raises(ValueError, match="array"):
        layers.scan_metadata(
            {"layers": [{"CompatibleRuntimes": "python3.12"}]}, "python3.12", "arm64"
        )


def test_live_layer_lookup_is_explicit_and_read_only(monkeypatch, capsys):
    calls = []

    class Client:
        def get_function_configuration(self, **kwargs):
            calls.append(("configuration", kwargs))
            return {
                "Layers": [{"Arn": "arn:fixture:1"}],
                "Environment": {"Variables": {"private": "never-output"}},
            }

        def get_layer_version_by_arn(self, **kwargs):
            calls.append(("layer", kwargs))
            return {
                "LayerVersionArn": "arn:fixture:1",
                "CompatibleRuntimes": ["python3.12"],
                "CompatibleArchitectures": ["x86_64"],
                "Content": {"Location": "never-output"},
            }

    class Session:
        def client(self, name, region_name):
            assert name == "lambda" and region_name == "us-east-1"
            return Client()

    monkeypatch.setitem(sys.modules, "boto3", types.SimpleNamespace(Session=Session))
    assert main(["layers", "--live", "--format", "json"]) == 2
    assert calls == []
    assert (
        main(
            [
                "layers",
                "--live",
                "--function",
                "example",
                "--region",
                "us-east-1",
                "--format",
                "json",
                "--strict",
            ]
        )
        == 0
    )
    assert [item[0] for item in calls] == ["configuration", "layer"]
    assert "never-output" not in capsys.readouterr().out


def test_extension_version_and_permissions_detected(tmp_path):
    path = make_zip(
        tmp_path,
        [
            (
                "extensions/agent",
                "#!/usr/bin/env python3.9\nraise RuntimeError('must not run')\n",
                0o100644,
            )
        ],
    )
    assert codes(extensions.scan(path, "python3.12", "x86_64")) == {
        "extension-python-version",
        "extension-unbundled-python",
        "extension-not-executable",
    }


def test_extension_bundle_not_confused_with_function_python(tmp_path):
    path = make_zip(
        tmp_path,
        [
            ("extensions/agent", "#!/opt/runtime/bin/python3.9\n", 0o100755),
            ("runtime/bin/python3.9", elf(), 0o100755),
        ],
    )
    result = extensions.scan(path, "python3.12", "x86_64")
    assert codes(result) == {"bundled-interpreter-review"}
    assert all(item["severity"] == "review" for item in result["findings"])


def test_native_shell_and_empty_extension_coverage(tmp_path):
    path = make_zip(
        tmp_path,
        [
            ("extensions/native", elf(183), 0o100755),
            ("extensions/script", "#!/bin/sh\nexec $PYTHON agent.py\n", 0o100755),
        ],
    )
    assert codes(extensions.scan(path, "python3.12", "x86_64")) == {
        "native-architecture",
        "extension-native-review",
        "extension-launcher-review",
    }
    path = make_zip(tmp_path, [("python/module.py", "x=1", 0o100644)])
    assert codes(extensions.scan(path, "python3.12", "x86_64")) == {"no-extension-entrypoint"}


def test_exact_powertools_metadata_does_not_generalize_from_major_version():
    assert powertools.check("3.0.0", "python3.8", powertools.RELEASES) == []
    assert powertools.check("3.15.1", "python3.9", powertools.RELEASES) == []
    assert powertools.check("3.34.0", "python3.12", powertools.RELEASES) == []
    assert (
        powertools.check("3.34.0", "python3.9", powertools.RELEASES)[0]["code"]
        == "powertools-python-requirement"
    )
    assert (
        powertools.check("2.43.1", "python3.14", powertools.RELEASES)[0]["code"]
        == "powertools-python-unadvertised"
    )
    assert (
        powertools.check("9.99.9", "python3.12", powertools.RELEASES)[0]["code"]
        == "powertools-release-unknown"
    )


def test_powertools_cli_exact_constraints_matrix_and_metadata(tmp_path, capsys):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("aws-lambda-powertools==3.34.0\n")
    assert (
        main(
            [
                "powertools",
                str(requirements),
                "--runtime",
                "python3.9",
                "--format",
                "json",
                "--strict",
            ]
        )
        == 1
    )
    assert (
        json.loads(capsys.readouterr().out)["findings"][0]["code"]
        == "powertools-python-requirement"
    )
    requirements.write_text("aws-lambda-powertools>=3.0\n")
    assert main(["powertools", str(requirements), "--format", "json", "--strict"]) == 1
    assert (
        json.loads(capsys.readouterr().out)["findings"][0]["code"]
        == "powertools-unresolved-version"
    )
    assert main(["powertools", "--matrix", "--format", "json"]) == 0
    assert len(json.loads(capsys.readouterr().out)["coverage"]["matrix"]) == 4
    meta = tmp_path / "release.json"
    meta.write_text(
        json.dumps(
            {
                "info": {
                    "name": "aws-lambda-powertools",
                    "version": "9.99.9",
                    "requires_python": ">=3.12,<4.0",
                    "classifiers": ["Programming Language :: Python :: 3.12"],
                }
            }
        )
    )
    assert (
        main(
            [
                "powertools",
                "--package-version",
                "9.99.9",
                "--metadata",
                str(meta),
                "--format",
                "json",
                "--strict",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["findings"] == []
    meta.write_text('{"info": {"name": "other-project"}}')
    assert main(["powertools", "--matrix", "--metadata", str(meta), "--format", "json"]) == 2
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("spec", ["", ">=3.12.*", ">=3.8 or <4", ">=3.8,invalid"])
def test_powertools_rejects_unsupported_metadata_specifiers(spec):
    with pytest.raises(ValueError, match="Requires-Python"):
        powertools.permits(spec, "python3.12")


@pytest.mark.parametrize("spec", [">3.12", "<=3.12", "==3.12.0", "!=3.12", ">=3.12.1"])
def test_powertools_does_not_guess_interpreter_patch_version(spec):
    with pytest.raises(ValueError, match="patch version"):
        powertools.permits(spec, "python3.12")


def test_action_template_preview_never_writes_and_apply_is_exclusive(tmp_path, capsys):
    out = tmp_path / "python.yml"
    assert main(["--no-banner", "action", "--out", str(out)]) == 0
    assert not out.exists()
    assert capsys.readouterr().out == action_template.content()
    assert main(["--no-banner", "action", "--out", str(out), "--apply"]) == 0
    assert out.read_text() == action_template.content()
    assert main(["--no-banner", "action", "--out", str(out), "--apply"]) == 2
    assert "contents: read" in out.read_text()
    assert "persist-credentials: false" in out.read_text()
    assert "--apply" not in out.read_text()


def test_action_refuses_symlink_and_missing_parent(tmp_path):
    target = tmp_path / "real.yml"
    target.write_text("preserve")
    link = tmp_path / "link.yml"
    link.symlink_to(target)
    assert main(["action", "--out", str(link), "--apply"]) == 2
    assert target.read_text() == "preserve"
    assert main(["action", "--out", str(tmp_path / "missing" / "file.yml"), "--apply"]) == 2


def test_packaged_action_template_matches_the_documented_example():
    kit = Path(__file__).resolve().parents[1]
    assert (
        kit / "examples/github-actions/python-compatibility.yml"
    ).read_text() == action_template.content()


def test_archive_compression_bomb_and_corruption_are_rejected(tmp_path):
    path = tmp_path / "bomb.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("python/large.py", b"x" * 100000)
    with pytest.raises(ValueError, match="compression ratio"):
        Archive(path)
    path.write_bytes(b"not a zip")
    with pytest.raises(zipfile.BadZipFile):
        Archive(path)


def test_no_output_or_aws_for_invalid_target(tmp_path, capsys, monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "boto3",
        types.SimpleNamespace(Session=lambda: pytest.fail("must validate before AWS")),
    )
    assert (
        main(
            [
                "layers",
                "--live",
                "--function",
                "test",
                "--region",
                "us-east-1",
                "--runtime",
                "nodejs20.x",
                "--format",
                "json",
            ]
        )
        == 2
    )
    assert capsys.readouterr().out == ""
