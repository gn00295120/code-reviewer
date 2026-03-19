"""Basic API tests."""

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "swarmforge"


def test_create_review_invalid_url():
    response = client.post("/api/reviews", json={"pr_url": "not-a-url"})
    assert response.status_code == 400


def test_get_review_not_found():
    """GET /api/reviews/<uuid> returns 404 when record doesn't exist (mocked DB)."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def _fake_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        response = client.get("/api/reviews/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
