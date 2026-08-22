const assert = require('node:assert/strict');
const {
  scanJavaScriptText,
  scanPythonText,
  scanStructuredText,
  scanTerraformText
} = require('../out/rules.js');

const json = scanStructuredText('{"Resources":{"Fn":{"Runtime":"nodejs20.x"}}}');
assert.equal(json.length, 1);
assert.equal(json[0].code, 'LAMBDA_NODE20_EOL');
assert.equal(scanStructuredText('{"Runtime":"nodejs22.x"}')[0].severity, 'medium');

const yaml = scanStructuredText('Runtime: python3.10\nImageId: amazonlinux2-ami\n');
assert.deepEqual(yaml.map(finding => finding.code), [
  'LAMBDA_PYTHON310_EOL',
  'AMAZON_LINUX2_EOL'
]);

assert.equal(scanJavaScriptText("import AWS from 'aws-sdk';")[0].code, 'AWS_SDK_V2_DEPRECATED');
assert.equal(scanPythonText('from collections import Mapping')[0].severity, 'low');
assert.equal(scanTerraformText('ami_name = "al2-ami-hvm"')[0].code, 'TF_AL2_AMI_DEPRECATED');
assert.equal(scanStructuredText('{"Runtime":"nodejs24.x"}').length, 0);

console.log('scanner rule behavior passed');
