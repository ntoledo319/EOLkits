"""Byte-local edits of direct runtime attributes in Lambda HCL resource blocks."""

import re


def patch_terraform(text, source_runtimes, target_runtime):
    tokens = []
    cursor = 0
    while cursor < len(text):
        rest = text[cursor:]
        skipped = re.match(r"(?:\s+|#[^\r\n]*|//[^\r\n]*)", rest)
        if skipped:
            cursor += len(skipped[0])
            continue
        if rest.startswith("/*"):
            end = text.find("*/", cursor + 2)
            if end < 0:
                raise ValueError("Unterminated Terraform comment; no changes written")
            cursor = end + 2
            continue
        heredoc = re.match(r"<<-?([A-Za-z_][\w-]*)[^\S\r\n]*\r?\n", rest)
        if heredoc:
            body_start = cursor + len(heredoc[0])
            end = re.search(
                r"^[ \t]*" + re.escape(heredoc[1]) + r"[ \t]*\r?$", text[body_start:], re.MULTILINE
            )
            if not end:
                raise ValueError("Unterminated Terraform heredoc; no changes written")
            cursor = body_start + end.end()
            tokens.append(("<heredoc>", False, cursor, cursor))
            continue
        quoted = re.match(r'"(?:\\[\s\S]|[^"\\])*"', rest)
        if rest[0] == '"' and not quoted:
            raise ValueError("Unterminated Terraform string; no changes written")
        identifier = re.match(r"[A-Za-z_][\w-]*", rest)
        raw = quoted[0] if quoted else identifier[0] if identifier else rest[0]
        tokens.append((raw[1:-1] if quoted else raw, bool(quoted), cursor, cursor + len(raw)))
        cursor += len(raw)
    blocks = []
    matches = []
    for i, (value, quoted, _, _) in enumerate(tokens):
        if not quoted and value == "{":
            is_lambda = (
                not blocks
                and i >= 3
                and tokens[i - 3][0] == "resource"
                and tokens[i - 2][:2] == ("aws_lambda_function", True)
                and tokens[i - 1][1]
            )
            blocks.append(is_lambda)
        elif not quoted and value == "}":
            if not blocks:
                raise ValueError("Unbalanced Terraform braces; no changes written")
            blocks.pop()
        elif blocks == [True] and not quoted and value == "runtime" and i + 2 < len(tokens):
            candidate = tokens[i + 2]
            if (
                tokens[i + 1][0] == "="
                and candidate[1]
                and candidate[0] in source_runtimes
                and candidate[0] != target_runtime
            ):
                matches.append(candidate)
    if blocks:
        raise ValueError("Unbalanced Terraform braces; no changes written")
    changed = text
    for _, _, start, end in reversed(matches):
        changed = changed[:start] + '"' + target_runtime + '"' + changed[end:]
    return changed, len(matches)
