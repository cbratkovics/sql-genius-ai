"""Regression coverage for the database dependency's acquisition/yield boundary."""

from dataclasses import dataclass

import pytest
from sqlalchemy.exc import SQLAlchemyError

from backend.core import database


@dataclass
class FakeSession:
    connection_error: SQLAlchemyError | None = None
    connections: int = 0
    closes: int = 0

    async def connection(self) -> None:
        self.connections += 1
        if self.connection_error is not None:
            raise self.connection_error

    async def close(self) -> None:
        self.closes += 1


@pytest.mark.asyncio
@pytest.mark.parametrize("application_error", [ValueError("application failure"), SQLAlchemyError("query failure")])
async def test_get_db_propagates_application_errors_without_retry(monkeypatch, application_error):
    session = FakeSession()
    acquisitions = []

    def factory():
        acquisitions.append(session)
        return session

    async def unexpected_sleep(delay):
        pytest.fail("Application failures must not trigger a connection retry")

    monkeypatch.setattr(database, "AsyncSessionLocal", factory)
    monkeypatch.setattr(database.asyncio, "sleep", unexpected_sleep)
    dependency = database.get_db()
    assert await anext(dependency) is session

    with pytest.raises(type(application_error), match=str(application_error)):
        await dependency.athrow(application_error)

    assert acquisitions == [session]
    assert session.connections == 1
    assert session.closes == 1
    with pytest.raises(StopAsyncIteration):
        await anext(dependency)


@pytest.mark.asyncio
async def test_get_db_retries_acquisition_then_yields_once(monkeypatch):
    failed = FakeSession(SQLAlchemyError("connection unavailable"))
    ready = FakeSession()
    pending = iter([failed, ready])
    acquisitions = []
    delays = []

    def factory():
        session = next(pending)
        acquisitions.append(session)
        return session

    async def sleep(delay):
        delays.append(delay)

    monkeypatch.setattr(database, "AsyncSessionLocal", factory)
    monkeypatch.setattr(database.asyncio, "sleep", sleep)
    dependency = database.get_db()
    assert await anext(dependency) is ready
    assert acquisitions == [failed, ready]
    assert failed.connections == failed.closes == 1
    assert ready.connections == 1
    assert ready.closes == 0
    assert delays == [1]

    with pytest.raises(StopAsyncIteration):
        await anext(dependency)
    assert ready.closes == 1


@pytest.mark.asyncio
async def test_get_db_exhausts_acquisition_retries_and_closes_each_session(monkeypatch):
    sessions = [FakeSession(SQLAlchemyError("connection unavailable")) for _ in range(3)]
    pending = iter(sessions)
    delays = []

    async def sleep(delay):
        delays.append(delay)

    monkeypatch.setattr(database, "AsyncSessionLocal", lambda: next(pending))
    monkeypatch.setattr(database.asyncio, "sleep", sleep)
    dependency = database.get_db()
    with pytest.raises(SQLAlchemyError, match="connection unavailable"):
        await anext(dependency)

    assert delays == [1, 2]
    assert all(session.connections == session.closes == 1 for session in sessions)
