"""Tests for Historical Replay (CRD-08): ReviewEvent model, schema, and timeline endpoint."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.models import ReviewEvent
from app.schemas.review import ReviewEventResponse

client = TestClient(app)


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_review_event_response_schema():
    """ReviewEventResponse should serialize correctly from ORM-like data."""
    event_id = uuid.uuid4()
    now = datetime.utcnow()

    obj = ReviewEventResponse(
        id=event_id,
        event_type="review:started",
        event_data={"review_id": "abc"},
        timestamp=now,
    )
    assert obj.event_type == "review:started"
    assert obj.event_data == {"review_id": "abc"}
    assert obj.timestamp == now


def test_review_event_response_from_attributes():
    """ReviewEventResponse.model_config includes from_attributes=True."""
    config = ReviewEventResponse.model_config
    assert config.get("from_attributes") is True


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


def test_review_event_model_has_correct_tablename():
    assert ReviewEvent.__tablename__ == "review_events"


def test_review_event_model_columns():
    columns = {col.key for col in ReviewEvent.__table__.columns}
    assert "id" in columns
    assert "review_id" in columns
    assert "event_type" in columns
    assert "event_data" in columns
    assert "timestamp" in columns


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


def _make_mock_db(return_events=None):
    """Build a mock async DB session that returns `return_events` for scalars().all()."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = return_events or []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def _fake_get_db():
        yield mock_session

    return _fake_get_db


def test_get_review_timeline_returns_empty_list():
    """GET /api/reviews/{id}/timeline returns [] when no events exist."""
    app.dependency_overrides[get_db] = _make_mock_db([])
    try:
        response = client.get(f"/api/reviews/{uuid.uuid4()}/timeline")
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.clear()


def test_get_review_timeline_returns_events_in_order():
    """GET /api/reviews/{id}/timeline returns events in the order provided by the DB."""
    review_id = uuid.uuid4()
    now = datetime.utcnow()

    event1 = MagicMock(spec=ReviewEvent)
    event1.id = uuid.uuid4()
    event1.event_type = "review:started"
    event1.event_data = {"review_id": str(review_id)}
    event1.timestamp = now

    event2 = MagicMock(spec=ReviewEvent)
    event2.id = uuid.uuid4()
    event2.event_type = "review:agent:started"
    event2.event_data = {"agent": "logic"}
    event2.timestamp = now

    app.dependency_overrides[get_db] = _make_mock_db([event1, event2])
    try:
        response = client.get(f"/api/reviews/{review_id}/timeline")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["event_type"] == "review:started"
        assert data[1]["event_type"] == "review:agent:started"
        assert data[1]["event_data"] == {"agent": "logic"}
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# save_review_event tests
# ---------------------------------------------------------------------------


def test_save_review_event_creates_db_record():
    """save_review_event commits a ReviewEvent to the database."""
    from app.tasks.review_task import save_review_event

    review_id = str(uuid.uuid4())
    with patch("app.tasks.review_task.Session") as MockSession:
        mock_db = MagicMock()
        MockSession.return_value.__enter__ = MagicMock(return_value=mock_db)
        MockSession.return_value.__exit__ = MagicMock(return_value=False)

        save_review_event(review_id, "review:started", {"review_id": review_id})

        mock_db.add.assert_called_once()
        added = mock_db.add.call_args[0][0]
        assert isinstance(added, ReviewEvent)
        assert added.event_type == "review:started"
        assert added.event_data == {"review_id": review_id}
        mock_db.commit.assert_called_once()


def test_publish_ws_event_also_saves_to_db():
    """publish_ws_event should call save_review_event for every event."""
    from app.tasks.review_task import publish_ws_event

    review_id = str(uuid.uuid4())
    with patch("app.tasks.review_task.redis_client") as mock_redis, \
         patch("app.tasks.review_task.save_review_event") as mock_save:
        mock_redis.publish = MagicMock()
        publish_ws_event(review_id, "review:started", {"review_id": review_id})

        mock_redis.publish.assert_called_once()
        mock_save.assert_called_once_with(
            review_id, "review:started", {"review_id": review_id}
        )
