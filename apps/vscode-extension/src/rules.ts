export interface RuleMatch {
    severity: 'critical' | 'high' | 'medium' | 'low';
    message: string;
    index: number;
    code: string;
}

function matches(
    text: string,
    pattern: RegExp,
    make: (match: RegExpExecArray) => Omit<RuleMatch, 'index'>
): RuleMatch[] {
    const findings: RuleMatch[] = [];
    let match: RegExpExecArray | null;
    while ((match = pattern.exec(text)) !== null) {
        findings.push({ ...make(match), index: match.index });
    }
    return findings;
}

export function scanStructuredText(text: string): RuleMatch[] {
    const findings = matches(
        text,
        /\b[Rr]untime\b["']?\s*[:=]\s*["']?nodejs(18|20|22)\.x\b/g,
        match => {
            const version = match[1];
            const dates: Record<string, string> = {
                '18': '2025-09-01',
                '20': '2026-04-30',
                '22': '2027-04-30'
            };
            return {
                severity: version === '22' ? 'medium' : 'high',
                message: `Lambda Node.js ${version} has an AWS deprecation timeline (projected deprecation: ${dates[version]}); review the current create/update block dates`,
                code: `LAMBDA_NODE${version}_EOL`
            };
        }
    );
    findings.push(...matches(
        text,
        /\b[Rr]untime\b["']?\s*[:=]\s*["']?python3\.(9|10|11)\b/g,
        match => {
            const version = match[1];
            const dates: Record<string, string> = {
                '9': '2025-12-15',
                '10': '2026-10-31',
                '11': '2027-06-30'
            };
            return {
                severity: version === '9' ? 'high' : 'medium',
                message: `Lambda Python 3.${version} deprecated (AWS Lambda EOL: ${dates[version]})`,
                code: `LAMBDA_PYTHON3${version}_EOL`
            };
        }
    ));
    findings.push(...matches(
        text,
        /(?:ImageId[^\n]*amazonlinux2|\bAMI\b[^\n]*\bAL2\b)/gi,
        () => ({
            severity: 'high',
            message: 'Amazon Linux 2 reached EOL on 2026-06-30; plan an AL2023 migration',
            code: 'AMAZON_LINUX2_EOL'
        })
    ));
    return findings;
}

export function scanJavaScriptText(text: string): RuleMatch[] {
    return matches(
        text,
        /require\(['"]aws-sdk['"]\)|from ['"]aws-sdk['"]/g,
        () => ({
            severity: 'medium',
            message: 'aws-sdk v2 is not bundled in Lambda Node.js 18+; bundle it or migrate to AWS SDK v3',
            code: 'AWS_SDK_V2_DEPRECATED'
        })
    );
}

export function scanPythonText(text: string): RuleMatch[] {
    const rules: Array<[RegExp, string]> = [
        [/from distutils\b/g, 'distutils deprecated, use setuptools'],
        [/import imp\b/g, 'imp module deprecated, use importlib'],
        [/from collections import[^\n]*\bMapping\b/g, 'collections.Mapping deprecated, use collections.abc.Mapping']
    ];
    return rules.flatMap(([pattern, message]) => matches(text, pattern, () => ({
        severity: message.startsWith('collections.') ? 'low' : 'medium',
        message,
        code: 'PYTHON_DEPRECATED_MODULE'
    })));
}

export function scanTerraformText(text: string): RuleMatch[] {
    return matches(
        text,
        /(?:ami[^\n]*amazon-linux-2|al2-ami)/gi,
        () => ({
            severity: 'high',
            message: 'Amazon Linux 2 reached EOL on 2026-06-30; review this AMI reference',
            code: 'TF_AL2_AMI_DEPRECATED'
        })
    );
}
