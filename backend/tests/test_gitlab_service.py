"""Unit tests for GitLabService (app/services/gitlab_service.py).

The python-gitlab package may not be installed in the test environment.
We mock it at the sys.modules level so the service module can be imported
and tested without the real library present.
"""

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from app.services.vcs_provider import FileDiff, PRDiff


# ---------------------------------------------------------------------------
# Module-level gitlab mock — injected before the service module is imported
# ---------------------------------------------------------------------------

def _inject_gitlab_mock():
    """Inject a minimal 'gitlab' stub into sys.modules if not already present."""
    if "gitlab" not in sys.modules:
        stub = types.ModuleType("gitlab")
        stub.Gitlab = MagicMock  # class-level mock; instances are MagicMocks
        sys.modules["gitlab"] = stub
    return sys.modules["gitlab"]


_inject_gitlab_mock()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service():
    """Return a GitLabService with settings patched to avoid env requirements.

    We start the patch, build the service, then stop the patch. The service
    captures the token/base_url in __init__, so it works correctly after
    the patch is torn down.
    """
    import app.services.gitlab_service as _mod

    patcher = patch.object(_mod, "get_settings")
    mock_settings = patcher.start()
    mock_settings.return_value.gitlab_token = "fake-token"
    mock_settings.return_value.gitlab_base_url = "https://gitlab.com"
    try:
        svc = _mod.GitLabService()
    finally:
        patcher.stop()
    return svc


# ---------------------------------------------------------------------------
# _parse_mr_url tests
# ---------------------------------------------------------------------------


def test_parse_mr_url_valid_gitlab_com():
    """_parse_mr_url correctly extracts host, project path and MR iid from gitlab.com."""
    svc = _make_service()
    base_url, project_path, mr_iid = svc._parse_mr_url(
        "https://gitlab.com/myorg/myrepo/-/merge_requests/42"
    )
    assert base_url == "https://gitlab.com"
    assert project_path == "myorg/myrepo"
    assert mr_iid == 42


def test_parse_mr_url_self_hosted_gitlab():
    """_parse_mr_url handles self-hosted GitLab instances with nested namespaces."""
    svc = _make_service()
    base_url, project_path, mr_iid = svc._parse_mr_url(
        "https://git.company.internal/team/sub-group/project/-/merge_requests/7"
    )
    assert base_url == "https://git.company.internal"
    assert project_path == "team/sub-group/project"
    assert mr_iid == 7


def test_parse_mr_url_invalid_raises_value_error():
    """_parse_mr_url raises ValueError for a URL that does not match the MR pattern."""
    svc = _make_service()
    with pytest.raises(ValueError, match="Invalid GitLab MR URL"):
        svc._parse_mr_url("https://github.com/owner/repo/pull/1")


def test_parse_mr_url_plain_url_raises_value_error():
    """_parse_mr_url raises ValueError for a completely invalid URL string."""
    svc = _make_service()
    with pytest.raises(ValueError, match="Invalid GitLab MR URL"):
        svc._parse_mr_url("not-a-url-at-all")


# ---------------------------------------------------------------------------
# _map_status tests
# ---------------------------------------------------------------------------


def _get_map_status():
    """Import _map_status after the gitlab stub is in place."""
    import app.services.gitlab_service as _mod
    return _mod._map_status


def test_map_status_new_file():
    assert _get_map_status()({"new_file": True}) == "added"


def test_map_status_deleted_file():
    assert _get_map_status()({"deleted_file": True}) == "removed"


def test_map_status_renamed_file():
    assert _get_map_status()({"renamed_file": True}) == "renamed"


def test_map_status_modified_file():
    assert _get_map_status()({}) == "modified"


def test_map_status_modified_when_no_flags_set():
    assert _get_map_status()({"new_file": False, "deleted_file": False, "renamed_file": False}) == "modified"


# ---------------------------------------------------------------------------
# fetch_pr_diff tests
# ---------------------------------------------------------------------------


def _make_mock_mr(title="Fix bug", description="Some description", target_branch="main", source_branch="fix-123"):
    mr = MagicMock()
    mr.title = title
    mr.description = description
    mr.target_branch = target_branch
    mr.source_branch = source_branch
    mr.changes.return_value = {
        "changes": [
            {
                "new_path": "app/main.py",
                "diff": "+def hello():\n+    pass\n-def old():\n-    pass",
                "new_file": False,
                "deleted_file": False,
                "renamed_file": False,
            }
        ]
    }
    return mr


def test_fetch_pr_diff_returns_prdiff_structure():
    """fetch_pr_diff builds a PRDiff from mocked python-gitlab client responses."""
    svc = _make_service()
    mock_mr = _make_mock_mr()

    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_mr

    mock_gl = MagicMock()
    mock_gl.projects.get.return_value = mock_project

    with patch.object(svc, "_get_client", return_value=mock_gl):
        result = svc.fetch_pr_diff("https://gitlab.com/myorg/myrepo/-/merge_requests/42")

    assert isinstance(result, PRDiff)
    assert result.pr_number == 42
    assert result.repo_name == "myorg/myrepo"
    assert result.title == "Fix bug"
    assert result.body == "Some description"
    assert result.base_branch == "main"
    assert result.head_branch == "fix-123"
    assert len(result.files) == 1
    assert result.files[0].filename == "app/main.py"
    assert result.files[0].status == "modified"


def test_fetch_pr_diff_counts_additions_and_deletions():
    """fetch_pr_diff correctly counts + and - lines from the diff patch."""
    svc = _make_service()
    mock_mr = MagicMock()
    mock_mr.title = "Add feature"
    mock_mr.description = ""
    mock_mr.target_branch = "main"
    mock_mr.source_branch = "feature"
    mock_mr.changes.return_value = {
        "changes": [
            {
                "new_path": "src/utils.py",
                "diff": "+++ b/src/utils.py\n--- a/src/utils.py\n+line1\n+line2\n+line3\n-removed1\n-removed2",
                "new_file": False,
                "deleted_file": False,
                "renamed_file": False,
            }
        ]
    }

    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl = MagicMock()
    mock_gl.projects.get.return_value = mock_project

    with patch.object(svc, "_get_client", return_value=mock_gl):
        result = svc.fetch_pr_diff("https://gitlab.com/myorg/myrepo/-/merge_requests/10")

    assert result.files[0].additions == 3
    assert result.files[0].deletions == 2
    assert result.total_additions == 3
    assert result.total_deletions == 2


def test_fetch_pr_diff_new_file_status():
    """fetch_pr_diff maps new_file=True to status='added'."""
    svc = _make_service()
    mock_mr = MagicMock()
    mock_mr.title = "Add new file"
    mock_mr.description = ""
    mock_mr.target_branch = "main"
    mock_mr.source_branch = "feature"
    mock_mr.changes.return_value = {
        "changes": [
            {
                "new_path": "new_file.py",
                "diff": "+new line",
                "new_file": True,
                "deleted_file": False,
                "renamed_file": False,
            }
        ]
    }

    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl = MagicMock()
    mock_gl.projects.get.return_value = mock_project

    with patch.object(svc, "_get_client", return_value=mock_gl):
        result = svc.fetch_pr_diff("https://gitlab.com/myorg/myrepo/-/merge_requests/11")

    assert result.files[0].status == "added"


# ---------------------------------------------------------------------------
# post_inline_comments tests
# ---------------------------------------------------------------------------


def _sample_finding(file_path="app/main.py", line_number=10, severity="high"):
    return {
        "severity": severity,
        "title": "SQL Injection risk",
        "description": "User input is not sanitized before query construction.",
        "suggested_fix": "Use parameterized queries.",
        "agent_role": "security",
        "confidence": 0.95,
        "file_path": file_path,
        "line_number": line_number,
    }


def test_post_inline_comments_returns_posted_count():
    """post_inline_comments returns the number of findings posted."""
    svc = _make_service()
    mock_mr = MagicMock()
    mock_mr.diff_refs = {
        "base_sha": "abc123",
        "start_sha": "def456",
        "head_sha": "ghi789",
    }
    mock_mr.discussions.create = MagicMock()
    mock_mr.notes.create = MagicMock()

    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl = MagicMock()
    mock_gl.projects.get.return_value = mock_project

    findings = [_sample_finding(), _sample_finding(file_path="app/utils.py", line_number=20)]

    with patch.object(svc, "_get_client", return_value=mock_gl):
        count = svc.post_inline_comments(
            "https://gitlab.com/myorg/myrepo/-/merge_requests/42",
            findings,
        )

    assert count == 2
    assert mock_mr.discussions.create.call_count == 2


def test_post_inline_comments_creates_summary_note():
    """post_inline_comments posts a summary note when findings are present."""
    svc = _make_service()
    mock_mr = MagicMock()
    mock_mr.diff_refs = {"base_sha": "a", "start_sha": "b", "head_sha": "c"}
    mock_mr.discussions.create = MagicMock()
    mock_mr.notes.create = MagicMock()

    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl = MagicMock()
    mock_gl.projects.get.return_value = mock_project

    with patch.object(svc, "_get_client", return_value=mock_gl):
        svc.post_inline_comments(
            "https://gitlab.com/myorg/myrepo/-/merge_requests/42",
            [_sample_finding()],
        )

    mock_mr.notes.create.assert_called_once()
    note_body = mock_mr.notes.create.call_args[0][0]["body"]
    assert "SwarmForge Code Review" in note_body


def test_post_inline_comments_includes_position_for_line_findings():
    """post_inline_comments includes position data when file_path and line_number are set."""
    svc = _make_service()
    mock_mr = MagicMock()
    mock_mr.diff_refs = {
        "base_sha": "base_sha_val",
        "start_sha": "start_sha_val",
        "head_sha": "head_sha_val",
    }
    mock_mr.discussions.create = MagicMock()
    mock_mr.notes.create = MagicMock()

    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl = MagicMock()
    mock_gl.projects.get.return_value = mock_project

    with patch.object(svc, "_get_client", return_value=mock_gl):
        svc.post_inline_comments(
            "https://gitlab.com/myorg/myrepo/-/merge_requests/42",
            [_sample_finding(file_path="src/main.py", line_number=5)],
        )

    call_kwargs = mock_mr.discussions.create.call_args[0][0]
    assert "position" in call_kwargs
    assert call_kwargs["position"]["new_path"] == "src/main.py"
    assert call_kwargs["position"]["new_line"] == 5
    assert call_kwargs["position"]["base_sha"] == "base_sha_val"


def test_post_inline_comments_no_position_when_no_line():
    """post_inline_comments omits position data when line_number is absent."""
    svc = _make_service()
    mock_mr = MagicMock()
    mock_mr.diff_refs = {"base_sha": "a", "start_sha": "b", "head_sha": "c"}
    mock_mr.discussions.create = MagicMock()
    mock_mr.notes.create = MagicMock()

    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl = MagicMock()
    mock_gl.projects.get.return_value = mock_project

    finding_no_line = {
        "severity": "low",
        "title": "Minor issue",
        "description": "No line info.",
        "agent_role": "logic",
        "confidence": 0.6,
        "file_path": None,
        "line_number": None,
    }

    with patch.object(svc, "_get_client", return_value=mock_gl):
        count = svc.post_inline_comments(
            "https://gitlab.com/myorg/myrepo/-/merge_requests/42",
            [finding_no_line],
        )

    assert count == 1
    call_kwargs = mock_mr.discussions.create.call_args[0][0]
    assert "position" not in call_kwargs


def test_post_inline_comments_empty_findings_returns_zero():
    """post_inline_comments returns 0 and posts no notes when findings list is empty."""
    svc = _make_service()
    mock_mr = MagicMock()
    mock_mr.diff_refs = {"base_sha": "a", "start_sha": "b", "head_sha": "c"}
    mock_mr.discussions.create = MagicMock()
    mock_mr.notes.create = MagicMock()

    mock_project = MagicMock()
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl = MagicMock()
    mock_gl.projects.get.return_value = mock_project

    with patch.object(svc, "_get_client", return_value=mock_gl):
        count = svc.post_inline_comments(
            "https://gitlab.com/myorg/myrepo/-/merge_requests/42",
            [],
        )

    assert count == 0
    mock_mr.discussions.create.assert_not_called()
    mock_mr.notes.create.assert_not_called()
