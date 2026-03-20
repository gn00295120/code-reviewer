"""Tests for org deploy and org-templates APIs."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_org(org_id=None, **kwargs):
    """Return a MagicMock resembling an AgentOrg ORM row."""
    org = MagicMock()
    org.id = org_id or uuid4()
    org.name = kwargs.get("name", "Test Org")
    org.description = kwargs.get("description", "desc")
    org.topology = kwargs.get("topology", {
        "agents": [
            {"role": "planner", "description": "Plans things", "connects_to": ["executor"]},
            {"role": "executor", "description": "Executes things", "connects_to": []},
        ]
    })
    org.config = kwargs.get("config", {"default_model": "gpt-4o"})
    org.is_template = kwargs.get("is_template", False)
    org.fork_count = kwargs.get("fork_count", 0)
    org.forked_from_id = None
    org.created_at = "2024-01-01T00:00:00"
    org.updated_at = "2024-01-01T00:00:00"
    return org


def _mock_db_returning(org_or_none):
    """Return an async generator that yields a mock session finding `org_or_none`."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = org_or_none
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    async def _fake_get_db():
        yield mock_session

    return _fake_get_db


# ===========================================================================
# Org Templates API
# ===========================================================================


def test_list_org_templates():
    """GET /api/org-templates returns all seed templates."""
    response = client.get("/api/org-templates")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 7  # 3 original + 4 new
    names = [t["name"] for t in data]
    assert "AutoResearch Team" in names
    assert "Code Review Team" in names
    assert "Science Discovery Team" in names
    assert "DevOps Pipeline" in names
    assert "Content Creation" in names
    assert "Customer Support" in names
    assert "Data Pipeline" in names


def test_list_org_templates_structure():
    """Each template has required fields."""
    response = client.get("/api/org-templates")
    data = response.json()
    for template in data:
        assert "name" in template
        assert "description" in template
        assert "topology" in template
        assert "config" in template
        assert "agents" in template["topology"]
        assert "connections" in template["topology"]
        # config fields
        assert "default_model" in template["config"]
        assert "memory_enabled" in template["config"]
        assert "max_concurrent" in template["config"]


def test_instantiate_org_template():
    """POST /api/org-templates/{name}/instantiate creates an AgentOrg."""
    new_org = _make_org(name="AutoResearch Team")
    new_org.is_template = True

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # no existing
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()

    async def _refresh(obj):
        obj.id = new_org.id
        obj.name = new_org.name
        obj.description = new_org.description
        obj.topology = new_org.topology
        obj.config = new_org.config
        obj.is_template = True
        obj.fork_count = 0
        obj.forked_from_id = None
        obj.created_at = new_org.created_at
        obj.updated_at = new_org.updated_at

    mock_session.refresh = AsyncMock(side_effect=_refresh)

    async def _fake_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.post("/api/org-templates/AutoResearch Team/instantiate")
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "AutoResearch Team"
        assert data["is_template"] is True
    finally:
        app.dependency_overrides.clear()


def test_instantiate_unknown_template_returns_404():
    """POST /api/org-templates/Unknown/instantiate returns 404."""
    response = client.post("/api/org-templates/Unknown Template XYZ/instantiate")
    assert response.status_code == 404


# ===========================================================================
# Org Deploy API
# ===========================================================================


def test_deploy_org_not_found():
    """POST /api/orgs/{id}/deploy returns 404 when org doesn't exist."""
    app.dependency_overrides[get_db] = _mock_db_returning(None)
    try:
        response = client.post(f"/api/orgs/{uuid4()}/deploy")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_deploy_org_success():
    """POST /api/orgs/{id}/deploy returns deployment record."""
    org = _make_org()
    app.dependency_overrides[get_db] = _mock_db_returning(org)
    try:
        response = client.post(f"/api/orgs/{org.id}/deploy")
        assert response.status_code == 200
        data = response.json()
        assert data["org_id"] == str(org.id)
        assert data["status"] == "running"
        assert "agents" in data
        assert len(data["agents"]) == 2  # planner + executor
        assert data["agents"][0]["role"] == "planner"
        assert data["agents"][0]["status"] == "running"
    finally:
        app.dependency_overrides.clear()


def test_get_org_status_not_found():
    """GET /api/orgs/{id}/status returns 404 when org doesn't exist."""
    app.dependency_overrides[get_db] = _mock_db_returning(None)
    try:
        response = client.get(f"/api/orgs/{uuid4()}/status")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_org_status_no_deployment():
    """GET /api/orgs/{id}/status returns idle when never deployed."""
    org = _make_org()
    app.dependency_overrides[get_db] = _mock_db_returning(org)
    try:
        response = client.get(f"/api/orgs/{org.id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["org_id"] == str(org.id)
        assert data["status"] == "idle"
    finally:
        app.dependency_overrides.clear()


def test_stop_org_not_found():
    """POST /api/orgs/{id}/stop returns 404 when org doesn't exist."""
    app.dependency_overrides[get_db] = _mock_db_returning(None)
    try:
        response = client.post(f"/api/orgs/{uuid4()}/stop")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_stop_org_success():
    """POST /api/orgs/{id}/stop returns stopped status."""
    org = _make_org()
    app.dependency_overrides[get_db] = _mock_db_returning(org)
    try:
        response = client.post(f"/api/orgs/{org.id}/stop")
        assert response.status_code == 200
        data = response.json()
        assert data["org_id"] == str(org.id)
        assert data["status"] == "stopped"
    finally:
        app.dependency_overrides.clear()
