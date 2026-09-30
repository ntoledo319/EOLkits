"""Executable browser-engine contracts: evidence locations and honest input failures."""

import json
import subprocess
from pathlib import Path

import build
import pytest

ENGINE = Path(__file__).parent / "static" / "scan-engine.js"


def scan(name, content):
    data = {
        "runtimes": {
            "nodejs20.x": {"severity": "high", "date": "2027-02-01"},
            "python3.9": {"severity": "high", "date": "2027-02-01"},
        },
        "native": build._NATIVE_PACKAGES,
        "wheels": build._PY312_WHEELS,
    }
    script = (
        "const DATA = "
        + json.dumps(data)
        + ";\n"
        + ENGINE.read_text(encoding="utf-8")
        + "\ntry { console.log(JSON.stringify({findings: scanFile(..."
        + json.dumps([name, content])
        + ")})); } catch (error) { console.log(JSON.stringify({error: error.message})); }"
    )
    result = subprocess.run(
        ["node", "-"], input=script, text=True, capture_output=True, timeout=15, check=True
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize(
    "name, content, message",
    [
        ("package.json", '{"dependencies":{"sharp":"0.32.0",}', "Invalid JSON"),
        ("package.json", "null", "Expected a JSON object"),
        ("package.json", "[]", "Expected a JSON object"),
        ("package.json", '{"dependencies":{"sharp":24}}', "version strings"),
        ("template.json", '{"Resources":', "Invalid JSON"),
        ("archive.zip", "Resources: {}", "Unsupported file type"),
        ("template.yaml", "", "File is empty"),
        ("template.yaml", "\x00Runtime: python3.9", "binary"),
        ("template.yaml", "\ufffdRuntime: python3.9", "valid UTF-8"),
        ("template.yaml", "x" * (1048576 + 1), "1 MiB"),
        ("pyproject.toml", '[tool.poetry.dependencies]\nnumpy = "1.24.0"', "Poetry"),
    ],
    ids=[
        "syntax",
        "null",
        "array",
        "version-type",
        "config-syntax",
        "archive",
        "empty",
        "binary",
        "encoding",
        "size",
        "poetry",
    ],
)
def test_invalid_or_unscanned_input_cannot_be_a_clean_scan(name, content, message):
    assert message in scan(name, content)["error"]


def test_valid_dependency_manifest_is_the_positive_control_for_parse_rejection():
    findings = scan("service/package.json", '{\n "dependencies": {\n "sharp": "0.32.0"\n }\n}')
    assert len(findings["findings"]) == 1
    assert findings["findings"][0]["severity"] == "high"
    assert findings["findings"][0]["lines"] == [3]
    assert findings["findings"][0]["source"] == "https://www.npmjs.com/package/sharp"


def test_each_dependency_section_retains_its_own_version_and_line():
    findings = scan(
        "package.json",
        '{\n "dependencies": {"sharp": "0.32.0"},\n'
        ' "devDependencies": {"sharp": "0.34.0"},\n'
        ' "optionalDependencies": {"node-sass": "9.0.0"}\n}',
    )["findings"]
    assert [(f["name"], f["severity"], f["lines"]) for f in findings] == [
        ("sharp", "high", [2]),
        ("sharp", "low", [3]),
        ("node-sass", "critical", [4]),
    ]


def test_multiline_json_locations_ignore_the_same_runtime_in_unrelated_properties():
    source = {
        "Settings": {"Runtime": "nodejs20.x"},
        "Resources": {
            "Fn": {
                "Type": "AWS::Lambda::Function",
                "Properties": {"Runtime": "nodejs20.x"},
            },
            "Other": {"Type": "Other::Thing", "Properties": {"Runtime": "python3.9"}},
        },
    }
    content = json.dumps(source, indent=2)
    result = scan("template.json", content)["findings"]
    assert [f["name"] for f in result] == ["nodejs20.x"]
    expected = [i for i, line in enumerate(content.splitlines(), 1) if '"nodejs20.x"' in line]
    assert len(expected) == 2
    assert result[0]["lines"] == [expected[1]]


def test_yaml_locations_group_real_resources_without_collecting_example_values():
    content = (
        "Settings:\n  Runtime: python3.9\nResources:\n"
        "  Fn:\n    Type: AWS::Lambda::Function\n    Properties:\n      Runtime: python3.9\n"
        "  Second:\n    Type: AWS::Lambda::Function\n    Properties:\n      Runtime: python3.9\n"
    )
    assert scan("template.yaml", content)["findings"][0]["lines"] == [7, 11]


def test_terraform_locations_exclude_comments_and_nested_variables():
    content = (
        'resource "aws_lambda_function" "fn" {\n'
        '  # runtime = "nodejs20.x"\n'
        '  environment { variables = { runtime = "nodejs20.x" } }\n'
        '  runtime = "python3.9"\n}\n'
    )
    findings = scan("main.tf", content)["findings"]
    assert [(f["name"], f["lines"]) for f in findings] == [("python3.9", [4])]


def test_pep621_single_quotes_extras_and_optional_dependencies_have_locations():
    content = (
        "[project]\nname = 'sample'\ndependencies = [\n"
        "  'numpy==1.24.0',\n  'scikit_learn[extras]==1.0.0',\n]\n"
        '[project.optional-dependencies]\nscience = ["pandas==1.0.0"]\n'
    )
    findings = scan("pyproject.toml", content)["findings"]
    assert [(f["name"], f["lines"]) for f in findings] == [
        ("numpy", [4]),
        ("scikit-learn", [5]),
        ("pandas", [8]),
    ]


def test_requirements_locations_and_package_normalization():
    findings = scan(
        "requirements-dev.txt", "# packages\n\nscikit_learn==1.0.0; python_version > '3.8'\n"
    )["findings"]
    assert findings[0]["name"] == "scikit-learn"
    assert findings[0]["lines"] == [3]


@pytest.mark.parametrize(
    "content", ["-r base.txt", "--requirement=base.txt", "-c pins.txt", "-e ./local"]
)
def test_unresolved_requirements_do_not_count_as_complete(content):
    assert "not resolved" in scan("requirements.txt", content)["error"]


def test_incomplete_or_dynamic_pep621_dependencies_are_not_silently_empty():
    assert (
        "Could not read"
        in scan("pyproject.toml", '[project]\ndependencies = ["numpy==1.24.0"')["error"]
    )
    assert (
        "Dynamic dependencies"
        in scan("pyproject.toml", '[project]\ndynamic = ["dependencies"]')["error"]
    )


def test_rule_tables_do_not_match_javascript_prototype_names():
    assert scan("package.json", '{"dependencies":{"constructor":"1.0.0","toString":"1.0.0"}}') == {
        "findings": []
    }
    assert scan("requirements.txt", "constructor==1.0.0") == {"findings": []}


def test_json_nesting_limit_is_visible_instead_of_partial_evidence():
    content = '{"outer":' * 65 + "{}" + "}" * 65
    assert "64-level" in scan("template.json", content)["error"]


def test_known_safe_configuration_and_current_dependency_do_not_invent_risks():
    assert scan("template.yaml", "Settings:\n  Runtime: python3.9\n") == {"findings": []}
    assert scan("requirements.txt", "numpy==2.0.0\n") == {"findings": []}


def test_rule_fingerprint_and_scanner_output_are_deterministic():
    rules = build.load_deprecations()
    first = build.build_scan_page(rules)
    assert first == build.build_scan_page(rules)
    assert '"version":"sha256:' in first
    assert "File names and contents stay in this browser" in first
