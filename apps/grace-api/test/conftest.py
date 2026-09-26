"""Shared, opt-in fixtures for the lead-bus tests.

The older test modules keep their own ``_load_app`` helpers; nothing here runs
unless a test asks for it by name. Outbound email is always replaced by a
recorder and RESEND_API_KEY is unset, so no test can reach Resend.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from leadbus_support import (
    BASE_ENV,
    CLEARED_ENV,
    call_asgi,
    fresh_import,
    install_email_recorder,
)


@pytest.fixture(name="fresh_import")
def fresh_import_fixture():
    return fresh_import


@pytest.fixture
def grace_env(tmp_path, monkeypatch):
    """Point the API at a throwaway data dir with test-mode settings."""

    def apply(**overrides: str) -> Path:
        env = {**BASE_ENV, "EOLKITS_DATA_DIR": str(tmp_path), **overrides}
        for key in CLEARED_ENV:
            if key not in env:
                monkeypatch.delenv(key, raising=False)
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        return Path(env["EOLKITS_DATA_DIR"])

    return apply


@pytest.fixture
def load_grace(grace_env, monkeypatch):
    """Factory: (app module, TestClient) for a fresh app on a fresh database."""
    from fastapi.testclient import TestClient

    def load(*, raise_server_exceptions: bool = True, **env: str):
        grace_env(**env)
        mod = fresh_import("eolkits_grace.app")
        mod.store.init()
        mod.sent_emails = install_email_recorder(mod, monkeypatch)
        client = TestClient(
            mod.app, follow_redirects=False, raise_server_exceptions=raise_server_exceptions
        )
        return mod, client

    return load


@pytest.fixture
def asgi():
    return call_asgi


@pytest.fixture
def secure_delete_off(monkeypatch):
    """Start every new SQLite connection with secure_delete OFF, as some SQLite
    builds do, so erasure tests prove the code turns it on by itself."""
    real_connect = sqlite3.connect

    def connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs)
        conn.execute("PRAGMA secure_delete = OFF")
        return conn

    monkeypatch.setattr(sqlite3, "connect", connect)


@pytest.fixture
def db_bytes():
    """Everything SQLite has on disk for the app's database: file plus WAL."""

    def read(mod) -> bytes:
        db = mod.settings.db_path
        wal = Path(str(db) + "-wal")
        return db.read_bytes() + (wal.read_bytes() if wal.exists() else b"")

    return read
