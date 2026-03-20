"""TDD tests for /api/marketplace endpoints (v2.0 — Marketplace)."""

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


def _make_listing(
    title="Awesome Template",
    listing_type="template",
    listing_id=None,
    is_published=True,
    downloads=0,
    rating=0.0,
    rating_count=0,
):
    obj = MagicMock()
    obj.id = listing_id or uuid.uuid4()
    obj.listing_type = listing_type
    obj.title = title
    obj.description = "A great listing"
    obj.author = "alice"
    obj.version = "1.0.0"
    obj.config = {"agents": []}
    obj.tags = ["security", "python"]
    obj.downloads = downloads
    obj.rating = rating
    obj.rating_count = rating_count
    obj.is_published = is_published
    obj.created_at = datetime.utcnow()
    obj.updated_at = datetime.utcnow()
    return obj


def _mock_db_with_listings(listings=None, scalar_result=None, scalar_count=0):
    mock_session = AsyncMock()
    list_result = MagicMock()
    if listings is not None:
        list_result.scalars.return_value.all.return_value = listings
    if scalar_result is not None:
        list_result.scalar_one_or_none.return_value = scalar_result
    mock_session.execute = AsyncMock(return_value=list_result)
    mock_session.scalar = AsyncMock(return_value=scalar_count)
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    return mock_session, _override


# ---------------------------------------------------------------------------
# GET /api/marketplace
# ---------------------------------------------------------------------------


def test_browse_marketplace_200(c):
    listings = [_make_listing(), _make_listing("Another")]
    mock_session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = listings
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.scalar = AsyncMock(return_value=2)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.get("/api/marketplace")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
    finally:
        app.dependency_overrides.clear()


def test_browse_marketplace_invalid_sort(c):
    resp = c.get("/api/marketplace?sort=invalid_field")
    assert resp.status_code == 400


def test_browse_marketplace_filter_by_type(c):
    mock_session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=result)
    mock_session.scalar = AsyncMock(return_value=0)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.get("/api/marketplace?listing_type=org")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /api/marketplace/{id}
# ---------------------------------------------------------------------------


def test_get_listing_found(c):
    lid = uuid.uuid4()
    listing = _make_listing(listing_id=lid)
    mock_session = AsyncMock()
    found = MagicMock()
    found.scalar_one_or_none.return_value = listing
    mock_session.execute = AsyncMock(return_value=found)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.get(f"/api/marketplace/{lid}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Awesome Template"
    finally:
        app.dependency_overrides.clear()


def test_get_listing_not_found(c):
    mock_session = AsyncMock()
    not_found = MagicMock()
    not_found.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=not_found)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.get(f"/api/marketplace/{uuid.uuid4()}")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/marketplace
# ---------------------------------------------------------------------------


def test_publish_listing_missing_required_fields(c):
    resp = c.post("/api/marketplace", json={"listing_type": "template"})  # missing title
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/marketplace/{id}
# ---------------------------------------------------------------------------


def test_update_listing_not_found(c):
    mock_session = AsyncMock()
    not_found = MagicMock()
    not_found.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=not_found)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.put(f"/api/marketplace/{uuid.uuid4()}", json={"title": "New"})
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/marketplace/{id}/install
# ---------------------------------------------------------------------------


def test_install_listing_not_found(c):
    mock_session = AsyncMock()
    not_found = MagicMock()
    not_found.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=not_found)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.post(f"/api/marketplace/{uuid.uuid4()}/install")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_install_listing_unpublished_400(c):
    lid = uuid.uuid4()
    listing = _make_listing(listing_id=lid, is_published=False)
    mock_session = AsyncMock()
    found = MagicMock()
    found.scalar_one_or_none.return_value = listing
    mock_session.execute = AsyncMock(return_value=found)
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.post(f"/api/marketplace/{lid}/install")
        assert resp.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_install_listing_success_increments_downloads(c):
    lid = uuid.uuid4()
    listing = _make_listing(listing_id=lid, downloads=5)
    mock_session = AsyncMock()
    found = MagicMock()
    found.scalar_one_or_none.return_value = listing
    mock_session.execute = AsyncMock(return_value=found)
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.post(f"/api/marketplace/{lid}/install")
        assert resp.status_code == 200
        data = resp.json()
        assert data["listing_id"] == str(lid)
        assert "installed_config" in data
        # Verify the listing's downloads was incremented in-memory.
        assert listing.downloads == 6
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/marketplace/{id}/rate
# ---------------------------------------------------------------------------


def test_rate_listing_invalid_star_value(c):
    resp = c.post(f"/api/marketplace/{uuid.uuid4()}/rate", json={"rating": 6})
    assert resp.status_code == 422


def test_rate_listing_not_found(c):
    mock_session = AsyncMock()
    not_found = MagicMock()
    not_found.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=not_found)

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.post(f"/api/marketplace/{uuid.uuid4()}/rate", json={"rating": 4})
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_rate_listing_rolling_average(c):
    lid = uuid.uuid4()
    # Start with existing rating of 3.0 from 2 ratings.
    listing = _make_listing(listing_id=lid, rating=3.0, rating_count=2)
    mock_session = AsyncMock()
    found = MagicMock()
    found.scalar_one_or_none.return_value = listing
    mock_session.execute = AsyncMock(return_value=found)
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override
    try:
        resp = c.post(f"/api/marketplace/{lid}/rate", json={"rating": 5})
        assert resp.status_code == 200
        data = resp.json()
        # Expected: (3.0 * 2 + 5) / 3 = 11/3 ≈ 3.67
        assert data["rating_count"] == 3
        assert abs(data["new_rating"] - 11 / 3) < 0.01
    finally:
        app.dependency_overrides.clear()
