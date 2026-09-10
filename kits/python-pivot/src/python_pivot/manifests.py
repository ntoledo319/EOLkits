"""Source spans for JSON and a bounded block-mapping YAML editing surface.

This is not a general YAML loader: structural aliases, multiline flow mappings
and dynamic runtime values require manual review. Single-line flow mappings and
opaque list data are supported; unrelated tagged values/comments are kept.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Node:
    entries: Optional[dict] = None
    items: Optional[list] = None
    value: object = None
    start: int = 0
    end: int = 0
    quote: str = ""
    opaque: bool = False


def _put(node: Node, key: str, value: Node) -> None:
    if node.entries is None:
        raise ValueError("Mixed YAML mapping and sequence; review manually")
    if key in node.entries:
        raise ValueError(f"Duplicate manifest key {key!r}; review manually")
    node.entries[key] = value


def parse_json(text: str) -> Node:
    def invalid_constant(value):
        raise ValueError(f"Invalid JSON constant {value}")

    json.loads(text, parse_constant=invalid_constant)
    tokens = list(re.finditer(r'"(?:\\[\s\S]|[^"\\])*"|[{}\[\]:,]|[^\s{}\[\]:,]+', text))
    cursor = 0

    def value() -> Node:
        nonlocal cursor
        token = tokens[cursor]
        cursor += 1
        if token[0] == "{":
            result = Node(entries={})
            while tokens[cursor][0] != "}":
                key = json.loads(tokens[cursor][0])
                cursor += 2  # key and colon; json.loads validated the grammar
                _put(result, key, value())
                if tokens[cursor][0] == ",":
                    cursor += 1
            cursor += 1
            return result
        if token[0] == "[":
            items = []
            while tokens[cursor][0] != "]":
                items.append(value())
                if tokens[cursor][0] == ",":
                    cursor += 1
            cursor += 1
            return Node(items=items)
        return Node(value=json.loads(token[0]), start=token.start(), end=token.end(), quote='"')

    return value()


def _uncomment(raw: str) -> str:
    quote = None
    collection = raw[:1] in ("[", "{")
    i = 0
    while i < len(raw):
        char = raw[i]
        if quote == '"' and char == "\\":
            i += 2
            continue
        if char == quote:
            if quote == "'" and raw[i + 1 : i + 2] == "'":
                i += 2
                continue
            quote = None
        elif quote is None and (i == 0 or collection) and char in "\"'":
            quote = char
        elif quote is None and char == "#" and (i == 0 or raw[i - 1].isspace()):
            return raw[:i].rstrip()
        i += 1
    if quote:
        raise ValueError("Unterminated YAML string; review manually")
    return raw.rstrip()


def _scalar(raw: str, start: int) -> Node:
    quote = raw[0] if raw[:1] in ('"', "'") else ""
    val = raw
    if quote:
        if raw[-1] != quote:
            raise ValueError("Unsupported YAML scalar; review manually")
        val = json.loads(raw) if quote == '"' else raw[1:-1].replace("''", "'")
    opaque = not quote and bool(re.match(r"[!&*|>\[{]", raw))
    return Node(value=val, start=start, end=start + len(raw), quote=quote, opaque=opaque)


def _flow(raw: str, start: int) -> Node:
    """Read a single-line flow collection; reject ambiguous multiline syntax."""
    cursor = 0

    def space():
        nonlocal cursor
        while cursor < len(raw) and raw[cursor].isspace():
            cursor += 1

    def atom(key=False):
        nonlocal cursor
        space()
        begin = cursor
        quote = raw[cursor : cursor + 1]
        if quote in ('"', "'"):
            cursor += 1
            while cursor < len(raw):
                if quote == '"' and raw[cursor] == "\\":
                    cursor += 2
                    continue
                char = raw[cursor]
                cursor += 1
                if char == quote:
                    if quote == "'" and raw[cursor : cursor + 1] == "'":
                        cursor += 1
                        continue
                    return _scalar(raw[begin:cursor], start + begin)
            raise ValueError("Unterminated flow YAML string; review manually")
        delimiters = ":,{}[]" if key else ",{}[]"
        while cursor < len(raw) and raw[cursor] not in delimiters:
            cursor += 1
        val = raw[begin:cursor].rstrip()
        if not val:
            raise ValueError("Unsupported flow YAML value; review manually")
        return _scalar(val, start + begin)

    def value():
        nonlocal cursor
        space()
        opening = raw[cursor : cursor + 1]
        if opening not in ("{", "["):
            return atom()
        cursor += 1
        result = Node(entries={}) if opening == "{" else Node(items=[])
        close = "}" if opening == "{" else "]"
        space()
        while raw[cursor : cursor + 1] != close:
            if cursor >= len(raw):
                raise ValueError("Multiline or unterminated flow YAML needs manual review")
            if opening == "{":
                key = atom(key=True).value
                space()
                if raw[cursor : cursor + 1] != ":" or key == "<<":
                    raise ValueError("Unsupported flow YAML mapping; review manually")
                cursor += 1
                _put(result, key, value())
            else:
                result.items.append(value())
            space()
            if raw[cursor : cursor + 1] == ",":
                cursor += 1
                space()
            elif raw[cursor : cursor + 1] != close:
                raise ValueError("Unsupported flow YAML separator; review manually")
        cursor += 1
        return result

    result = value()
    space()
    if cursor != len(raw):
        raise ValueError("Unsupported trailing flow YAML; review manually")
    return result


def parse_yaml(text: str) -> Node:
    if text.lstrip().startswith("{"):
        try:
            return parse_json(text)
        except ValueError:
            if "\n" in text.strip():
                raise
            return _flow(_uncomment(text.strip()), text.index("{"))
    root = Node(entries={})
    stack = [(-1, root)]
    offset = 0
    opaque_indent = None
    seen_document = False
    seen_content = False
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        start = offset
        offset += len(line)
        if not body.strip() or body.lstrip().startswith("#"):
            continue
        if body == "---":
            if seen_document or seen_content:
                raise ValueError("Multiple YAML documents are not supported; split the templates")
            seen_document = True
            continue
        if body == "...":
            continue
        seen_content = True
        whitespace = body[: len(body) - len(body.lstrip())]
        if "\t" in whitespace:
            raise ValueError("YAML tab indentation is not supported; review manually")
        indent = len(whitespace)
        if opaque_indent is not None and indent > opaque_indent:
            continue
        opaque_indent = None
        item = re.fullmatch(r"-(?:\s+|$)(.*)", body[indent:])
        if item:
            while stack[-1][0] > indent:
                stack.pop()
            node = stack[-1][1]
            if node.entries:
                raise ValueError("Mixed YAML mapping and sequence; review manually")
            node.entries = None
            if node.items is None:
                node.items = []
            # Nested list data is opaque; literal Transform entries identify
            # SAM Globals but a sequence can never supply an editable runtime.
            node.items.append(_scalar(_uncomment(item[1]), 0))
            opaque_indent = indent
            continue
        pair = re.fullmatch(
            r"""("(?:\\.|[^"\\])*"|'(?:''|[^'])*'|[^:\s][^:]*?)\s*:(?:\s+|$)(.*)""", body[indent:]
        )
        if not pair:
            raise ValueError(
                "Unsupported YAML structure; use block mappings or JSON and review manually"
            )
        while stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        key = _scalar(pair[1].strip(), 0).value
        if not isinstance(key, str):
            raise ValueError("YAML mapping keys must be strings; review manually")
        if key == "<<":
            raise ValueError("YAML merge keys need manual review; no changes written")
        raw = _uncomment(pair[2])
        if not raw:
            node = Node(entries={})
            _put(parent, key, node)
            stack.append((indent, node))
        else:
            value_start = start + len(body) - len(pair[2])
            _put(
                parent,
                key,
                _flow(raw, value_start) if raw[0] in "[{" else _scalar(raw, value_start),
            )
            opaque_indent = indent  # Block strings/sequences must never become configuration.
    return root


def _object_at(node: Optional[Node], key: str) -> Optional[Node]:
    child = node.entries.get(key) if node and node.entries is not None else None
    if child and child.entries is None:
        raise ValueError(
            f"{key} must be an explicit mapping; resolve aliases or expressions manually"
        )
    return child


def runtime_nodes(root: Node, *, serverless=False, terraform=False) -> list:
    found = []

    def runtime(node: Optional[Node], key: str) -> None:
        value = node.entries.get(key) if node and node.entries is not None else None
        if value is None:
            return
        if (
            value.opaque
            or value.entries is not None
            or value.items is not None
            or not isinstance(value.value, str)
        ):
            raise ValueError(
                f"{key} is not a literal runtime; resolve it manually. No changes written"
            )
        found.append(value)

    if terraform:
        resources = _object_at(_object_at(root, "resource"), "aws_lambda_function")
        for resource in ((resources.entries or {}) if resources else {}).values():
            if resource.entries is None:
                raise ValueError("Terraform resources must be explicit mappings; review manually")
            runtime(resource, "runtime")
    elif serverless:
        provider = _object_at(root, "provider")
        if (
            not provider
            or provider.entries is None
            or provider.entries.get("name", Node()).value != "aws"
        ):
            return found
        runtime(provider, "runtime")
        functions = _object_at(root, "functions")
        for fn in ((functions.entries or {}) if functions else {}).values():
            if fn.entries is None:
                raise ValueError(
                    "Serverless function definitions must be explicit mappings; review manually"
                )
            runtime(fn, "runtime")
    else:
        resources = _object_at(root, "Resources")
        transform = root.entries.get("Transform", Node()) if root.entries is not None else Node()
        sam = transform.value == "AWS::Serverless-2016-10-31" or any(
            item.value == "AWS::Serverless-2016-10-31" for item in (transform.items or [])
        )
        for resource in ((resources.entries or {}) if resources else {}).values():
            if resource.entries is None:
                raise ValueError(
                    "CloudFormation resources must be explicit mappings; review manually"
                )
            kind = resource.entries.get("Type", Node())
            if kind.opaque or kind.entries is not None or kind.items is not None:
                raise ValueError(
                    "Resource Type must be a literal string; resolve aliases or expressions manually"
                )
            if kind.value == "AWS::Serverless::Function":
                sam = True
            if kind.value in ("AWS::Lambda::Function", "AWS::Serverless::Function"):
                runtime(_object_at(resource, "Properties"), "Runtime")
        if sam:
            runtime(_object_at(_object_at(root, "Globals"), "Function"), "Runtime")
    return found


def patch_manifest(text: str, *, json_format=False, source_runtimes, target_runtime, **options):
    root = parse_json(text) if json_format else parse_yaml(text)
    nodes = [
        node
        for node in runtime_nodes(root, **options)
        if node.value in source_runtimes and node.value != target_runtime
    ]
    changed = text
    for node in sorted(nodes, key=lambda item: item.start, reverse=True):
        replacement = (
            json.dumps(target_runtime)
            if node.quote == '"'
            else node.quote + target_runtime + node.quote
        )
        changed = changed[: node.start] + replacement + changed[node.end :]
    return changed, len(nodes)
