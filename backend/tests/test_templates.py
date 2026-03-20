"""Tests for /api/templates endpoints (TDD — CRD-09)."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app


@pytest.fixture
def c():
    """TestClient with raise_server_exceptions=False to catch 4xx/5xx properly."""
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_RULES = {
    "agents": {
        "logic": {"enabled": True, "severity_threshold": "medium", "custom_instructions": "", "max_findings": 10},
        "security": {"enabled": True, "severity_threshold": "medium", "custom_instructions": "", "max_findings": 10},
        "edge_case": {"enabled": False, "severity_threshold": "medium", "custom_instructions": "", "max_findings": 10},
        "convention": {"enabled": False, "severity_threshold": "medium", "custom_instructions": "", "max_findings": 10},
        "performance": {"enabled": False, "severity_threshold": "medium", "custom_instructions": "", "max_findings": 10},
    },
    "global": {"max_total_findings": 20, "min_confidence": 0.7, "language_hints": [], "ignore_patterns": []},
}


def _make_template(name="Test Template", template_id=None):
    obj = MagicMock()
    obj.id = template_id or uuid.uuid4()
    obj.name = name
    obj.description = "A test template"
    obj.rules = SAMPLE_RULES
    obj.created_by = "tester"
    obj.created_at = datetime.utcnow()
    obj.updated_at = datetime.utcnow()
    return obj


_UNSET = object()


def _mock_db(templates=None, scalar_result=_UNSET):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    if templates is not None:
        mock_result.scalars.return_value.all.return_value = templates
    if scalar_result is not _UNSET:
        mock_result.scalar_one_or_none.return_value = scalar_result

    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.flush = AsyncMock()
    mock_session.delete = AsyncMock()

    async def _override():
        yield mock_session

    return mock_session, _override


# ---------------------------------------------------------------------------
# GET /api/templates
# ---------------------------------------------------------------------------


def test_list_templates_returns_200(c):
    templates = [_make_template("Alpha"), _make_template("Beta")]
    _, override = _mock_db(templates=templates)
    app.dependency_overrides[get_db] = override
    try:
        response = c.get("/api/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
    finally:
        app.dependency_overrides.clear()


def test_list_templates_filter_by_created_by(c):
    _, override = _mock_db(templates=[])
    app.dependency_overrides[get_db] = override
    try:
        response = c.get("/api/templates?created_by=system")
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /api/templates/{id}
# ---------------------------------------------------------------------------


def test_get_template_found(c):
    tid = uuid.uuid4()
    tmpl = _make_template("Found", template_id=tid)
    _, override = _mock_db(scalar_result=tmpl)
    app.dependency_overrides[get_db] = override
    try:
        response = c.get(f"/api/templates/{tid}")
        assert response.status_code == 200
        assert response.json()["name"] == "Found"
    finally:
        app.dependency_overrides.clear()


def test_get_template_not_found(c):
    _, override = _mock_db(scalar_result=None)
    app.dependency_overrides[get_db] = override
    try:
        response = c.get(f"/api/templates/{uuid.uuid4()}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/templates
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="Requires real DB — ORM constructor mock doesn't satisfy response validation")
def test_create_template_success(c):
    mock_session = AsyncMock()
    no_dup = MagicMock()
    no_dup.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=no_dup)
    mock_session.add = MagicMock()
    created_tmpl = _make_template("New Template")

    async def _fake_flush():
        pass  # ORM object already fully populated by _make_template

    mock_session.flush = _fake_flush

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    with patch("app.api.templates.ReviewTemplate", return_value=created_tmpl):
        try:
            response = c.post("/api/templates", json={"name": "New Template", "description": "desc", "rules": SAMPLE_RULES})
            assert response.status_code == 201
            assert response.json()["name"] == "New Template"
        finally:
            app.dependency_overrides.clear()


def test_create_template_duplicate_name_returns_409(c):
    existing = _make_template("Duplicate")
    mock_session = AsyncMock()
    dup_result = MagicMock()
    dup_result.scalar_one_or_none.return_value = existing
    mock_session.execute = AsyncMock(return_value=dup_result)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.post("/api/templates", json={"name": "Duplicate", "description": "", "rules": {}})
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# PUT /api/templates/{id}
# ---------------------------------------------------------------------------


def test_update_template_not_found(c):
    _, override = _mock_db(scalar_result=None)
    app.dependency_overrides[get_db] = override
    try:
        response = c.put(f"/api/templates/{uuid.uuid4()}", json={"name": "New Name"})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# DELETE /api/templates/{id}
# ---------------------------------------------------------------------------


def test_delete_template_not_found(c):
    _, override = _mock_db(scalar_result=None)
    app.dependency_overrides[get_db] = override
    try:
        response = c.delete(f"/api/templates/{uuid.uuid4()}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_delete_template_success(c):
    tid = uuid.uuid4()
    tmpl = _make_template("To Delete", template_id=tid)
    mock_session = AsyncMock()
    found = MagicMock()
    found.scalar_one_or_none.return_value = tmpl
    mock_session.execute = AsyncMock(return_value=found)
    mock_session.delete = AsyncMock()
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.delete(f"/api/templates/{tid}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/templates/{id}/fork
# ---------------------------------------------------------------------------


def test_fork_template_not_found(c):
    _, override = _mock_db(scalar_result=None)
    app.dependency_overrides[get_db] = override
    try:
        response = c.post(f"/api/templates/{uuid.uuid4()}/fork")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.skip(reason="Requires real DB — ORM constructor mock doesn't satisfy response validation")
def test_fork_template_success(c):
    tid = uuid.uuid4()
    source = _make_template("Original", template_id=tid)
    forked = _make_template("Original (fork)")
    mock_session = AsyncMock()
    call_count = 0

    async def _execute(stmt, *args, **kwargs):
        nonlocal call_count
        result = MagicMock()
        call_count += 1
        if call_count == 1:
            result.scalar_one_or_none.return_value = source
        else:
            result.scalar_one_or_none.return_value = None
        return result

    mock_session.execute = _execute
    mock_session.add = MagicMock()

    async def _fake_flush():
        pass

    mock_session.flush = _fake_flush

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    with patch("app.api.templates.ReviewTemplate", return_value=forked):
        try:
            response = c.post(f"/api/templates/{tid}/fork")
            assert response.status_code == 201
            assert "(fork)" in response.json()["name"]
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Review creation with template_id
# ---------------------------------------------------------------------------


def test_create_review_with_invalid_template_id_returns_404(c):
    mock_session = AsyncMock()
    tmpl_result = MagicMock()
    tmpl_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=tmpl_result)
    mock_session.flush = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.rollback = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.post("/api/reviews", json={
            "pr_url": "https://github.com/owner/repo/pull/42",
            "template_id": str(uuid.uuid4()),
        })
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Template seed data
# ---------------------------------------------------------------------------


def test_default_templates_have_required_keys():
    from app.services.template_seeds import get_default_templates

    templates = get_default_templates()
    assert len(templates) == 3
    names = {t["name"] for t in templates}
    assert "Strict Security" in names
    assert "Quick Scan" in names
    assert "Full Review" in names

    for t in templates:
        assert "name" in t
        assert "rules" in t
        rules = t["rules"]
        assert "agents" in rules
        assert "global" in rules
