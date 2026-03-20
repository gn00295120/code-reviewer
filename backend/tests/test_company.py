"""Tests for /api/companies endpoints — v3.0 Self-hosting Agent Company."""

import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app


@pytest.fixture
def c():
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_company(name="Acme AI", company_id=None, status="draft"):
    obj = MagicMock()
    obj.id = company_id or uuid.uuid4()
    obj.name = name
    obj.description = "Test company"
    obj.owner = "tester"
    obj.org_chart = {}
    obj.processes = []
    obj.shared_state = {}
    obj.budget_usd = Decimal("100.00")
    obj.spent_usd = Decimal("10.000000")
    obj.status = status
    obj.agent_count = 0
    obj.created_at = datetime.utcnow()
    obj.updated_at = datetime.utcnow()
    obj.agents = []
    return obj


def _make_agent(company_id, agent_id=None, role="engineer"):
    obj = MagicMock()
    obj.id = agent_id or uuid.uuid4()
    obj.company_id = company_id
    obj.role = role
    obj.title = "Senior Engineer"
    obj.model = "claude-sonnet"
    obj.system_prompt = None
    obj.capabilities = []
    obj.reports_to = None
    obj.status = "idle"
    obj.total_tasks = 0
    obj.total_cost_usd = Decimal("0.000000")
    obj.created_at = datetime.utcnow()
    return obj


def _mock_db(scalar_result=None, scalars_list=None, scalar_count=0):
    mock_session = AsyncMock()

    call_count = 0

    async def _execute(stmt, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        result.scalar_one_or_none.return_value = scalar_result
        result.scalar.return_value = scalar_count
        if scalars_list is not None:
            result.scalars.return_value.all.return_value = scalars_list
        return result

    mock_session.execute = _execute
    mock_session.flush = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.delete = AsyncMock()
    mock_session.scalar = AsyncMock(return_value=scalar_count)

    async def _override():
        yield mock_session

    return mock_session, _override


# ---------------------------------------------------------------------------
# GET /api/companies
# ---------------------------------------------------------------------------


def test_list_companies_returns_200(c):
    companies = [_make_company("Alpha"), _make_company("Beta")]
    mock_session = AsyncMock()

    call_count = 0

    async def _execute(stmt, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            result.scalar.return_value = 2
        else:
            result.scalars.return_value.all.return_value = companies
        return result

    mock_session.execute = _execute
    mock_session.scalar = AsyncMock(return_value=2)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.get("/api/companies")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    finally:
        app.dependency_overrides.clear()


def test_list_companies_filter_by_status(c):
    mock_session = AsyncMock()

    call_count = 0

    async def _execute(stmt, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        result.scalar.return_value = 0
        result.scalars.return_value.all.return_value = []
        return result

    mock_session.execute = _execute
    mock_session.scalar = AsyncMock(return_value=0)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.get("/api/companies?status=active")
        assert response.status_code == 200
        assert response.json()["items"] == []
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /api/companies/{id}
# ---------------------------------------------------------------------------


def test_get_company_not_found(c):
    _, override = _mock_db(scalar_result=None)
    app.dependency_overrides[get_db] = override
    try:
        response = c.get(f"/api/companies/{uuid.uuid4()}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_company_found(c):
    cid = uuid.uuid4()
    company = _make_company("Found Co", company_id=cid)
    company.agents = []
    mock_session = AsyncMock()

    async def _execute(stmt, *args, **kwargs):
        result = MagicMock()
        result.scalar_one_or_none.return_value = company
        return result

    mock_session.execute = _execute

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.get(f"/api/companies/{cid}")
        assert response.status_code == 200
        assert response.json()["name"] == "Found Co"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# PUT /api/companies/{id}
# ---------------------------------------------------------------------------


def test_update_company_not_found(c):
    _, override = _mock_db(scalar_result=None)
    app.dependency_overrides[get_db] = override
    try:
        response = c.put(f"/api/companies/{uuid.uuid4()}", json={"name": "New Name"})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/companies/{id}/activate
# ---------------------------------------------------------------------------


def test_activate_company_already_active(c):
    cid = uuid.uuid4()
    company = _make_company("Active Co", company_id=cid, status="active")
    mock_session = AsyncMock()

    async def _execute(stmt, *args, **kwargs):
        result = MagicMock()
        result.scalar_one_or_none.return_value = company
        return result

    mock_session.execute = _execute
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.post(f"/api/companies/{cid}/activate")
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_activate_company_archived_returns_409(c):
    cid = uuid.uuid4()
    company = _make_company("Archived Co", company_id=cid, status="archived")
    mock_session = AsyncMock()

    async def _execute(stmt, *args, **kwargs):
        result = MagicMock()
        result.scalar_one_or_none.return_value = company
        return result

    mock_session.execute = _execute
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.post(f"/api/companies/{cid}/activate")
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_activate_company_success(c):
    cid = uuid.uuid4()
    company = _make_company("Draft Co", company_id=cid, status="draft")
    mock_session = AsyncMock()

    async def _execute(stmt, *args, **kwargs):
        result = MagicMock()
        result.scalar_one_or_none.return_value = company
        return result

    mock_session.execute = _execute
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.post(f"/api/companies/{cid}/activate")
        assert response.status_code == 200
        assert company.status == "active"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/companies/{id}/pause
# ---------------------------------------------------------------------------


def test_pause_company_not_active_returns_409(c):
    cid = uuid.uuid4()
    company = _make_company("Draft Co", company_id=cid, status="draft")
    mock_session = AsyncMock()

    async def _execute(stmt, *args, **kwargs):
        result = MagicMock()
        result.scalar_one_or_none.return_value = company
        return result

    mock_session.execute = _execute
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.post(f"/api/companies/{cid}/pause")
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_pause_company_success(c):
    cid = uuid.uuid4()
    company = _make_company("Active Co", company_id=cid, status="active")
    mock_session = AsyncMock()

    async def _execute(stmt, *args, **kwargs):
        result = MagicMock()
        result.scalar_one_or_none.return_value = company
        return result

    mock_session.execute = _execute
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.post(f"/api/companies/{cid}/pause")
        assert response.status_code == 200
        assert company.status == "paused"
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /api/companies/{id}/budget
# ---------------------------------------------------------------------------


def test_get_budget_not_found(c):
    _, override = _mock_db(scalar_result=None)
    app.dependency_overrides[get_db] = override
    try:
        response = c.get(f"/api/companies/{uuid.uuid4()}/budget")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_budget_returns_summary(c):
    cid = uuid.uuid4()
    company = _make_company("Budget Co", company_id=cid)
    company.budget_usd = Decimal("200.00")
    company.spent_usd = Decimal("50.000000")
    mock_session = AsyncMock()

    async def _execute(stmt, *args, **kwargs):
        result = MagicMock()
        result.scalar_one_or_none.return_value = company
        return result

    mock_session.execute = _execute

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.get(f"/api/companies/{cid}/budget")
        assert response.status_code == 200
        data = response.json()
        assert data["budget_usd"] == "200.00"
        assert data["spent_usd"] == "50.000000"
        assert data["remaining_usd"] == "150.000000"
        assert data["utilization_pct"] == 25.0
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /api/companies/{id}/agents
# ---------------------------------------------------------------------------


def test_list_agents_company_not_found(c):
    mock_session = AsyncMock()

    call_count = 0

    async def _execute(stmt, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        result.scalars.return_value.all.return_value = []
        return result

    mock_session.execute = _execute

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.get(f"/api/companies/{uuid.uuid4()}/agents")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_list_agents_success(c):
    cid = uuid.uuid4()
    company = _make_company(company_id=cid)
    agent = _make_agent(cid)
    mock_session = AsyncMock()

    call_count = 0

    async def _execute(stmt, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            # company lookup
            result.scalar_one_or_none.return_value = company
        else:
            # agent list
            result.scalars.return_value.all.return_value = [agent]
        return result

    mock_session.execute = _execute

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.get(f"/api/companies/{cid}/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# DELETE /api/companies/{id}/agents/{agent_id}
# ---------------------------------------------------------------------------


def test_remove_agent_not_found(c):
    cid = uuid.uuid4()
    company = _make_company(company_id=cid)
    mock_session = AsyncMock()

    call_count = 0

    async def _execute(stmt, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            result.scalar_one_or_none.return_value = company
        else:
            result.scalar_one_or_none.return_value = None
        return result

    mock_session.execute = _execute
    mock_session.flush = AsyncMock()
    mock_session.delete = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        response = c.delete(f"/api/companies/{cid}/agents/{uuid.uuid4()}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
