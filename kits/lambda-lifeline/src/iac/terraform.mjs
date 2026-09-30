// Tokenize enough HCL to locate direct runtime attributes of top-level Lambda
// resource blocks. Comments, quoted text and heredocs never become configuration.
export function patchTerraform(text, from, to) {
  const tokens = [];
  let cursor = 0;
  while (cursor < text.length) {
    const rest = text.slice(cursor);
    const skipped = rest.match(/^(?:\s+|#[^\r\n]*|\/\/[^\r\n]*)/);
    if (skipped) { cursor += skipped[0].length; continue; }
    if (rest.startsWith('/*')) {
      const end = text.indexOf('*/', cursor + 2);
      if (end < 0) throw new Error('Unterminated Terraform comment; no changes written.');
      cursor = end + 2;
      continue;
    }
    const heredoc = rest.match(/^<<-?([A-Za-z_][\w-]*)[^\S\r\n]*\r?\n/);
    if (heredoc) {
      const bodyStart = cursor + heredoc[0].length;
      const end = new RegExp(`^[ \\t]*${heredoc[1]}[ \\t]*\\r?$`, 'm').exec(text.slice(bodyStart));
      if (!end) throw new Error('Unterminated Terraform heredoc; no changes written.');
      cursor = bodyStart + end.index + end[0].length;
      tokens.push({ value: '<heredoc>' });
      continue;
    }
    const quoted = rest.match(/^"(?:\\[\s\S]|[^"\\])*"/);
    if (rest[0] === '"' && !quoted) throw new Error('Unterminated Terraform string; no changes written.');
    const raw = quoted?.[0] || rest.match(/^[A-Za-z_][\w-]*/)?.[0] || rest[0];
    tokens.push({ value: quoted ? raw.slice(1, -1) : raw, quoted: Boolean(quoted), start: cursor, end: cursor + raw.length });
    cursor += raw.length;
  }
  const blocks = [];
  const matches = [];
  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    if (!token.quoted && token.value === '{') {
      blocks.push(blocks.length === 0 && tokens[i - 3]?.value === 'resource'
        && tokens[i - 2]?.quoted && tokens[i - 2]?.value === 'aws_lambda_function'
        && Boolean(tokens[i - 1]?.quoted));
    } else if (!token.quoted && token.value === '}') {
      if (!blocks.length) throw new Error('Unbalanced Terraform braces; no changes written.');
      blocks.pop();
    } else if (blocks.length === 1 && blocks[0] && !token.quoted && token.value === 'runtime'
      && tokens[i + 1]?.value === '=' && tokens[i + 2]?.quoted
      && from.includes(tokens[i + 2].value) && tokens[i + 2].value !== to) {
      matches.push(tokens[i + 2]);
    }
  }
  if (blocks.length) throw new Error('Unbalanced Terraform braces; no changes written.');
  let changed = text;
  for (const token of [...matches].reverse()) {
    changed = changed.slice(0, token.start) + JSON.stringify(to) + changed.slice(token.end);
  }
  return { changed, hits: matches.map(token => token.value) };
}
