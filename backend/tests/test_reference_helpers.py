"""Exercise optional file/image helpers without cloud or database services."""

import asyncio
import base64
import gzip
import hashlib
import importlib
import json
import sys
import tarfile
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


@pytest.fixture
def backup_helpers(monkeypatch: pytest.MonkeyPatch) -> Iterator[ModuleType]:
    import boto3
    import redis.asyncio

    name = "backend.disaster_recovery.backup_manager"
    was_loaded = name in sys.modules
    package = importlib.import_module("backend.disaster_recovery")
    previous = getattr(package, "backup_manager", None)
    # The module's legacy global manager must not discover cloud credentials or
    # create network clients just to test its real filesystem helpers.
    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: SimpleNamespace())
    monkeypatch.setattr(redis.asyncio, "from_url", lambda *args, **kwargs: SimpleNamespace())
    module = importlib.import_module(name)
    yield module
    if not was_loaded:
        sys.modules.pop(name, None)
        if previous is None:
            delattr(package, "backup_manager")
        else:
            package.__dict__["backup_manager"] = previous


def test_backup_compression_preserves_binary_contents(
    backup_helpers: ModuleType, tmp_path: Path
) -> None:
    source = tmp_path / "backup.sql"
    destination = tmp_path / "backup.sql.gz"
    content = b"synthetic pg_dump bytes\x00\xff\n"
    source.write_bytes(content)
    backup_helpers._compress_file(str(source), str(destination))
    assert source.read_bytes() == content
    with gzip.open(destination, "rb") as compressed:
        assert compressed.read() == content


def test_wal_archive_preserves_relative_files(
    backup_helpers: ModuleType, tmp_path: Path
) -> None:
    source = tmp_path / "wal"
    source.mkdir()
    (source / "segment").write_bytes(b"synthetic WAL segment")
    destination = tmp_path / "wal.tar.gz"
    backup_helpers._archive_wal_directory(str(source), str(destination))
    with tarfile.open(destination, "r:gz") as archive:
        assert "wal_files/segment" in archive.getnames()
        member = archive.extractfile("wal_files/segment")
        assert member is not None
        assert member.read() == b"synthetic WAL segment"


def test_backup_requires_explicit_postgres_configuration(backup_helpers: ModuleType) -> None:
    for value in [None, ""]:
        with pytest.raises(ValueError, match="POSTGRES_HOST must be configured"):
            backup_helpers._required_postgres_setting(value, "POSTGRES_HOST")
    assert backup_helpers._required_postgres_setting("localhost", "POSTGRES_HOST") == "localhost"


@pytest.mark.asyncio
async def test_async_database_backup_offloads_compression(
    backup_helpers: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in [("POSTGRES_HOST", "localhost"), ("POSTGRES_USER", "test"), ("POSTGRES_DB", "test")]:
        monkeypatch.setattr(backup_helpers.settings, name, value)
    calls = []
    original_to_thread = asyncio.to_thread

    async def to_thread(function, *args):
        calls.append(function)
        return await original_to_thread(function, *args)

    async def subprocess(*args, **kwargs):
        assert args[0] == "pg_dump"
        assert "--no-password" in args
        path = Path(args[args.index("--file") + 1])
        path.write_bytes(b"synthetic SQL dump")

        async def communicate():
            return b"", b""

        return SimpleNamespace(returncode=0, communicate=communicate)

    monkeypatch.setattr(asyncio, "to_thread", to_thread)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", subprocess)
    manager = backup_helpers.DisasterRecoveryManager.__new__(backup_helpers.DisasterRecoveryManager)
    result = Path(await manager._create_full_database_backup())
    try:
        assert calls == [backup_helpers._compress_file]
        with gzip.open(result, "rb") as compressed:
            assert compressed.read() == b"synthetic SQL dump"
        assert not Path(str(result)[:-3]).exists()
    finally:
        result.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_totp_setup_exports_png_and_stores_matching_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import redis.asyncio

    setup_values = {}
    backup_values = {}

    class LocalRedis:
        async def setex(self, key, expiry, value):
            setup_values[key] = (expiry, value)

        async def set(self, key, value):
            backup_values[key] = value

    monkeypatch.setattr(redis.asyncio, "from_url", lambda *args, **kwargs: LocalRedis())
    name = "backend.auth.mfa"
    was_loaded = name in sys.modules
    package = importlib.import_module("backend.auth")
    previous = getattr(package, "mfa", None)
    try:
        module = importlib.import_module(name)
        result = await module.MultiFactorAuthService().setup_totp("fixture-user", "fixture@example.com")
        assert isinstance(result["secret"], str)
        assert isinstance(result["provisioning_uri"], str)
        assert isinstance(result["qr_code"], str)
        assert result["secret"] in result["provisioning_uri"]
        prefix, encoded = result["qr_code"].split(",", 1)
        assert prefix == "data:image/png;base64"
        assert base64.b64decode(encoded).startswith(b"\x89PNG\r\n\x1a\n")
        expiry, stored = setup_values["mfa:totp_setup:fixture-user"]
        assert expiry == 600
        assert json.loads(stored)["secret"] == result["secret"]
        codes = result["backup_codes"]
        assert isinstance(codes, list)
        assert len(codes) == len(set(codes)) == 10
        stored_codes = json.loads(backup_values["mfa:backup_codes:fixture-user"])["codes"]
        assert len(stored_codes) == 10
        assert all(code not in stored_codes for code in codes)
        assert all(hashlib.sha256(code.encode()).hexdigest() in stored_codes for code in codes)
        assert all(value["used"] is False for value in stored_codes.values())
    finally:
        if not was_loaded:
            sys.modules.pop(name, None)
            if previous is None:
                delattr(package, "mfa")
            else:
                package.__dict__["mfa"] = previous
