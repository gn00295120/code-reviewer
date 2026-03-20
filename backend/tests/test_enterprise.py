"""TDD tests for /api/audit, /api/security-policies (v2.0 — Enterprise Guard)."""

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


def _make_audit_log(action="review.created", resource_type="review", log_id=None):
    obj = MagicMock()
    obj.id = log_id or uuid.uuid4()
    obj.action = action
    obj.actor = "user@example.com"
    obj.resource_type = resource_type
    obj.resource_id = uuid.uuid4()
    obj.details = {}
    obj.ip_address = "127.0.0.1"
    obj.created_at = datetime.utcnow()
    return obj


def _make_policy(name="Default Rate Limit", policy_type="rate_limit", policy_id=None):
    obj = MagicMock()
    obj.id = policy_id or uuid.uuid4()
    obj.name = name
    obj.policy_type = policy_type
    obj.config = {"window_seconds": 60, "max_calls": 100}
    obj.is_active = True
    obj.created_at = datetime.utcnow()
    obj.updated_at = datetime.utcnow()
    return obj


# ---------------------------------------------------------------------------
# GET /api/audit
# ---------------------------------------------------------------------------


def test_list_audit_logs_200(c):
    logs = [_make_audit_log(), _make_audit_log("template.forked", "template")]
    mock_session = AsyncMock()
    list_result = MagicMock()
    list_result.scalars.return_value.all.return_value = logs
    mock_session.execute = AsyncMock(return_value=list_result)
    mock_session.scalar = AsyncMock(return_value=2)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.get("/api/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
    finally:
        app.dependency_overrides.clear()


def test_list_audit_logs_filter_by_action(c):
    mock_session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.scalar = AsyncMock(return_value=0)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.get("/api/audit?action=review.created")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /api/security-policies
# ---------------------------------------------------------------------------


def test_list_security_policies_200(c):
    policies = [_make_policy()]
    mock_session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = policies
    mock_session.execute = AsyncMock(return_value=result)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.get("/api/security-policies")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 1
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/security-policies
# ---------------------------------------------------------------------------


def test_create_security_policy_duplicate_409(c):
    existing = _make_policy("Duplicate Policy")
    mock_session = AsyncMock()
    dup_result = MagicMock()
    dup_result.scalar_one_or_none.return_value = existing
    mock_session.execute = AsyncMock(return_value=dup_result)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.post(
            "/api/security-policies",
            json={
                "name": "Duplicate Policy",
                "policy_type": "rate_limit",
                "config": {},
            },
        )
        assert resp.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_create_security_policy_missing_fields(c):
    resp = c.post("/api/security-policies", json={"name": "No Type"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/security-policies/{id}
# ---------------------------------------------------------------------------


def test_update_security_policy_not_found(c):
    mock_session = AsyncMock()
    not_found = MagicMock()
    not_found.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=not_found)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.put(f"/api/security-policies/{uuid.uuid4()}", json={"name": "X"})
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/security-policies/{id}/toggle
# ---------------------------------------------------------------------------


def test_toggle_security_policy_not_found(c):
    mock_session = AsyncMock()
    not_found = MagicMock()
    not_found.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=not_found)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.post(f"/api/security-policies/{uuid.uuid4()}/toggle")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_toggle_security_policy_success(c):
    pid = uuid.uuid4()
    policy = _make_policy(policy_id=pid)
    policy.is_active = True
    mock_session = AsyncMock()
    found = MagicMock()
    found.scalar_one_or_none.return_value = policy
    mock_session.execute = AsyncMock(return_value=found)
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.post(f"/api/security-policies/{pid}/toggle")
        assert resp.status_code == 200
        data = resp.json()
        assert "is_active" in data
        assert "message" in data
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# guard_service unit tests
# ---------------------------------------------------------------------------


def test_detect_secrets_finds_api_key():
    from app.services.guard_service import detect_secrets

    content = 'API_KEY = "sk-12345678abcdefgh"'
    findings = detect_secrets(content)
    assert len(findings) > 0


def test_detect_secrets_clean_content():
    from app.services.guard_service import detect_secrets

    content = "x = 1 + 2\nprint(x)"
    findings = detect_secrets(content)
    assert len(findings) == 0


def test_detect_secrets_aws_key():
    from app.services.guard_service import detect_secrets

    content = "key = AKIAIOSFODNN7EXAMPLE"
    findings = detect_secrets(content)
    # AWS key pattern is in the list
    assert any("AKIA" in f["match"] or "****" in f["match"] for f in findings)


@pytest.mark.asyncio
async def test_log_audit_unit():
    from app.services.guard_service import log_audit

    db = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()

    entry = await log_audit(db, "review.created", "review", actor="alice")
    db.add.assert_called_once()
    db.flush.assert_called_once()
    assert entry.action == "review.created"
    assert entry.actor == "alice"


@pytest.mark.asyncio
async def test_check_rate_limit_allows_first_call():
    from app.services import guard_service

    # Clear the in-process bucket for this test.
    guard_service._rate_limit_buckets.clear()

    db = AsyncMock()
    no_policy = MagicMock()
    no_policy.scalars.return_value.first.return_value = None
    db.execute = AsyncMock(return_value=no_policy)

    result = await guard_service.check_rate_limit(db, "test_actor_unique", "test_action")
    assert result["allowed"] is True
    assert result["remaining"] >= 0
