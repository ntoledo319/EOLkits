const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {
  scanJavaScriptText,
  scanPythonText,
  scanStructuredText,
  scanTerraformText
} = require('../out/rules.js');
const { resolveSetting } = require('../out/settings.js');

const json = scanStructuredText('{"Resources":{"Fn":{"Runtime":"nodejs20.x"}}}');
assert.equal(json.length, 1);
assert.equal(json[0].code, 'LAMBDA_NODE20_EOL');
assert.equal(scanStructuredText('{"Runtime":"nodejs22.x"}')[0].severity, 'medium');
assert.equal(scanStructuredText('{"Runtime":"nodejs16.x"}')[0].code, 'LAMBDA_NODE16_EOL');
assert.equal(scanStructuredText('{"Runtime":"python3.8"}')[0].code, 'LAMBDA_PYTHON38_EOL');
assert.match(scanStructuredText('{"Runtime":"python3.10"}')[0].message, /projected/);
assert.equal(scanStructuredText('{"runtime":"nodejs20.x"}').length, 0);

const yaml = scanStructuredText('Runtime: python3.10\nImageId: amazonlinux2-ami\n');
assert.deepEqual(yaml.map(finding => finding.code), [
  'LAMBDA_PYTHON310_EOL',
  'AMAZON_LINUX2_EOL'
]);

assert.equal(scanJavaScriptText("import AWS from 'aws-sdk';")[0].code, 'AWS_SDK_V2_DEPRECATED');
assert.equal(scanPythonText('from collections import Mapping')[0].severity, 'low');
assert.equal(scanTerraformText('ami_name = "al2-ami-hvm"')[0].code, 'TF_AL2_AMI_DEPRECATED');
const terraform = scanTerraformText(`
resource "aws_lambda_function" "api" {
  runtime = "nodejs16.x"
  # runtime = "python3.8"
  environment { variables = { runtime = "python3.8", EXAMPLE = "}" } }
  description = <<-TEXT
    resource "aws_lambda_function" "fake" {
      runtime = "python3.9"
    }
  TEXT
}
resource "aws_sfn_state_machine" "workflow" {
  runtime = "python3.8"
}
variable "runtime" { default = "nodejs20.x" }
// resource "aws_lambda_function" "commented" { runtime = "python3.11" }
`);
assert.deepEqual(terraform.map(finding => finding.code), ['LAMBDA_NODE16_EOL']);
assert.ok(terraform[0].index > 0);
assert.equal(scanStructuredText('{"Runtime":"nodejs24.x"}').length, 0);

const extensionRoot = path.resolve(__dirname, '..');
const manifest = JSON.parse(fs.readFileSync(path.join(extensionRoot, 'package.json'), 'utf8'));
const compiledExtension = fs.readFileSync(path.join(extensionRoot, 'out', 'extension.js'), 'utf8');
const verifiedSite = 'https://ntoledo319.github.io/EOLkits/';
assert.equal(`${manifest.publisher}.${manifest.name}`, 'rupture.rupture-vscode');
assert.equal(manifest.version, '1.3.0');
assert.equal(manifest.displayName, 'AWS Lambda EOL Scanner — EOLkits');
assert.match(manifest.description, /Terraform, SAM\/CloudFormation/);
assert.ok(manifest.keywords.includes('nodejs20'));
assert.ok(manifest.keywords.includes('aws sdk v2'));
assert.ok(manifest.activationEvents.includes('onCommand:rupture.scanWorkspace'));
assert.equal(manifest.homepage, verifiedSite);
assert.ok(manifest.sponsor.url.startsWith(`${verifiedSite}audit/`));
assert.match(compiledExtension, /https:\/\/ntoledo319\.github\.io\/EOLkits\/audit\//);
assert.doesNotMatch(compiledExtension, /https:\/\/eolkits\.com\/audit/);
assert.match(compiledExtension, /rupture\.scanWorkspace/);
assert.match(compiledExtension, /See \$299 Report/);
assert.match(compiledExtension, /issues\/new\?template=audit-interest\.yml/);

const config = (values = {}) => ({
  inspect: (section) => values[section] === undefined ? undefined : { workspaceValue: values[section] },
  get: (section, defaultValue) => values[section] === undefined ? defaultValue : values[section]
});
assert.equal(resolveSetting(config(), config({ autoScan: false }), 'autoScan', true), false);
assert.equal(resolveSetting(config({ autoScan: true }), config({ autoScan: false }), 'autoScan', true), true);
assert.deepEqual(
  resolveSetting(config(), config({ enabledKits: ['python-pivot'] }), 'enabledKits', []),
  ['python-pivot']
);

console.log('scanner rule behavior passed');
