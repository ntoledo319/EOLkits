"""
Smoke tests for the runner. Exercises hash-anchored PDF metadata
without requiring WeasyPrint to be installed in CI's test matrix.
"""

import hashlib
import pytest


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def test_sha_anchor_format():
    payload = b"runtime: nodejs20.x"
    sha = _sha256_bytes(payload)
    assert len(sha) == 64
    assert all(c in "0123456789abcdef" for c in sha)


def test_runner_module_imports():
    # If audit_pdf.py imports cleanly, the module surface is intact.
    import importlib.util
    import os

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(here, "audit_pdf.py")
    spec = importlib.util.spec_from_file_location("audit_pdf", target)
    if spec is None:
        pytest.skip("audit_pdf.py not present")
    # Attempt import; tolerate WeasyPrint absence.
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except ImportError as e:
        if "weasyprint" in str(e).lower():
            pytest.skip("WeasyPrint not installed in this matrix")
        raise


def test_runner_http_auth_rejects_bad_token(monkeypatch):
    import importlib.util
    import os
    from io import BytesIO

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(here, "main.py")
    spec = importlib.util.spec_from_file_location("runner_main", target)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    writes = []
    handler = object.__new__(mod.RunnerHandler)
    handler.path = "/job"
    handler.headers = {"Authorization": "Bearer wrong", "Content-Length": "2"}
    handler.rfile = BytesIO(b"{}")
    monkeypatch.setenv("RUNNER_TOKEN", "expected")
    monkeypatch.setattr(handler, "send_response", lambda status: writes.append(("status", status)))
    monkeypatch.setattr(handler, "send_header", lambda key, value: None)
    monkeypatch.setattr(handler, "end_headers", lambda: None)
    handler.wfile = type("Writer", (), {"write": lambda _self, data: writes.append(("body", data))})()

    handler.do_POST()

    assert ("status", 401) in writes
    assert b"unauthorized" in dict(writes)["body"]
