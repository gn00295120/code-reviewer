"""Tests for VCS provider abstraction (app/services/vcs_provider.py).

The python-gitlab package may not be installed. We inject a minimal stub into
sys.modules before any gitlab-related imports occur, following the same pattern
used in test_gitlab_service.py.
"""

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from app.services.vcs_provider import detect_platform, get_vcs_provider


# ---------------------------------------------------------------------------
# Inject gitlab stub so importing GitLabService does not fail
# ---------------------------------------------------------------------------

def _inject_stubs():
    """Inject stubs for optional dependencies that may not be installed locally."""
    if "gitlab" not in sys.modules:
        stub = types.ModuleType("gitlab")
        stub.Gitlab = MagicMock
        sys.modules["gitlab"] = stub
    if "github" not in sys.modules:
        stub = types.ModuleType("github")
        stub.Github = MagicMock
        auth_mod = types.ModuleType("github.Auth")
        auth_mod.Token = MagicMock
        stub.Auth = auth_mod
        sys.modules["github"] = stub
        sys.modules["github.Auth"] = auth_mod


_inject_stubs()


# ---------------------------------------------------------------------------
# detect_platform tests
# ---------------------------------------------------------------------------


def test_detect_platform_github_url():
    """detect_platform identifies a github.com PR URL as 'github'."""
    url = "https://github.com/owner/repo/pull/42"
    assert detect_platform(url) == "github"


def test_detect_platform_github_url_with_http():
    """detect_platform handles http:// github URLs correctly."""
    url = "http://github.com/owner/repo/pull/1"
    assert detect_platform(url) == "github"


def test_detect_platform_gitlab_com_url():
    """detect_platform identifies a gitlab.com MR URL as 'gitlab'."""
    url = "https://gitlab.com/myorg/myrepo/-/merge_requests/99"
    assert detect_platform(url) == "gitlab"


def test_detect_platform_self_hosted_gitlab_url():
    """detect_platform identifies a self-hosted GitLab MR URL as 'gitlab'."""
    url = "https://git.company.internal/team/project/-/merge_requests/7"
    assert detect_platform(url) == "gitlab"


def test_detect_platform_self_hosted_gitlab_nested_namespace():
    """detect_platform handles deeply nested GitLab group/subgroup paths."""
    url = "https://gitlab.mycompany.com/group/subgroup/project/-/merge_requests/3"
    assert detect_platform(url) == "gitlab"


def test_detect_platform_invalid_url_raises_value_error():
    """detect_platform raises ValueError for an unrecognized URL format."""
    with pytest.raises(ValueError, match="Invalid URL"):
        detect_platform("https://bitbucket.org/owner/repo/pull-requests/1")


def test_detect_platform_plain_string_raises_value_error():
    """detect_platform raises ValueError for a non-URL string."""
    with pytest.raises(ValueError, match="Invalid URL"):
        detect_platform("not-a-url")


def test_detect_platform_empty_string_raises_value_error():
    """detect_platform raises ValueError for an empty string."""
    with pytest.raises(ValueError, match="Invalid URL"):
        detect_platform("")


def test_detect_platform_github_url_does_not_match_gitlab():
    """A github.com URL must not be detected as gitlab."""
    url = "https://github.com/owner/repo/pull/10"
    assert detect_platform(url) != "gitlab"


def test_detect_platform_gitlab_url_does_not_match_github():
    """A GitLab MR URL must not be detected as github."""
    url = "https://gitlab.com/myorg/myrepo/-/merge_requests/5"
    assert detect_platform(url) != "github"


# ---------------------------------------------------------------------------
# get_vcs_provider tests
# ---------------------------------------------------------------------------


def test_get_vcs_provider_github_returns_github_service():
    """get_vcs_provider('github') returns a GitHubService instance."""
    with patch("app.services.github_service.get_settings") as mock_settings:
        mock_settings.return_value.github_token = "fake-token"
        from app.services.github_service import GitHubService
        provider = get_vcs_provider("github")
        assert isinstance(provider, GitHubService)


def test_get_vcs_provider_gitlab_returns_gitlab_service():
    """get_vcs_provider('gitlab') returns a GitLabService instance."""
    import app.services.gitlab_service as _gl_mod
    with patch.object(_gl_mod, "get_settings") as mock_settings:
        mock_settings.return_value.gitlab_token = "fake-token"
        mock_settings.return_value.gitlab_base_url = "https://gitlab.com"
        from app.services.gitlab_service import GitLabService
        provider = get_vcs_provider("gitlab")
        assert isinstance(provider, GitLabService)


def test_get_vcs_provider_unknown_raises_value_error():
    """get_vcs_provider raises ValueError for an unrecognized platform string."""
    with pytest.raises(ValueError, match="Unknown platform"):
        get_vcs_provider("bitbucket")


def test_get_vcs_provider_empty_string_raises_value_error():
    """get_vcs_provider raises ValueError for an empty platform string."""
    with pytest.raises(ValueError, match="Unknown platform"):
        get_vcs_provider("")


def test_get_vcs_provider_github_has_fetch_pr_diff():
    """The GitHub provider returned by get_vcs_provider has a fetch_pr_diff method."""
    with patch("app.services.github_service.get_settings") as mock_settings:
        mock_settings.return_value.github_token = "fake-token"
        provider = get_vcs_provider("github")
        assert callable(getattr(provider, "fetch_pr_diff", None))


def test_get_vcs_provider_github_has_post_inline_comments():
    """The GitHub provider returned by get_vcs_provider has a post_inline_comments method."""
    with patch("app.services.github_service.get_settings") as mock_settings:
        mock_settings.return_value.github_token = "fake-token"
        provider = get_vcs_provider("github")
        assert callable(getattr(provider, "post_inline_comments", None))


def test_get_vcs_provider_gitlab_has_fetch_pr_diff():
    """The GitLab provider returned by get_vcs_provider has a fetch_pr_diff method."""
    import app.services.gitlab_service as _gl_mod
    with patch.object(_gl_mod, "get_settings") as mock_settings:
        mock_settings.return_value.gitlab_token = "fake-token"
        mock_settings.return_value.gitlab_base_url = "https://gitlab.com"
        provider = get_vcs_provider("gitlab")
        assert callable(getattr(provider, "fetch_pr_diff", None))


def test_get_vcs_provider_gitlab_has_post_inline_comments():
    """The GitLab provider returned by get_vcs_provider has a post_inline_comments method."""
    import app.services.gitlab_service as _gl_mod
    with patch.object(_gl_mod, "get_settings") as mock_settings:
        mock_settings.return_value.gitlab_token = "fake-token"
        mock_settings.return_value.gitlab_base_url = "https://gitlab.com"
        provider = get_vcs_provider("gitlab")
        assert callable(getattr(provider, "post_inline_comments", None))


# ---------------------------------------------------------------------------
# VCSProvider protocol compliance
# ---------------------------------------------------------------------------


def test_github_service_satisfies_vcs_provider_protocol():
    """GitHubService is structurally compatible with the VCSProvider Protocol."""
    with patch("app.services.github_service.get_settings") as mock_settings:
        mock_settings.return_value.github_token = "fake-token"
        from app.services.github_service import GitHubService
        from app.services.vcs_provider import VCSProvider
        import typing

        provider = GitHubService()
        # Protocol structural check: both required methods must exist
        assert hasattr(provider, "fetch_pr_diff")
        assert hasattr(provider, "post_inline_comments")


def test_gitlab_service_satisfies_vcs_provider_protocol():
    """GitLabService is structurally compatible with the VCSProvider Protocol."""
    import app.services.gitlab_service as _gl_mod
    with patch.object(_gl_mod, "get_settings") as mock_settings:
        mock_settings.return_value.gitlab_token = "fake-token"
        mock_settings.return_value.gitlab_base_url = "https://gitlab.com"
        from app.services.gitlab_service import GitLabService

        provider = GitLabService()
        assert hasattr(provider, "fetch_pr_diff")
        assert hasattr(provider, "post_inline_comments")
