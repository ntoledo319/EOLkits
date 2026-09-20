"""Behavioral coverage for the five roadmap commands; no live AWS or PR calls."""

import json
import os
import subprocess
import sys

import pytest
from al2023_gate import agent_shim, ci_template, config_export, eks_proposal, state
from al2023_gate.artifacts import json_text, read_json, write_bundle
from al2023_gate.cli import main


def node_group():
    return {
        "resource": {
            "aws_eks_node_group": {
                "workers": {
                    "cluster_name": "example",
                    "node_role_arn": "${aws_iam_role.nodes.arn}",
                    "subnet_ids": ["${aws_subnet.private.id}"],
                    "node_group_name": "workers",
                    "ami_type": "AL2_x86_64",
                    "scaling_config": [{"desired_size": 2, "min_size": 1, "max_size": 3}],
                    "tags": {"owner": "example-team"},
                }
            }
        },
        "output": {"unchanged": {"value": "preserved"}},
    }


def test_raw_state_addresses_and_no_secret_output():
    document = {
        "version": 4,
        "resources": [
            {
                "module": "module.compute",
                "mode": "managed",
                "type": "aws_instance",
                "name": "app",
                "instances": [
                    {
                        "index_key": "blue",
                        "attributes": {"ami": "ami-12345678", "user_data": "PRIVATE_PAYLOAD"},
                    }
                ],
            }
        ],
        "outputs": {"key": {"value": "PRIVATE_SECRET"}},
    }
    result = state.scan_state(document)
    assert result["findings"] == [
        {
            "address": 'module.compute.aws_instance.app["blue"]',
            "attribute": "/ami",
            "value": "ami-12345678",
            "region": "",
            "platform": "unknown",
            "evidence": "unresolved-ami-id",
        }
    ]
    assert "PRIVATE" not in json_text(result)


def test_only_provider_attributes_are_ami_evidence():
    document = {
        "version": 4,
        "resources": [
            {
                "type": "aws_instance",
                "name": "example",
                "instances": [
                    {
                        "attributes": {
                            "ami": "ami-12345678",
                            "tags": {"ami": "ami-87654321", "ami_type": "PRIVATE_SECRET"},
                            "user_data": {"image_id": "ami-87654321"},
                        }
                    }
                ],
            }
        ],
    }
    result = state.scan_state(document)
    assert len(result["findings"]) == 1
    assert "ami-87654321" not in json_text(result) and "PRIVATE" not in json_text(result)


def test_missing_provider_image_is_unresolved_without_echoing_tags(tmp_path, capsys):
    source = tmp_path / "state.json"
    source.write_text(
        json_text(
            {
                "version": 4,
                "resources": [
                    {
                        "type": "aws_instance",
                        "name": "example",
                        "instances": [{"attributes": {"tags": {"ami": "ami-87654321"}}}],
                    }
                ],
            }
        )
    )
    assert main(["terraform-state", str(source), "--strict"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["findings"] == [] and len(report["unresolved_resources"]) == 1
    assert "ami-87654321" not in json_text(report)


def test_unscoped_state_ami_metadata_does_not_resolve_other_unknown_regions():
    document = {
        "format_version": "1.0",
        "values": {
            "root_module": {
                "resources": [
                    {
                        "address": "data.aws_ami.base",
                        "mode": "data",
                        "type": "aws_ami",
                        "values": {"id": "ami-12345678", "name": "Amazon Linux 2"},
                    },
                    {
                        "address": "aws_instance.app",
                        "type": "aws_instance",
                        "values": {"ami": "ami-12345678"},
                    },
                ]
            }
        },
    }
    assert state.scan_state(document)["findings"][0]["platform"] == "unknown"
    assert state.scan_state(document, region="us-east-1")["findings"][0]["platform"] == "al2"


@pytest.mark.parametrize(
    "document",
    [
        {"format_version": "1.0", "values": []},
        {"format_version": "1.0", "values": {"root_module": {"resources": ["bad"]}}},
        {
            "format_version": "1.0",
            "values": {
                "root_module": {
                    "resources": [
                        {"address": "aws_instance.x", "type": "aws_instance", "values": "bad"}
                    ]
                }
            },
        },
        {"version": 4, "resources": ["bad"]},
        {
            "version": 4,
            "resources": [{"type": "aws_instance", "name": "x", "instances": [{"attributes": []}]}],
        },
    ],
)
def test_malformed_state_schema_has_actionable_cli_errors(tmp_path, capsys, document):
    source = tmp_path / "bad.json"
    source.write_text(json_text(document))
    assert main(["terraform-state", str(source)]) == 2
    message = capsys.readouterr().err
    assert "must" in message or "require" in message
    assert "AttributeError" not in message and "Traceback" not in message


def test_module_depth_bound():
    root = {}
    for _ in range(66):
        root = {"child_modules": [root]}
    with pytest.raises(ValueError, match="64-level"):
        state.scan_state({"format_version": "1.0", "values": {"root_module": root}})


def test_show_state_children_local_ami_metadata_and_regional_catalog():
    document = {
        "format_version": "1.0",
        "values": {
            "root_module": {
                "child_modules": [
                    {
                        "resources": [
                            {
                                "address": "module.child.data.aws_ami.base",
                                "mode": "data",
                                "type": "aws_ami",
                                "values": {"id": "ami-12345678", "name": "amzn2-ami"},
                            },
                            {
                                "address": "module.child.aws_launch_template.app",
                                "type": "aws_launch_template",
                                "values": {"image_id": "ami-12345678"},
                            },
                            {
                                "address": "module.child.aws_eks_node_group.arm",
                                "type": "aws_eks_node_group",
                                "values": {"ami_type": "AL2023_ARM_64_STANDARD"},
                            },
                        ]
                    }
                ]
            }
        },
    }
    findings = state.scan_state(document, region="eu-west-1")["findings"]
    assert [item["platform"] for item in findings] == ["al2023", "al2"]
    catalog = state.catalog_entries(
        [{"region": "us-east-1", "ami_id": "ami-12345678", "description": "Amazon Linux 2"}]
    )
    assert state.ami_platform("ami-12345678", "eu-west-1", catalog)[0] == "unknown"


@pytest.mark.parametrize(
    "document",
    [{}, [], {"format_version": "1.0", "planned_values": {}}, {"version": 3, "resources": []}],
)
def test_state_rejects_unsupported_or_plan_formats(document):
    with pytest.raises(ValueError):
        state.scan_state(document)


def test_duplicate_json_keys_are_refused(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"resource": {}, "resource": {}}')
    with pytest.raises(ValueError, match="Duplicate"):
        read_json(path)


class ConfigClient:
    def __init__(self):
        self.calls = []

    def select_aggregate_resource_config(self, **kwargs):
        self.calls.append(("inventory", kwargs))
        account = "222222222222" if kwargs.get("NextToken") else "111111111111"
        result = {
            "Results": [
                json.dumps(
                    {
                        "resourceId": "i-example",
                        "resourceType": "AWS::EC2::Instance",
                        "accountId": account,
                        "awsRegion": "us-east-1",
                        "configuration": {"imageId": "ami-12345678"},
                    }
                )
            ]
        }
        if not kwargs.get("NextToken"):
            result["NextToken"] = "inventory-second"
        return result

    def describe_aggregate_compliance_by_config_rules(self, **kwargs):
        self.calls.append(("summaries", kwargs))
        second = bool(kwargs.get("NextToken"))
        return {
            "AggregateComplianceByConfigRules": [
                {
                    "ConfigRuleName": "approved-amis",
                    "AccountId": "222222222222" if second else "111111111111",
                    "AwsRegion": "eu-west-1" if second else "us-east-1",
                }
            ],
            **({} if second else {"NextToken": "summary-second"}),
        }

    def get_aggregate_compliance_details_by_config_rule(self, **kwargs):
        self.calls.append(("details", kwargs))
        second = bool(kwargs.get("NextToken"))
        return {
            "AggregateEvaluationResults": [
                {
                    "EvaluationResultIdentifier": {
                        "EvaluationResultQualifier": {
                            "ResourceId": "i-two" if second else "i-one",
                            "ResourceType": "AWS::EC2::Instance",
                        }
                    },
                    "ComplianceType": "NON_COMPLIANT",
                    "Annotation": "DO_NOT_EXPORT_ANNOTATION",
                }
            ],
            **({} if second else {"NextToken": "details-second"}),
        }


def test_config_all_pagination_layers_and_account_region_scope():
    client = ConfigClient()
    export = config_export.collect(client, "existing-org", "approved-amis")
    assert len(export["resources"]) == 2
    assert len(export["evaluations"]) == 4
    details = [args for kind, args in client.calls if kind == "details"]
    assert {(args["AccountId"], args["AwsRegion"]) for args in details} == {
        ("111111111111", "us-east-1"),
        ("222222222222", "eu-west-1"),
    }
    assert all(
        args["ComplianceType"] == "NON_COMPLIANT" and args["Limit"] == 100 for args in details
    )
    assert "DO_NOT_EXPORT" not in json_text(export)
    report = config_export.report_export(export)
    assert all(item["platform"] == "unknown" for item in report["findings"])
    assert config_export.report_export(export) == report


def test_config_repeated_token_and_access_failure_are_not_success():
    class Broken:
        def query(self, **kwargs):
            return {"Results": [], "NextToken": "same"}

    with pytest.raises(ValueError, match="repeated"):
        list(config_export.pages(Broken(), "query", "Results"))

    class Denied:
        def select_aggregate_resource_config(self, **kwargs):
            raise RuntimeError("Access denied")

    with pytest.raises(RuntimeError, match="Access denied"):
        config_export.collect(Denied(), "existing-org")


@pytest.mark.parametrize(
    "document",
    [
        {"resources": ["bad"]},
        {"resources": [], "evaluations": ["bad"]},
        {
            "resources": [
                {
                    "resourceId": "i-one",
                    "resourceType": "AWS::EC2::Instance",
                    "accountId": "111111111111",
                    "awsRegion": "us-east-1",
                    "configuration": [],
                }
            ]
        },
    ],
)
def test_malformed_config_schema_has_actionable_errors(document):
    with pytest.raises(ValueError):
        config_export.report_export(document)


@pytest.mark.parametrize("trailing_newline", [True, False])
def test_eks_patch_is_real_applicable_and_preserves_old_group(tmp_path, trailing_newline):
    document = node_group()
    original = json.dumps(document, indent=2) + ("\n" if trailing_newline else "")
    report, files = eks_proposal.propose(document, "workers", "nodes.tf.json", original)
    assert report["strategy"] == "parallel-node-group"
    proposed = json.loads(files["proposed.tf.json"])
    assert (
        proposed["resource"]["aws_eks_node_group"]["workers"]
        == document["resource"]["aws_eks_node_group"]["workers"]
    )
    assert (
        proposed["resource"]["aws_eks_node_group"]["workers_al2023"]["ami_type"]
        == "AL2023_x86_64_STANDARD"
    )
    assert proposed["output"] == document["output"]
    (tmp_path / "nodes.tf.json").write_text(original)
    (tmp_path / "migration.patch").write_text(files["migration.patch"])
    result = subprocess.run(
        ["git", "apply", "--check", "migration.patch"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    subprocess.run(["git", "apply", "migration.patch"], cwd=tmp_path, check=True)
    assert json.loads((tmp_path / "nodes.tf.json").read_text()) == proposed


@pytest.mark.parametrize(
    "change",
    [
        {"launch_template": [{}]},
        {"count": 2},
        {"ami_type": "AL2_x86_64_GPU"},
        {"release_version": "old"},
        {"node_group_name": "${var.group}"},
    ],
)
def test_eks_refuses_ambiguous_or_unsupported_groups(change):
    document = node_group()
    document["resource"]["aws_eks_node_group"]["workers"].update(change)
    with pytest.raises(ValueError):
        eks_proposal.propose(document, "workers", "nodes.tf.json", json_text(document))


def test_pr_script_dry_run_and_dirty_tree_refusal_never_publish(tmp_path):
    bundle = tmp_path / "bundle"
    _, files = eks_proposal.propose(
        node_group(), "workers", "nodes.tf.json", json_text(node_group())
    )
    write_bundle(bundle, files)
    tools = tmp_path / "bin"
    tools.mkdir()
    log = tmp_path / "commands.log"
    for name in ("git", "gh"):
        command = tools / name
        command.write_text(
            '#!/bin/sh\nprintf "%s\\n" "$0 $*" >> "$COMMAND_LOG"\nif [ "$1" = status ]; then printf " M dirty\\n"; fi\n'
        )
        command.chmod(0o700)
    env = {
        **os.environ,
        "PATH": str(tools) + os.pathsep + os.environ["PATH"],
        "COMMAND_LOG": str(log),
    }
    result = subprocess.run(
        ["bash", str(bundle / "open-pr.sh")], cwd=tmp_path, env=env, capture_output=True, text=True
    )
    assert result.returncode == 0 and not log.exists()
    result = subprocess.run(
        ["bash", str(bundle / "open-pr.sh"), "--create-pr"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "status --porcelain" in log.read_text() and "gh" not in log.read_text()


def test_pr_script_explicit_opt_in_reaches_draft_publication_using_fake_tools(tmp_path):
    _, files = eks_proposal.propose(
        node_group(), "workers", "nodes.tf.json", json_text(node_group())
    )
    bundle = tmp_path / "bundle"
    write_bundle(bundle, files)
    tools = tmp_path / "bin"
    tools.mkdir()
    log = tmp_path / "commands.log"
    script = """#!/bin/sh
printf '%s\\n' "$0 $*" >> "$COMMAND_LOG"
case "$1" in
  rev-parse) pwd -P ;;
  branch) printf 'main\\n' ;;
esac
"""
    for name in ("git", "gh"):
        path = tools / name
        path.write_text(script)
        path.chmod(0o700)
    result = subprocess.run(
        ["bash", str(bundle / "open-pr.sh"), "--create-pr"],
        cwd=tmp_path,
        env={
            **os.environ,
            "PATH": str(tools) + os.pathsep + os.environ["PATH"],
            "COMMAND_LOG": str(log),
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    commands = log.read_text()
    assert "apply --check" in commands and "apply --index" in commands
    assert "push --set-upstream origin codex/eks-al2023-" in commands
    assert "pr create --draft --base main --head codex/eks-al2023-" in commands
    assert "terraform" not in commands


@pytest.mark.parametrize(
    "agent,filename,key",
    [
        ("datadog", "datadog-agent/datadog.yaml", "api_key"),
        ("newrelic", "newrelic-infra.yml", "license_key"),
    ],
)
def test_agent_bundle_preserves_values_and_script_preview_restore(tmp_path, agent, filename, key):
    exported = tmp_path / "export"
    source = exported / filename
    source.parent.mkdir(parents=True)
    original = f"# retain comment\n{key}: fixture-only\nproxy: https://example.invalid\n".encode()
    source.write_bytes(original)
    manifest, files = agent_shim.build_bundle(exported, agent)
    assert "fixture-only" not in json_text(manifest)
    assert files["config/" + filename] == original
    bundle = tmp_path / "bundle"
    write_bundle(bundle, files)
    assert bundle.stat().st_mode & 0o777 == 0o700
    assert (bundle / "config" / filename).stat().st_mode & 0o777 == 0o600
    destination = tmp_path / "new-host"
    (destination / "etc").mkdir(parents=True)
    (destination / "etc/os-release").write_text('ID="amzn"\nVERSION_ID="2023"\n')
    command = [sys.executable, str(bundle / "migrate.py"), "--target-root", str(destination)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0 and not (destination / "etc" / filename).exists()
    result = subprocess.run(command + ["--apply"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (destination / "etc" / filename).read_bytes() == original
    assert "fixture-only" not in result.stdout
    assert (source).read_bytes() == original


def test_agent_missing_key_or_symlink_refused(tmp_path):
    config = tmp_path / "datadog-agent"
    config.mkdir()
    (config / "datadog.yaml").write_text("# api_key: example\napi_key: # empty\n")
    with pytest.raises(ValueError, match="api_key"):
        agent_shim.build_bundle(tmp_path, "datadog")
    (config / "datadog.yaml").write_text("api_key: fixture-only\n")
    (config / "alias.yaml").symlink_to(config / "datadog.yaml")
    with pytest.raises(ValueError, match="Symlinks"):
        agent_shim.build_bundle(tmp_path, "datadog")


@pytest.mark.parametrize("value", ["", " # empty", ' ""', " null", " |", " {from: environment}"])
def test_agent_empty_and_complex_credentials_refused(tmp_path, value):
    (tmp_path / "newrelic-infra.yml").write_text(
        "license_key:" + value + "\nproxy: must-not-be-treated-as-key\n"
    )
    with pytest.raises(ValueError, match="license_key"):
        agent_shim.build_bundle(tmp_path, "newrelic")


def test_agent_refuses_wrong_os_and_target_symlink(tmp_path):
    export = tmp_path / "export"
    export.mkdir()
    (export / "newrelic-infra.yml").write_text("license_key: fixture-only\n")
    _, files = agent_shim.build_bundle(export, "newrelic")
    bundle = tmp_path / "bundle"
    write_bundle(bundle, files)
    destination = tmp_path / "host"
    (destination / "etc").mkdir(parents=True)
    release = destination / "etc/os-release"
    release.write_text('ID="amzn"\nVERSION_ID="2"\n')
    command = [
        sys.executable,
        str(bundle / "migrate.py"),
        "--target-root",
        str(destination),
        "--apply",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0 and "Amazon Linux 2023" in result.stderr
    release.write_text('ID="amzn"\nVERSION_ID="2023"\n')
    (destination / "etc/newrelic-infra.yml").symlink_to(export / "newrelic-infra.yml")
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0 and "symlink" in result.stderr


def test_config_cli_fixture_strict_and_output_refuses_overwrite(tmp_path, capsys):
    export = config_export.collect(ConfigClient(), "fixture", "approved-amis")
    fixture = tmp_path / "config.json"
    fixture.write_text(json_text(export))
    output = tmp_path / "report.json"
    assert main(["config-export", "--fixture", str(fixture), "--strict", "--out", str(output)]) == 1
    first = output.read_bytes()
    assert main(["config-export", "--fixture", str(fixture), "--out", str(output)]) == 2
    assert output.read_bytes() == first
    capsys.readouterr()


def test_workflow_has_real_gate_no_credentials_no_upload_or_shell_injection():
    workflow = ci_template.render("inventory/state.json", ami_catalog="inventory/images.json")
    assert (
        "terraform-state './inventory/state.json' --ami-catalog 'inventory/images.json' --strict"
        in workflow
    )
    assert "contents: read" in workflow and "persist-credentials: false" in workflow
    assert "upload-artifact" not in workflow and "aws-actions" not in workflow
    assert "--region 'us-east-1'" in ci_template.render("state.json", region="us-east-1")
    with pytest.raises(ValueError):
        ci_template.render("state.json", region="$(bad)")
    for path in ("../state.json", "/state.json", "$(touch danger)", "a'bad", "line\nbreak"):
        with pytest.raises(ValueError):
            ci_template.render(path)


def test_cli_strict_errors_dry_run_and_bundles(tmp_path, capsys, monkeypatch):
    source = tmp_path / "nodes.tf.json"
    source.write_text(json_text(node_group()))
    original = source.read_bytes()
    assert main(["eks-proposal", str(source), "--resource", "workers"]) == 0
    assert json.loads(capsys.readouterr().out)["written"] is False
    assert source.read_bytes() == original
    monkeypatch.setenv("AL2023_GATE_DRY_RUN", "1")
    bundle = tmp_path / "bundle"
    assert (
        main(
            ["eks-proposal", str(source), "--resource", "workers", "--apply", "--out", str(bundle)]
        )
        == 0
    )
    assert not bundle.exists()
    capsys.readouterr()
    state_file = tmp_path / "state.json"
    state_file.write_text(
        json_text(
            {
                "version": 4,
                "resources": [
                    {
                        "type": "aws_instance",
                        "name": "app",
                        "instances": [{"attributes": {"ami": "ami-12345678"}}],
                    }
                ],
            }
        )
    )
    assert main(["terraform-state", str(state_file), "--strict"]) == 1
    assert json.loads(capsys.readouterr().out)["findings"][0]["platform"] == "unknown"
    assert main(["config-export", "--live"]) == 2
    assert "requires" in capsys.readouterr().err
