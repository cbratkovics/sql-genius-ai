"""Offline test configuration, applied before application imports."""

import os
import socket

import pytest

# Tests cannot inherit a hosted database, provider key, or production signing key.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "offline-test-signing-key-not-for-deployment"
for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "REDIS_URL", "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
    os.environ.pop(name, None)


@pytest.fixture(autouse=True)
def prevent_external_network(monkeypatch):
    """In-process ASGI and SQLite need no INET connections or DNS."""
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def deny_network(*args, **kwargs):
        raise AssertionError("External network access is forbidden in offline tests")

    def connect(sock, *args, **kwargs):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            return deny_network(*args, **kwargs)
        return original_connect(sock, *args, **kwargs)

    def connect_ex(sock, *args, **kwargs):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            return deny_network(*args, **kwargs)
        return original_connect_ex(sock, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(socket, "getaddrinfo", deny_network)
