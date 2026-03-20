"""TDD tests for /api/memory endpoints and memory_service (v2.0 — Memory Palace)."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def c():
    return TestClient(app, raise_server_exceptions=False)


def _make_memory(
    agent_role="logic",
    memory_type="pattern",
    memory_id=None,
    relevance_score=1.0,
):
    obj = MagicMock()
    obj.id = memory_id or uuid.uuid4()
    obj.agent_role = agent_role
    obj.memory_type = memory_type
    obj.content = {"key": "value"}
    obj.source_review_id = None
    obj.relevance_score = relevance_score
    obj.access_count = 0
    obj.created_at = datetime.utcnow()
    obj.last_accessed_at = datetime.utcnow()
    return obj


def _mock_db(memories=None, scalar_result=object()):
    _UNSET = object()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    if memories is not None:
        mock_result.scalars.return_value.all.return_value = memories
    # Use a sentinel to distinguish "not provided" from None
    if scalar_result is not object():
        mock_result.scalar_one_or_none.return_value = scalar_result

    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.flush = AsyncMock()
    mock_session.delete = AsyncMock()
    mock_session.scalar = AsyncMock(return_value=0)

    async def _override():
        yield mock_session

    return mock_session, _override


# ---------------------------------------------------------------------------
# GET /api/memory
# ---------------------------------------------------------------------------


def test_list_memories_returns_200(c):
    mems = [_make_memory("logic"), _make_memory("security")]
    mock_session = AsyncMock()
    list_result = MagicMock()
    list_result.scalars.return_value.all.return_value = mems
    mock_session.execute = AsyncMock(return_value=list_result)
    mock_session.scalar = AsyncMock(return_value=2)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.get("/api/memory")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
    finally:
        app.dependency_overrides.clear()


def test_list_memories_filter_by_agent_role(c):
    mock_session = AsyncMock()
    filtered_result = MagicMock()
    filtered_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=filtered_result)
    mock_session.scalar = AsyncMock(return_value=0)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.get("/api/memory?agent_role=security")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /api/memory/{id}
# ---------------------------------------------------------------------------


def test_get_memory_found(c):
    mid = uuid.uuid4()
    mem = _make_memory(memory_id=mid)
    mock_session = AsyncMock()
    found = MagicMock()
    found.scalar_one_or_none.return_value = mem
    mock_session.execute = AsyncMock(return_value=found)
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.get(f"/api/memory/{mid}")
        assert resp.status_code == 200
        assert resp.json()["agent_role"] == "logic"
    finally:
        app.dependency_overrides.clear()


def test_get_memory_not_found(c):
    mock_session = AsyncMock()
    not_found = MagicMock()
    not_found.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=not_found)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.get(f"/api/memory/{uuid.uuid4()}")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/memory
# ---------------------------------------------------------------------------


def test_create_memory_missing_required_fields(c):
    # No db mock needed — Pydantic rejects before hitting the route.
    resp = c.post("/api/memory", json={"agent_role": "logic"})  # missing memory_type
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/memory/{id}
# ---------------------------------------------------------------------------


def test_delete_memory_not_found(c):
    mock_session = AsyncMock()
    not_found = MagicMock()
    not_found.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=not_found)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.delete(f"/api/memory/{uuid.uuid4()}")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_delete_memory_success(c):
    mid = uuid.uuid4()
    mem = _make_memory(memory_id=mid)
    mock_session = AsyncMock()
    found = MagicMock()
    found.scalar_one_or_none.return_value = mem
    mock_session.execute = AsyncMock(return_value=found)
    mock_session.delete = AsyncMock()
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.delete(f"/api/memory/{mid}")
        assert resp.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/memory/consolidate
# ---------------------------------------------------------------------------


def test_consolidate_requires_agent_role(c):
    resp = c.post("/api/memory/consolidate", json={})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# memory_service unit tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_store_memory_unit():
    """store_memory adds to session and flushes."""
    from app.services.memory_service import store_memory

    db = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()

    # Minimal call — flush is invoked.
    mem = await store_memory(db, "logic", "pattern", {"k": "v"})
    db.add.assert_called_once()
    db.flush.assert_called_once()
    assert mem.agent_role == "logic"


@pytest.mark.asyncio
async def test_decay_memories_unit():
    """decay_memories executes an UPDATE and returns rowcount."""
    from app.services.memory_service import decay_memories

    db = AsyncMock()
    update_result = MagicMock()
    update_result.rowcount = 3
    db.execute = AsyncMock(return_value=update_result)
    db.flush = AsyncMock()

    count = await decay_memories(db)
    assert count == 3
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_consolidate_memories_unit():
    """consolidate_memories processes no memories gracefully."""
    from app.services.memory_service import consolidate_memories

    db = AsyncMock()
    empty_result = MagicMock()
    empty_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=empty_result)
    db.flush = AsyncMock()

    summary = await consolidate_memories(db, "logic")
    assert summary["agent_role"] == "logic"
    assert summary["merged"] == 0
    assert summary["deleted"] == 0
    assert summary["remaining"] == 0
