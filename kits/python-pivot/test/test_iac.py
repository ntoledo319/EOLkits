"""Test IaC patcher."""

from argparse import Namespace
from pathlib import Path

import pytest
from python_pivot import iac

FIX = Path(__file__).parent / "fixtures"


def _args(path, apply=False, strict=False):
    return Namespace(path=str(path), apply=apply, strict=strict)


def test_sam_template_patched(tmp_path):
    f = tmp_path / "template.yaml"
    f.write_text((FIX / "template.yaml").read_text())
    rc = iac.run(_args(f, apply=True))
    assert rc == 0
    patched = f.read_text()
    assert "Runtime: python3.12" in patched
    # already-migrated one should still be there
    assert patched.count("python3.12") >= 3  # globals + 2 functions + existing one


def test_terraform_patched(tmp_path):
    f = tmp_path / "main.tf"
    f.write_text((FIX / "main.tf").read_text())
    rc = iac.run(_args(f, apply=True))
    assert rc == 0
    patched = f.read_text()
    assert 'runtime       = "python3.12"' in patched
    # Existing 3.12 unchanged
    assert "already-migrated" in patched


def test_cdk_ts_patched(tmp_path):
    f = tmp_path / "stack.ts"
    f.write_text((FIX / "stack.ts").read_text())
    rc = iac.run(_args(f, apply=True))
    assert rc == 0
    patched = f.read_text()
    assert "Runtime.PYTHON_3_12" in patched
    assert "Runtime.PYTHON_3_9" not in patched
    assert "Runtime.PYTHON_3_10" not in patched


def test_dry_run_no_write(tmp_path):
    f = tmp_path / "template.yaml"
    f.write_text((FIX / "template.yaml").read_text())
    original = f.read_text()
    rc = iac.run(_args(f, apply=False))
    assert rc == 0
    assert f.read_text() == original


def test_strict_dry_run_exits_1_when_edits_needed(tmp_path):
    f = tmp_path / "template.yaml"
    f.write_text((FIX / "template.yaml").read_text())
    rc = iac.run(_args(f, apply=False, strict=True))
    assert rc == 1


def test_idempotent(tmp_path):
    f = tmp_path / "template.yaml"
    f.write_text((FIX / "template.yaml").read_text())
    iac.run(_args(f, apply=True))
    first = f.read_text()
    iac.run(_args(f, apply=True))
    second = f.read_text()
    assert first == second


def test_unrelated_runtime_is_never_rewritten(tmp_path):
    f = tmp_path / "settings.yaml"
    original = "Settings:\n  Runtime: python3.9\n"
    f.write_text(original)
    assert iac.run(_args(f, apply=True)) == 0
    assert f.read_text() == original


def test_json_scopes_rewrite_to_lambda_and_preserves_exact_surroundings(tmp_path):
    f = tmp_path / "template.json"
    original = '{"Settings":{"Runtime":"python3.9"}, "Resources":{"Fn":{"Properties":{"Runtime": "python3.9", "Environment":{"Variables":{"Runtime":"python3.9"}}}, "Type":"AWS::Lambda::\\u0046unction"}, "Other":{"Type":"Custom::Worker","Properties":{"Runtime":"python3.9"}}}}\n'
    f.write_text(original)
    assert iac.run(_args(f, strict=True)) == 1
    assert f.read_text() == original
    assert iac.run(_args(f, apply=True)) == 0
    assert f.read_text() == original.replace('"Runtime": "python3.9"', '"Runtime": "python3.12"')
    assert iac.run(_args(f, strict=True)) == 0


def test_yaml_quotes_comments_tags_block_strings_and_unrelated_maps_survive(tmp_path):
    f = tmp_path / "template.yaml"
    original = """Description: A developer's template
Settings:
  Runtime: python3.9
Resources:
  Fn:
    Properties:
      Runtime: 'python3.9' # keep comment
      Role: !GetAtt Role.Arn
      Layers:
        - !Ref SharedLayer
      Tags:
        - Key: Runtime
          Value: python3.9
      Description: |
        Runtime: python3.9
      Environment:
        Variables:
          Runtime: python3.9
    Type: AWS::Lambda::Function
  Other:
    Type: Custom::Worker
    Properties:
      Runtime: python3.9
""".replace(
        "\n", "\r\n"
    )
    f.write_bytes(original.encode())
    assert iac.run(_args(f, apply=True)) == 0
    assert (
        f.read_bytes() == original.replace("Runtime: 'python3.9'", "Runtime: 'python3.12'").encode()
    )


def test_inline_sam_and_globals_are_scoped(tmp_path):
    f = tmp_path / "template.yaml"
    original = 'Transform: AWS::Serverless-2016-10-31\nGlobals: { Function: { Runtime: python3.9 }, Api: { Runtime: python3.9 } }\nResources:\n  Fn: { Type: AWS::Serverless::Function, Properties: { Runtime: "python3.10" } }\n'
    f.write_text(original)
    assert iac.run(_args(f, apply=True)) == 0
    assert f.read_text() == original.replace(
        "Function: { Runtime: python3.9 }", "Function: { Runtime: python3.12 }"
    ).replace('"python3.10"', '"python3.12"')


def test_transform_sequence_identifies_sam_globals(tmp_path):
    f = tmp_path / "template.yaml"
    original = "Transform:\n  - 'AWS::Serverless-2016-10-31'\nGlobals:\n  Function:\n    Runtime: python3.9\n"
    f.write_text(original)
    assert iac.run(_args(f, apply=True)) == 0
    assert f.read_text() == original.replace("Runtime: python3.9", "Runtime: python3.12")


def test_serverless_only_edits_aws_provider_and_function_runtimes(tmp_path):
    f = tmp_path / "serverless.yml"
    original = 'service: fixture\nprovider:\n  name: aws\n  runtime: python3.9\n  environment:\n    runtime: python3.9\nfunctions:\n  worker:\n    runtime: "python3.10"\ncustom:\n  runtime: python3.9\n'
    f.write_text(original)
    assert iac.run(_args(f, apply=True)) == 0
    assert f.read_text() == original.replace(
        "  runtime: python3.9", "  runtime: python3.12", 1
    ).replace('"python3.10"', '"python3.12"')
    azure = original.replace("name: aws", "name: azure")
    f.write_text(azure)
    assert iac.run(_args(f, apply=True)) == 0
    assert f.read_text() == azure


def test_terraform_json_only_edits_lambda_runtime(tmp_path):
    f = tmp_path / "main.tf.json"
    original = '{"resource":{"aws_lambda_function":{"fn":{"runtime":"python3.9"}},"other":{"fn":{"runtime":"python3.9"}}},"locals":{"runtime":"python3.9"}}'
    f.write_text(original)
    assert iac.run(_args(f, apply=True)) == 0
    assert f.read_text() == original.replace('"python3.9"', '"python3.12"', 1)


@pytest.mark.parametrize(
    "name,content",
    [
        (
            "bad.json",
            '{"Resources":{"Fn":{"Type":"AWS::Lambda::Function","Properties":{"Runtime":"python3.9"}}}',
        ),
        (
            "bad.json",
            '{"Resources":{"Fn":{"Type":"AWS::Lambda::Function","Properties":{"Runtime":"python3.9","Runtime":"python3.10"}}}}',
        ),
        (
            "bad.yaml",
            "Resources:\n  Fn:\n    Type: AWS::Lambda::Function\n    Properties:\n      Runtime: !Ref SelectedRuntime\n",
        ),
        (
            "bad.yaml",
            "Resources:\n  Fn: { Type: AWS::Lambda::Function,\n    Properties: { Runtime: python3.9 } }\n",
        ),
    ],
)
def test_bad_template_stops_the_entire_batch_before_any_write(tmp_path, capsys, name, content):
    good = tmp_path / "a-template.yaml"
    original = "Resources:\n  Fn:\n    Type: AWS::Lambda::Function\n    Properties:\n      Runtime: python3.9\n"
    good.write_text(original)
    bad = tmp_path / name
    bad.write_text(content)
    assert iac.run(_args(tmp_path, apply=True)) == 2
    assert good.read_text() == original
    assert bad.read_text() == content
    assert "no changes written" in capsys.readouterr().err


def test_terraform_hcl_scopes_runtime_and_skips_comments_and_heredocs(tmp_path):
    f = tmp_path / "main.tf"
    original = """locals {
  runtime = "python3.9"
  example = <<EOF
resource "aws_lambda_function" "fake" { runtime = "python3.9" }
EOF
}
# resource "aws_lambda_function" "fake" { runtime = "python3.9" }
resource "other" "x" { runtime = "python3.9" }
resource "aws_lambda_function" "real" {
  runtime = "python3.9" # keep
  tags = { runtime = "python3.9" }
}
"""
    f.write_text(original)
    assert iac.run(_args(f, apply=True)) == 0
    assert f.read_text() == original.replace(
        'runtime = "python3.9" # keep', 'runtime = "python3.12" # keep'
    )
