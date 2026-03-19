"""Basic API tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

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
    response = client.get("/api/reviews/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
