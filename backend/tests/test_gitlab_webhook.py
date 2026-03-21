"""Tests for the GitLab webhook endpoint (/api/webhooks/gitlab)."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------------


def _make_mock_db():
    """Return a mock async DB session and the dependency override callable."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()

    async def _override():
        yield mock_session

    return mock_session, _override


def _gitlab_mr_payload(action="open", mr_iid=99, project_path="myorg/myrepo"):
    """Build a minimal GitLab Merge Request Hook payload."""
    return {
        "object_kind": "merge_request",
        "project": {
            "id": 1,
            "name": "myrepo",
            "path_with_namespace": project_path,
        },
        "object_attributes": {
            "iid": mr_iid,
            "action": action,
            "url": f"https://gitlab.com/{project_path}/-/merge_requests/{mr_iid}",
            "title": "Fix critical bug",
            "source_branch": "fix-bug",
            "target_branch": "main",
            "state": "opened",
        },
    }


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------


def test_valid_token_accepted():
    """A request with the correct X-Gitlab-Token header is accepted (not 401)."""
    mock_session, override = _make_mock_db()
    app.dependency_overrides[get_db] = override

    with patch("app.api.webhooks.settings") as mock_settings, \
         patch("app.api.webhooks.run_review_task") as mock_task:
        mock_settings.gitlab_webhook_secret = "my-secret"
        mock_task.delay = MagicMock()

        try:
            response = client.post(
                "/api/webhooks/gitlab",
                content=json.dumps(_gitlab_mr_payload()).encode(),
                headers={
                    "X-Gitlab-Token": "my-secret",
                    "X-Gitlab-Event": "Merge Request Hook",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


def test_invalid_token_returns_401():
    """A request with a wrong X-Gitlab-Token is rejected with 401."""
    mock_session, override = _make_mock_db()
    app.dependency_overrides[get_db] = override

    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.gitlab_webhook_secret = "correct-secret"

        try:
            response = client.post(
                "/api/webhooks/gitlab",
                content=json.dumps(_gitlab_mr_payload()).encode(),
                headers={
                    "X-Gitlab-Token": "wrong-secret",
                    "X-Gitlab-Event": "Merge Request Hook",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 401
            assert "Invalid GitLab webhook token" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


def test_missing_token_when_secret_configured_returns_401():
    """A request with no X-Gitlab-Token header is rejected when secret is configured."""
    mock_session, override = _make_mock_db()
    app.dependency_overrides[get_db] = override

    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.gitlab_webhook_secret = "required-secret"

        try:
            response = client.post(
                "/api/webhooks/gitlab",
                content=json.dumps(_gitlab_mr_payload()).encode(),
                headers={
                    "X-Gitlab-Event": "Merge Request Hook",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Event type filtering
# ---------------------------------------------------------------------------


def test_non_mr_event_is_ignored():
    """A Push Hook or other non-MR event returns status='ignored'."""
    mock_session, override = _make_mock_db()
    app.dependency_overrides[get_db] = override

    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.gitlab_webhook_secret = ""  # No secret — skip verification

        try:
            response = client.post(
                "/api/webhooks/gitlab",
                content=json.dumps({"object_kind": "push"}).encode(),
                headers={
                    "X-Gitlab-Event": "Push Hook",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ignored"
            assert "Push Hook" in data["reason"]
        finally:
            app.dependency_overrides.clear()


def test_note_hook_is_ignored():
    """A Note Hook event returns status='ignored'."""
    mock_session, override = _make_mock_db()
    app.dependency_overrides[get_db] = override

    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.gitlab_webhook_secret = ""

        try:
            response = client.post(
                "/api/webhooks/gitlab",
                content=json.dumps({"object_kind": "note"}).encode(),
                headers={
                    "X-Gitlab-Event": "Note Hook",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 200
            assert response.json()["status"] == "ignored"
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Action filtering
# ---------------------------------------------------------------------------


def test_ignored_action_close_returns_ignored():
    """An MR with action='close' is ignored and no review is queued."""
    mock_session, override = _make_mock_db()
    app.dependency_overrides[get_db] = override

    with patch("app.api.webhooks.settings") as mock_settings, \
         patch("app.api.webhooks.run_review_task") as mock_task:
        mock_settings.gitlab_webhook_secret = ""
        mock_task.delay = MagicMock()

        try:
            response = client.post(
                "/api/webhooks/gitlab",
                content=json.dumps(_gitlab_mr_payload(action="close")).encode(),
                headers={
                    "X-Gitlab-Event": "Merge Request Hook",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ignored"
            assert "close" in data["reason"]
            mock_task.delay.assert_not_called()
        finally:
            app.dependency_overrides.clear()


def test_ignored_action_merge_returns_ignored():
    """An MR with action='merge' is ignored and no review is queued."""
    mock_session, override = _make_mock_db()
    app.dependency_overrides[get_db] = override

    with patch("app.api.webhooks.settings") as mock_settings, \
         patch("app.api.webhooks.run_review_task") as mock_task:
        mock_settings.gitlab_webhook_secret = ""
        mock_task.delay = MagicMock()

        try:
            response = client.post(
                "/api/webhooks/gitlab",
                content=json.dumps(_gitlab_mr_payload(action="merge")).encode(),
                headers={
                    "X-Gitlab-Event": "Merge Request Hook",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 200
            assert response.json()["status"] == "ignored"
            mock_task.delay.assert_not_called()
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Successful MR open queues a review
# ---------------------------------------------------------------------------


def test_mr_open_queues_review():
    """A valid MR open event creates a CodeReview record and queues a Celery task."""
    mock_session, override = _make_mock_db()
    app.dependency_overrides[get_db] = override

    with patch("app.api.webhooks.settings") as mock_settings, \
         patch("app.api.webhooks.run_review_task") as mock_task, \
         patch("app.api.webhooks.CodeReview") as MockCodeReview:
        mock_settings.gitlab_webhook_secret = ""
        mock_task.delay = MagicMock()

        fake_review = MagicMock()
        fake_review.id = uuid.uuid4()
        MockCodeReview.return_value = fake_review

        try:
            response = client.post(
                "/api/webhooks/gitlab",
                content=json.dumps(_gitlab_mr_payload(action="open", mr_iid=5)).encode(),
                headers={
                    "X-Gitlab-Event": "Merge Request Hook",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"
            assert "review_id" in data

            # Verify CodeReview was constructed with the right platform
            MockCodeReview.assert_called_once()
            init_kwargs = MockCodeReview.call_args[1]
            assert init_kwargs["platform"] == "gitlab"
            assert init_kwargs["pr_number"] == 5
            assert init_kwargs["status"] == "pending"

            # Verify the Celery task was dispatched
            mock_task.delay.assert_called_once_with(str(fake_review.id))
        finally:
            app.dependency_overrides.clear()


def test_mr_update_queues_review():
    """An MR with action='update' also queues a review (synchronize-equivalent)."""
    mock_session, override = _make_mock_db()
    app.dependency_overrides[get_db] = override

    with patch("app.api.webhooks.settings") as mock_settings, \
         patch("app.api.webhooks.run_review_task") as mock_task, \
         patch("app.api.webhooks.CodeReview") as MockCodeReview:
        mock_settings.gitlab_webhook_secret = ""
        mock_task.delay = MagicMock()

        fake_review = MagicMock()
        fake_review.id = uuid.uuid4()
        MockCodeReview.return_value = fake_review

        try:
            response = client.post(
                "/api/webhooks/gitlab",
                content=json.dumps(_gitlab_mr_payload(action="update")).encode(),
                headers={
                    "X-Gitlab-Event": "Merge Request Hook",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 200
            assert response.json()["status"] == "queued"
            mock_task.delay.assert_called_once()
        finally:
            app.dependency_overrides.clear()


def test_mr_reopen_queues_review():
    """An MR with action='reopen' queues a review."""
    mock_session, override = _make_mock_db()
    app.dependency_overrides[get_db] = override

    with patch("app.api.webhooks.settings") as mock_settings, \
         patch("app.api.webhooks.run_review_task") as mock_task, \
         patch("app.api.webhooks.CodeReview") as MockCodeReview:
        mock_settings.gitlab_webhook_secret = ""
        mock_task.delay = MagicMock()

        fake_review = MagicMock()
        fake_review.id = uuid.uuid4()
        MockCodeReview.return_value = fake_review

        try:
            response = client.post(
                "/api/webhooks/gitlab",
                content=json.dumps(_gitlab_mr_payload(action="reopen")).encode(),
                headers={
                    "X-Gitlab-Event": "Merge Request Hook",
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 200
            assert response.json()["status"] == "queued"
            mock_task.delay.assert_called_once()
        finally:
            app.dependency_overrides.clear()
