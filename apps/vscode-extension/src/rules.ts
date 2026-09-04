export interface RuleMatch {
    severity: 'critical' | 'high' | 'medium' | 'low';
    message: string;
    index: number;
    code: string;
}

interface RuntimeRule {
    label: string;
    deprecationDate: string;
    projected: boolean;
    severity: RuleMatch['severity'];
    code: string;
}

const LAMBDA_RUNTIMES: Record<string, RuntimeRule> = {
    'nodejs16.x': {
        label: 'Lambda Node.js 16',
        deprecationDate: '2024-06-12',
        projected: false,
        severity: 'high',
        code: 'LAMBDA_NODE16_EOL'
    },
    'nodejs18.x': {
        label: 'Lambda Node.js 18',
        deprecationDate: '2025-09-01',
        projected: false,
        severity: 'high',
        code: 'LAMBDA_NODE18_EOL'
    },
    'nodejs20.x': {
        label: 'Lambda Node.js 20',
        deprecationDate: '2026-04-30',
        projected: false,
        severity: 'high',
        code: 'LAMBDA_NODE20_EOL'
    },
    'nodejs22.x': {
        label: 'Lambda Node.js 22',
        deprecationDate: '2027-04-30',
        projected: true,
        severity: 'medium',
        code: 'LAMBDA_NODE22_EOL'
    },
    'python3.8': {
        label: 'Lambda Python 3.8',
        deprecationDate: '2024-10-14',
        projected: false,
        severity: 'high',
        code: 'LAMBDA_PYTHON38_EOL'
    },
    'python3.9': {
        label: 'Lambda Python 3.9',
        deprecationDate: '2025-12-15',
        projected: false,
        severity: 'high',
        code: 'LAMBDA_PYTHON39_EOL'
    },
    'python3.10': {
        label: 'Lambda Python 3.10',
        deprecationDate: '2026-10-31',
        projected: true,
        severity: 'high',
        code: 'LAMBDA_PYTHON310_EOL'
    },
    'python3.11': {
        label: 'Lambda Python 3.11',
        deprecationDate: '2027-06-30',
        projected: true,
        severity: 'medium',
        code: 'LAMBDA_PYTHON311_EOL'
    }
};

const RUNTIME_VALUE = '(nodejs(?:16|18|20|22)\\.x|python3\\.(?:8|9|10|11))';

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

function runtimeMatches(
    text: string,
    pattern: RegExp,
    offset = 0,
    include: (index: number) => boolean = () => true
): RuleMatch[] {
    return matches(text, pattern, match => {
        const runtime = match[1].toLowerCase();
        const rule = LAMBDA_RUNTIMES[runtime];
        const status = rule.projected
            ? `has an AWS-projected deprecation date of ${rule.deprecationDate}`
            : `was deprecated by AWS Lambda on ${rule.deprecationDate}`;
        return {
            severity: rule.severity,
            message: `${rule.label} ${status}; verify the current create/update block dates`,
            code: rule.code
        };
    })
        .filter(finding => include(finding.index))
        .map(finding => ({ ...finding, index: finding.index + offset }));
}

interface TerraformLexicalView {
    codeMask: Uint8Array;
    searchableText: string;
}

function terraformLexicalView(text: string): TerraformLexicalView {
    const codeMask = new Uint8Array(text.length);
    const visibleMask = new Uint8Array(text.length);
    let cursor = 0;

    while (cursor < text.length) {
        const character = text[cursor];
        const next = text[cursor + 1] || '';

        if (character === '#' || (character === '/' && next === '/')) {
            const newline = text.indexOf('\n', cursor);
            cursor = newline === -1 ? text.length : newline;
            continue;
        }
        if (character === '/' && next === '*') {
            const end = text.indexOf('*/', cursor + 2);
            cursor = end === -1 ? text.length : end + 2;
            continue;
        }
        if (character === '"' || character === "'") {
            const quote = character;
            codeMask[cursor] = 1;
            visibleMask[cursor++] = 1;
            let escaped = false;
            while (cursor < text.length) {
                const quotedCharacter = text[cursor];
                visibleMask[cursor] = 1;
                if (escaped) {
                    escaped = false;
                } else if (quotedCharacter === '\\') {
                    escaped = true;
                } else if (quotedCharacter === quote) {
                    codeMask[cursor++] = 1;
                    break;
                }
                cursor++;
            }
            continue;
        }
        if (character === '<' && next === '<') {
            const heredoc = /^<<(-?)([A-Za-z_][A-Za-z0-9_-]*)[^\S\r\n]*(?:\r?\n|$)/.exec(
                text.slice(cursor)
            );
            if (heredoc) {
                codeMask.fill(1, cursor, cursor + heredoc[0].length);
                visibleMask.fill(1, cursor, cursor + heredoc[0].length);
                cursor += heredoc[0].length;
                const allowIndent = heredoc[1] === '-';
                const delimiter = heredoc[2];
                while (cursor < text.length) {
                    const newline = text.indexOf('\n', cursor);
                    const lineEnd = newline === -1 ? text.length : newline;
                    const line = text.slice(cursor, lineEnd).replace(/\r$/, '');
                    const closesHeredoc = allowIndent
                        ? line.trim() === delimiter
                        : line === delimiter;
                    cursor = newline === -1 ? text.length : newline + 1;
                    if (closesHeredoc) break;
                }
                continue;
            }
        }

        codeMask[cursor] = 1;
        visibleMask[cursor++] = 1;
    }

    const searchableText = Array.from(
        { length: text.length },
        (_, index) => visibleMask[index] === 1 || text[index] === '\n' ? text[index] : ' '
    ).join('');
    return { codeMask, searchableText };
}

interface TerraformBlock {
    text: string;
    offset: number;
    openingBrace: number;
}

function terraformLambdaBlocks(text: string, codeMask: Uint8Array): TerraformBlock[] {
    const blocks: TerraformBlock[] = [];
    const resource = /\bresource\s+"aws_lambda_function"\s+"[^"]+"\s*\{/g;
    let match: RegExpExecArray | null;

    while ((match = resource.exec(text)) !== null) {
        if (codeMask[match.index] !== 1) continue;
        const openingBrace = match.index + match[0].lastIndexOf('{');
        let depth = 1;
        let cursor = openingBrace + 1;

        for (; cursor < text.length && depth > 0; cursor++) {
            if (codeMask[cursor] !== 1) continue;
            if (text[cursor] === '{') {
                depth++;
            } else if (text[cursor] === '}') {
                depth--;
            }
        }

        if (depth === 0) {
            blocks.push({
                text: text.slice(match.index, cursor),
                offset: match.index,
                openingBrace
            });
            resource.lastIndex = cursor;
        } else {
            break;
        }
    }
    return blocks;
}

function terraformBraceDepthAt(
    text: string,
    codeMask: Uint8Array,
    openingBrace: number,
    index: number
): number {
    let depth = 0;
    for (let cursor = openingBrace; cursor < index; cursor++) {
        if (codeMask[cursor] !== 1) continue;
        if (text[cursor] === '{') depth++;
        else if (text[cursor] === '}') depth--;
    }
    return depth;
}

export function scanStructuredText(text: string): RuleMatch[] {
    const runtimePattern = new RegExp(
        `\\bRuntime\\b["']?\\s*[:=]\\s*["']?${RUNTIME_VALUE}\\b`,
        'g'
    );
    const findings = runtimeMatches(text, runtimePattern);
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
    const { codeMask, searchableText } = terraformLexicalView(text);
    const findings = matches(
        searchableText,
        /(?:ami[^\n]*amazon-linux-2|al2-ami)/gi,
        () => ({
            severity: 'high',
            message: 'Amazon Linux 2 reached EOL on 2026-06-30; review this AMI reference',
            code: 'TF_AL2_AMI_DEPRECATED'
        })
    );
    const runtimePattern = new RegExp(
        `\\bruntime\\s*=\\s*["']?${RUNTIME_VALUE}\\b`,
        'gi'
    );
    for (const block of terraformLambdaBlocks(text, codeMask)) {
        findings.push(...runtimeMatches(
            block.text,
            runtimePattern,
            block.offset,
            localIndex => {
                const absoluteIndex = block.offset + localIndex;
                return codeMask[absoluteIndex] === 1 && terraformBraceDepthAt(
                    text,
                    codeMask,
                    block.openingBrace,
                    absoluteIndex
                ) === 1;
            }
        ));
    }
    return findings;
}
