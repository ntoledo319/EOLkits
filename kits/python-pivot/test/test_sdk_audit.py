"""Synthetic botocore models exercise differences without inventing AWS removals."""

from __future__ import annotations

import gzip
import json

import pytest
from python_pivot.cli import main
from python_pivot.sdk_audit import Models, scan


def model(root, version="2020-01-01", members=None, operations=None, compressed=False):
    folder = root / "fixture-service" / version
    folder.mkdir(parents=True, exist_ok=True)
    data = {
        "version": "2.0",
        "metadata": {"apiVersion": version},
        "operations": operations or {"RunJob": {"input": {"shape": "Request"}}},
        "shapes": {
            "Request": {"type": "structure", "members": members or {"Name": {"shape": "String"}}},
            "String": {"type": "string"},
        },
    }
    raw = json.dumps(data).encode()
    path = folder / ("service-2.json.gz" if compressed else "service-2.json")
    path.write_bytes(gzip.compress(raw) if compressed else raw)
    return path


def source(tmp_path, content):
    path = tmp_path / "app.py"
    path.write_text(content)
    return path


def codes(result):
    return {item["code"] for item in result["findings"]}


def test_supported_alias_session_and_literal_calls(tmp_path):
    models = tmp_path / "models"
    model(models, compressed=True)
    path = source(
        tmp_path,
        "import boto3 as aws\nsession = aws.Session()\nclient = session.client('fixture-service')\nclient.run_job(Name='safe')\n",
    )
    result = scan(path, Models(models))
    assert result["findings"] == []
    assert result["coverage"]["calls"] == 1
    assert result["coverage"]["clients"] == 1


def test_removed_parameter_and_operation_require_baseline(tmp_path):
    target, previous = tmp_path / "target", tmp_path / "previous"
    model(target)
    model(
        previous,
        members={"Name": {"shape": "String"}, "Old": {"shape": "String"}},
        operations={"RunJob": {"input": {"shape": "Request"}}, "OldJob": {}},
    )
    path = source(
        tmp_path,
        "from boto3 import client\napi = client('fixture-service')\napi.run_job(Name='safe', Old='legacy')\napi.old_job()\n",
    )
    result = scan(path, Models(target), Models(previous))
    assert codes(result) == {"parameter-removed", "operation-removed"}
    assert {item["subject"] for item in result["findings"]} == {"app.py:3", "app.py:4"}
    assert codes(scan(path, Models(target))) == {"parameter-unavailable", "operation-unmodeled"}


def test_missing_version_is_not_called_removed_without_old_model(tmp_path):
    target, previous = tmp_path / "target", tmp_path / "previous"
    model(target, version="2022-01-01")
    model(previous)
    path = source(
        tmp_path,
        "import boto3\napi = boto3.client('fixture-service', api_version='2020-01-01')\napi.run_job(Name='test')\n",
    )
    assert codes(scan(path, Models(target))) == {"api-version-unavailable"}
    assert codes(scan(path, Models(target), Models(previous))) == {"api-version-removed"}


def test_explicit_model_deprecations_and_dynamic_kwargs(tmp_path):
    target = tmp_path / "target"
    model(
        target,
        members={"Legacy": {"shape": "String", "deprecated": True}},
        operations={"RunJob": {"input": {"shape": "Request"}, "deprecated": True}},
    )
    path = source(
        tmp_path,
        "import boto3\nboto3.client('fixture-service').run_job(Legacy='x', **params)\nboto3.client(service_name=SERVICE)\n",
    )
    assert codes(scan(path, Models(target))) == {
        "operation-deprecated",
        "parameter-deprecated",
        "dynamic-sdk-parameters",
        "dynamic-sdk-client",
    }


def test_independent_scopes_and_reassigned_client_do_not_generate_false_removal(tmp_path):
    target = tmp_path / "target"
    model(target)
    path = source(
        tmp_path,
        "import boto3\napi = boto3.client('fixture-service')\ndef handler(api):\n    api.not_a_boto_call()\napi.run_job(Name='good')\napi = object()\napi.not_a_boto_call()\n# boto3.client('removed').not_a_real_call()\n",
    )
    result = scan(path, Models(target))
    assert result["findings"] == []
    assert result["coverage"]["calls"] == 1


def test_invalid_source_or_model_is_error_not_clean_report(tmp_path, capsys):
    target = tmp_path / "target"
    data = model(target)
    path = source(tmp_path, "import boto3\napi = boto3.client('fixture-service')\n")
    data.write_text("{}")
    assert main(["boto3", str(path), "--models", str(target), "--format", "json"]) == 2
    assert capsys.readouterr().out == ""
    model(target)
    path.write_text("def invalid(:\n")
    assert main(["boto3", str(path), "--models", str(target), "--format", "json"]) == 2
    assert capsys.readouterr().out == ""


def test_cli_strict_and_model_path_boundaries(tmp_path, capsys):
    target = tmp_path / "target"
    model(target)
    path = source(
        tmp_path, "import boto3\napi=boto3.client('fixture-service')\napi.run_job(Unknown='x')\n"
    )
    assert main(["boto3", str(path), "--models", str(target), "--format", "json", "--strict"]) == 1
    assert json.loads(capsys.readouterr().out)["findings"][0]["code"] == "parameter-unavailable"
    with pytest.raises(ValueError, match="service name"):
        Models(target).load("../escape", None)
    with pytest.raises(ValueError, match="api_version"):
        Models(target).load("fixture-service", "../escape")
    linked = tmp_path / "linked"
    linked.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        Models(linked)


def test_resource_calls_and_class_scopes_have_explicit_coverage(tmp_path):
    target = tmp_path / "target"
    model(target)
    path = source(
        tmp_path,
        "import boto3\napi = boto3.client('fixture-service')\nclass Example:\n    api = object()\n    api.not_a_boto_call()\napi.run_job(Name='good')\nboto3.resource('fixture-service')\n",
    )
    result = scan(path, Models(target))
    assert codes(result) == {"sdk-resource-unresolved"}
    assert result["coverage"]["calls"] == 1


@pytest.mark.parametrize(
    "block",
    [
        "for api in unrelated:\n    api.not_a_boto_call()\n",
        "with unrelated() as api:\n    api.not_a_boto_call()\n",
        "try:\n    api.not_a_boto_call()\nexcept Exception as api:\n    api.not_a_boto_call()\n",
        "while condition:\n    api.not_a_boto_call()\n    api = unrelated()\n",
        "if condition:\n    api = unrelated()\n",
    ],
)
def test_control_flow_shadowing_is_manual_review_not_an_aws_operation(tmp_path, block):
    target = tmp_path / "target"
    model(target)
    path = source(
        tmp_path,
        "import boto3\napi = boto3.client('fixture-service')\n" + block + "api.not_a_boto_call()\n",
    )
    result = scan(path, Models(target))
    assert codes(result) == {"sdk-binding-control-flow"}
    assert result["coverage"]["calls"] == 0
    assert result["findings"][0]["severity"] == "review"


@pytest.mark.parametrize("binding", ["import unrelated as api", "from unrelated import api"])
def test_function_import_alias_shadows_module_client_before_import(tmp_path, binding):
    target = tmp_path / "target"
    model(target)
    path = source(
        tmp_path,
        "import boto3\napi = boto3.client('fixture-service')\n"
        "def handler():\n    api.not_a_boto_call()\n    " + binding + "\n"
        "api.run_job(Name='good')\n",
    )
    result = scan(path, Models(target))
    assert result["findings"] == []
    assert result["coverage"]["calls"] == 1


def test_unshadowed_sdk_calls_inside_branches_remain_checked(tmp_path):
    target = tmp_path / "target"
    model(target)
    path = source(
        tmp_path,
        "import boto3\napi = boto3.client('fixture-service')\n"
        "for name in names:\n    api.run_job(Unknown=name)\n"
        "try:\n    api.run_job(Name='good')\nexcept Exception:\n    pass\n",
    )
    result = scan(path, Models(target))
    assert codes(result) == {"parameter-unavailable"}
    assert result["coverage"]["calls"] == 2


def test_comprehension_and_lambda_targets_do_not_leak_or_imply_aws_calls(tmp_path):
    target = tmp_path / "target"
    model(target)
    path = source(
        tmp_path,
        "import boto3\napi = boto3.client('fixture-service')\n"
        "items = [api.not_a_boto_call() for api in unrelated]\n"
        "callback = lambda api: api.not_a_boto_call()\n"
        "api.run_job(Name='good')\n"
        "(api := object()).not_a_boto_call()\napi.not_a_boto_call()\n",
    )
    result = scan(path, Models(target))
    assert codes(result) == {"sdk-binding-control-flow"}
    assert result["coverage"]["calls"] == 1


def test_positional_api_version_and_imported_resource_are_not_silently_skipped(tmp_path):
    target, baseline = tmp_path / "target", tmp_path / "baseline"
    model(target, version="2022-01-01")
    model(baseline)
    path = source(
        tmp_path,
        "from boto3 import client, resource as aws_resource\n"
        "api = client('fixture-service', 'example-region', '2020-01-01')\n"
        "aws_resource('fixture-service')\n",
    )
    result = scan(path, Models(target), Models(baseline))
    assert codes(result) == {"api-version-removed", "sdk-resource-unresolved"}
