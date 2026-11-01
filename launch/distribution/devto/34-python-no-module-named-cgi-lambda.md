---
title: '"ModuleNotFoundError: No module named ''cgi''" — fixing the Python 3.13 Lambda cold-start crash'
canonical_url: https://eolkits.com/fix/python-no-module-named-cgi/
description: The cgi and cgitb modules are gone in Python 3.13. Here are the exact drop-in replacements for parse_qs, FieldStorage, escape, and cgitb — so your Lambda cold-starts again.
tags: python, aws, lambda, serverless
---

Switch a Lambda function to `python3.13` and the cold start may die with:

```
[ERROR] Runtime.ImportModuleError: Unable to import module 'lambda_function':
No module named 'cgi'
```

or, if the import is buried in a dependency:

```
ModuleNotFoundError: No module named 'cgi'
```

The `cgi` module was removed in Python 3.13. Here is what replaces each part of it.

## Why it disappeared

[PEP 594](https://peps.python.org/pep-0594/) removed 19 long-deprecated "dead batteries" from the standard library in Python 3.13. `cgi` and `cgitb` were on that list. They had been deprecated since Python 3.11 — `python3.13` Lambda functions (available since November 2024, running on Amazon Linux 2023) are the first runtimes where the import simply fails.

The module served CGI scripts, a deployment model that predates modern web frameworks by decades. Its API was not extended after Python 2. PEP 594's migration notes point to narrower, maintained replacements for each use case.

## Fix by use case

### `cgi.parse_qs` → `urllib.parse.parse_qs`

This is the most common hit. `cgi.parse_qs` was a thin alias for `urllib.parse.parse_qs` since Python 3.x. The fix is a one-line import change:

```python
# Before (breaks on python3.13)
from cgi import parse_qs
params = parse_qs(environ['QUERY_STRING'])

# After
from urllib.parse import parse_qs
params = parse_qs(environ['QUERY_STRING'])
```

Same signature, same return value. No new dependency.

### `cgi.escape` → `html.escape`

`cgi.escape` was removed even earlier (Python 3.8), but code that survived on older runtimes may still use it. Its replacement has been in the standard library since Python 3.2:

```python
# Before
from cgi import escape
safe = escape('<script>alert("xss")</script>')

# After
from html import escape
safe = escape('<script>alert("xss")</script>')
```

`html.escape` also quotes single quotes by default when you pass `quote=True`. Check your call sites if that matters.

### `cgi.parse_header` → `email.message`

`cgi.parse_header` parsed `Content-Type` header values such as `multipart/form-data; boundary=----abc`. Its PEP 594-recommended replacement:

```python
# Before
from cgi import parse_header
content_type, params = parse_header(event['headers']['content-type'])

# After
from email.message import Message
m = Message()
m['content-type'] = event['headers']['content-type']
content_type = m.get_content_type()
params = dict(m.get_params()[1:])  # skip the content-type itself
```

### `cgi.FieldStorage` (multipart form body) → `multipart` library

`FieldStorage` parsed `multipart/form-data` request bodies — common in file-upload handlers. The closest maintained replacement is the `multipart` library (pure Python, actively maintained):

```python
# Before
from cgi import FieldStorage
import io
environ['wsgi.input'] = io.BytesIO(body_bytes)
form = FieldStorage(fp=environ['wsgi.input'], environ=environ)
file_bytes = form['upload'].file.read()

# After
import multipart

def on_field(field):
    print(field.field_name, field.value)

def on_file(file):
    data = file.file_object.read()

multipart.multipart.create_form_parser(headers, on_field, on_file)
```

Add it to `requirements.txt`:

```
multipart
```

If you use a web framework (Flask, FastAPI, Chalice), its request object already handles multipart for you — delete the `FieldStorage` code entirely.

### `cgitb` → `traceback` or structured logging

`cgitb` generated HTML-formatted tracebacks for CGI debugging. On Lambda, structured logging is the right approach:

```python
# Before
import cgitb; cgitb.enable()

# After — structured exception logging (works in CloudWatch)
import traceback, logging, json

logger = logging.getLogger()

def handler(event, context):
    try:
        return your_logic(event)
    except Exception as e:
        logger.error(json.dumps({
            "error": str(e),
            "traceback": traceback.format_exc(),
        }))
        raise
```

CloudWatch Logs Insights queries on `error` and `traceback` fields are easier to use than HTML output anyway.

## Finding all the imports at once

Search your codebase and dependencies in one pass:

```bash
grep -rn 'import cgi\b\|from cgi import\|import cgitb\|from cgitb import' .
```

Then check your pinned dependencies for the same:

```bash
pip show <package> | grep -i location
grep -r 'import cgi' $(pip show <package> | grep Location | cut -d' ' -f2)
```

If a third-party dependency is the importer, check its changelog for a release that dropped `cgi` — most actively maintained packages have already shipped one.

## Before you redeploy

1. Run `python3.13 -c "import <your_handler_module>"` inside `public.ecr.aws/lambda/python:3.13` — every `ModuleNotFoundError` from this class of removal is visible at import time, before any Lambda invoke.
2. `cgi` is one of 19 modules removed by PEP 594. A single upgrade to `python3.13` can surface `cgi`, `cgitb`, `crypt`, `audioop`, `telnetlib`, `pipes`, `aifc`, and others simultaneously. Run the container check after each fix, not just once.
3. Confirm the cold start is clean with `aws lambda invoke --function-name <name> /dev/null && aws logs tail /aws/lambda/<name> --since 2m`.

---

[EOLkits](https://eolkits.com/scan) can scan your Lambda functions and flag runtimes and dependencies with known compatibility issues before you flip the runtime switch.
