import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CLI = join(__dirname, '..', 'bin', 'cli.mjs');

function run(args) {
  return spawnSync('node', [CLI, ...args], { encoding: 'utf8' });
}
function scratch() {
  const dir = mkdtempSync(join(tmpdir(), 'll-iac-'));
  return { dir, cleanup: () => rmSync(dir, { recursive: true, force: true }) };
}

test('iac dry-run finds SAM runtime references without modifying', () => {
  const { dir, cleanup } = scratch();
  try {
    const tmpl = join(dir, 'template.yaml');
    const original = `Transform: AWS::Serverless-2016-10-31
Resources:
  Fn:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: nodejs20.x
`;
    writeFileSync(tmpl, original);
    const r = run(['iac', '--path', dir]);
    assert.equal(r.status, 0, r.stderr);
    assert.match(r.stdout, /SAM\/CFN|SAM/);
    assert.match(r.stdout, /nodejs20\.x/);
    assert.equal(readFileSync(tmpl, 'utf8'), original);
  } finally { cleanup(); }
});

test('iac --apply rewrites SAM runtime', () => {
  const { dir, cleanup } = scratch();
  try {
    const tmpl = join(dir, 'template.yaml');
    writeFileSync(tmpl, `Transform: AWS::Serverless-2016-10-31
Resources:
  Fn:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: nodejs20.x
`);
    const r = run(['iac', '--path', dir, '--apply']);
    assert.equal(r.status, 0, r.stderr);
    const result = readFileSync(tmpl, 'utf8');
    assert.match(result, /Runtime: nodejs24\.x/);
    assert.doesNotMatch(result, /nodejs20\.x/);
  } finally { cleanup(); }
});

test('iac --apply rewrites legacy Node.js 14 runtime', () => {
  const { dir, cleanup } = scratch();
  try {
    const file = join(dir, 'template.yaml');
    writeFileSync(file, `Transform: AWS::Serverless-2016-10-31
Resources:
  Fn:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: nodejs14.x
      Handler: index.handler
`);
    const r = run(['iac', '--path', file, '--apply']);
    assert.equal(r.status, 0, r.stderr);
    const result = readFileSync(file, 'utf8');
    assert.match(result, /Runtime: nodejs24\.x/);
    assert.doesNotMatch(result, /nodejs14\.x/);
  } finally {
    cleanup();
  }
});

test('iac --apply rewrites Terraform runtime', () => {
  const { dir, cleanup } = scratch();
  try {
    const tf = join(dir, 'main.tf');
    writeFileSync(tf, `resource "aws_lambda_function" "a" {
  runtime = "nodejs18.x"
}
resource "aws_lambda_function" "b" {
  runtime = "nodejs20.x"
}
`);
    const r = run(['iac', '--path', dir, '--apply']);
    assert.equal(r.status, 0, r.stderr);
    const result = readFileSync(tf, 'utf8');
    assert.match(result, /runtime = "nodejs24\.x"/);
    assert.doesNotMatch(result, /nodejs20\.x/);
    assert.doesNotMatch(result, /nodejs18\.x/);
  } finally { cleanup(); }
});

test('iac --apply rewrites CDK runtime enum', () => {
  const { dir, cleanup } = scratch();
  try {
    const stack = join(dir, 'stack.ts');
    writeFileSync(stack, `import * as lambda from 'aws-cdk-lib/aws-lambda';
new lambda.Function(this, 'A', { runtime: lambda.Runtime.NODEJS_18_X });
new lambda.Function(this, 'B', { runtime: lambda.Runtime.NODEJS_20_X });
`);
    const r = run(['iac', '--path', dir, '--apply']);
    assert.equal(r.status, 0, r.stderr);
    const result = readFileSync(stack, 'utf8');
    assert.match(result, /NODEJS_24_X/);
    assert.doesNotMatch(result, /NODEJS_20_X/);
    assert.doesNotMatch(result, /NODEJS_18_X/);
  } finally { cleanup(); }
});

test('iac is idempotent', () => {
  const { dir, cleanup } = scratch();
  try {
    const tmpl = join(dir, 'template.yaml');
    writeFileSync(tmpl, `Transform: AWS::Serverless-2016-10-31
Resources:
  Fn: { Type: AWS::Serverless::Function, Properties: { Runtime: nodejs24.x } }
`);
    const r1 = run(['iac', '--path', dir, '--apply']);
    const r2 = run(['iac', '--path', dir, '--apply']);
    assert.equal(r1.status, 0);
    assert.equal(r2.status, 0);
    assert.match(r2.stdout, /No IaC runtime references needed patching/);
  } finally { cleanup(); }
});

test('iac edits CloudFormation JSON literals and preserves unrelated data byte for byte', () => {
  const { dir, cleanup } = scratch();
  try {
    const file = join(dir, 'template.json');
    const original = '{ "Settings": {"Runtime":"nodejs20.x"}, "Resources": {"Fn": {"Properties": {"Runtime": "nodejs20.x", "Environment":{"Variables":{"Runtime":"nodejs20.x"}}}, "Type":"AWS::Lambda::\\u0046unction"}, "Other":{"Type":"Custom::Worker", "Properties":{"Runtime":"nodejs20.x"}}}}\n';
    writeFileSync(file, original);
    const dry = run(['iac', '--path', file, '--strict']);
    assert.equal(dry.status, 1, dry.stderr);
    assert.equal(readFileSync(file, 'utf8'), original);
    const apply = run(['iac', '--path', file, '--apply']);
    assert.equal(apply.status, 0, apply.stderr);
    const expected = original.replace('"Runtime": "nodejs20.x"', '"Runtime": "nodejs24.x"');
    assert.equal(readFileSync(file, 'utf8'), expected);
    assert.equal(run(['iac', '--path', file, '--strict']).status, 0);
  } finally { cleanup(); }
});

test('iac YAML preserves tags, comments, quote style, block strings and unrelated Runtime keys', () => {
  const { dir, cleanup } = scratch();
  try {
    const file = join(dir, 'template.yaml');
    const original = `Description: A developer's template
Settings:
  Runtime: nodejs20.x
Resources:
  Fn:
    Properties:
      Runtime: 'nodejs20.x' # keep this comment
      Role: !GetAtt Role.Arn
      Layers:
        - !Ref SharedLayer
      Tags:
        - Key: Runtime
          Value: nodejs20.x
      Description: |
        Runtime: nodejs20.x
      Environment:
        Variables:
          Runtime: nodejs20.x
    Type: AWS::Lambda::Function
  Other:
    Type: Custom::Worker
    Properties:
      Runtime: nodejs20.x
`;
    writeFileSync(file, original.replaceAll('\n', '\r\n'));
    const r = run(['iac', '--path', file, '--apply']);
    assert.equal(r.status, 0, r.stderr);
    assert.equal(readFileSync(file, 'utf8'), original.replace("Runtime: 'nodejs20.x'", "Runtime: 'nodejs24.x'").replaceAll('\n', '\r\n'));
  } finally { cleanup(); }
});

test('iac recognizes SAM Transform sequences and leaves quoted list data intact', () => {
  const { dir, cleanup } = scratch();
  try {
    const file = join(dir, 'template.yaml');
    const original = "Transform:\n  - 'AWS::Serverless-2016-10-31'\nGlobals:\n  Function:\n    Runtime: nodejs20.x\n";
    writeFileSync(file, original);
    const r = run(['iac', '--path', file, '--apply']);
    assert.equal(r.status, 0, r.stderr);
    assert.equal(readFileSync(file, 'utf8'), original.replace('Runtime: nodejs20.x', 'Runtime: nodejs24.x'));
  } finally { cleanup(); }
});

test('iac handles inline SAM YAML and Globals without changing unrelated maps', () => {
  const { dir, cleanup } = scratch();
  try {
    const file = join(dir, 'template.yaml');
    const original = 'Transform: AWS::Serverless-2016-10-31\nGlobals: { Function: { Runtime: nodejs20.x }, Api: { Runtime: nodejs20.x } }\nResources:\n  Fn: { Type: AWS::Serverless::Function, Properties: { Runtime: "nodejs18.x" } }\n';
    writeFileSync(file, original);
    const r = run(['iac', '--path', file, '--apply']);
    assert.equal(r.status, 0, r.stderr);
    assert.equal(readFileSync(file, 'utf8'), original.replace('Function: { Runtime: nodejs20.x }', 'Function: { Runtime: nodejs24.x }').replace('"nodejs18.x"', '"nodejs24.x"'));
  } finally { cleanup(); }
});

test('iac Serverless only edits AWS provider and direct function runtimes', () => {
  const { dir, cleanup } = scratch();
  try {
    const file = join(dir, 'serverless.yml');
    const original = 'service: fixture\nprovider:\n  name: aws\n  runtime: nodejs20.x\n  environment:\n    runtime: nodejs20.x\nfunctions:\n  worker:\n    runtime: "nodejs18.x"\ncustom:\n  runtime: nodejs20.x\n  templateType: AWS::Lambda::Function\n';
    writeFileSync(file, original);
    const r = run(['iac', '--path', file, '--apply']);
    assert.equal(r.status, 0, r.stderr);
    assert.equal(readFileSync(file, 'utf8'), original.replace('  runtime: nodejs20.x', '  runtime: nodejs24.x').replace('"nodejs18.x"', '"nodejs24.x"'));
    writeFileSync(file, original.replace('name: aws', 'name: azure'));
    assert.equal(run(['iac', '--path', file, '--apply']).status, 0);
    assert.equal(readFileSync(file, 'utf8'), original.replace('name: aws', 'name: azure'));
  } finally { cleanup(); }
});

test('iac Terraform JSON scopes changes to aws_lambda_function', () => {
  const { dir, cleanup } = scratch();
  try {
    const file = join(dir, 'main.tf.json');
    const original = '{"resource":{"aws_lambda_function":{"fn":{"runtime":"nodejs20.x"}},"other":{"fn":{"runtime":"nodejs20.x"}}},"locals":{"runtime":"nodejs20.x"}}';
    writeFileSync(file, original);
    assert.equal(run(['iac', '--path', file, '--apply']).status, 0);
    assert.equal(readFileSync(file, 'utf8'), original.replace('"nodejs20.x"', '"nodejs24.x"'));
  } finally { cleanup(); }
});

test('iac refuses ambiguous or invalid templates before writing any batch member', () => {
  const invalid = [
    ['bad.json', '{"Resources":{"Fn":{"Type":"AWS::Lambda::Function","Properties":{"Runtime":"nodejs20.x"}}}'],
    ['bad.json', '{"Resources":{"Fn":{"Type":"AWS::Lambda::Function","Properties":{"Runtime":"nodejs20.x","Runtime":"nodejs18.x"}}}}'],
    ['bad.yaml', 'Resources:\n  Fn:\n    Type: AWS::Lambda::Function\n    Properties:\n      Runtime: !Ref SelectedRuntime\n'],
    ['bad.yaml', 'Resources:\n  Fn: { Type: AWS::Lambda::Function,\n    Properties: { Runtime: nodejs20.x } }\n'],
  ];
  for (const [name, content] of invalid) {
    const { dir, cleanup } = scratch();
    try {
      const good = join(dir, 'a-template.yaml');
      const original = 'Resources:\n  Fn:\n    Type: AWS::Lambda::Function\n    Properties:\n      Runtime: nodejs20.x\n';
      writeFileSync(good, original);
      writeFileSync(join(dir, name), content);
      const r = run(['iac', '--path', dir, '--apply']);
      assert.equal(r.status, 2, r.stdout + r.stderr);
      assert.equal(readFileSync(good, 'utf8'), original);
      assert.equal(readFileSync(join(dir, name), 'utf8'), content);
    } finally { cleanup(); }
  }
});

test('iac does not treat runtime prefixes or regex syntax as literal runtimes', () => {
  const { dir, cleanup } = scratch();
  try {
    const file = join(dir, 'template.yaml');
    const original = 'Resources:\n  Fn:\n    Type: AWS::Lambda::Function\n    Properties:\n      Runtime: nodejs20Xx\n';
    writeFileSync(file, original);
    assert.equal(run(['iac', '--path', file, '--apply']).status, 0);
    assert.equal(readFileSync(file, 'utf8'), original);
    assert.equal(run(['iac', '--path', file, '--from', 'nodejs20.*', '--apply']).status, 2);
    assert.equal(readFileSync(file, 'utf8'), original);
  } finally { cleanup(); }
});

test('iac Terraform HCL preserves locals, other resources, nested values, comments and heredocs', () => {
  const { dir, cleanup } = scratch();
  try {
    const file = join(dir, 'main.tf');
    const original = `locals {
  runtime = "nodejs20.x"
  example = <<EOF
resource "aws_lambda_function" "fake" { runtime = "nodejs20.x" }
EOF
}
# resource "aws_lambda_function" "fake" { runtime = "nodejs20.x" }
resource "other" "x" { runtime = "nodejs20.x" }
resource "aws_lambda_function" "real" {
  runtime = "nodejs20.x" # keep
  tags = { runtime = "nodejs20.x" }
}
`;
    writeFileSync(file, original);
    const r = run(['iac', '--path', file, '--apply']);
    assert.equal(r.status, 0, r.stderr);
    assert.equal(readFileSync(file, 'utf8'), original.replace('runtime = "nodejs20.x" # keep', 'runtime = "nodejs24.x" # keep'));
  } finally { cleanup(); }
});
