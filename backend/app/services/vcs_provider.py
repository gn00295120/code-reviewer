"""VCS provider abstraction layer for multi-platform support."""

import re
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass
class FileDiff:
    filename: str
    patch: str
    additions: int
    deletions: int
    status: str


@dataclass
class PRDiff:
    repo_name: str
    pr_number: int
    title: str
    body: str
    base_branch: str
    head_branch: str
    files: list[FileDiff]
    total_additions: int
    total_deletions: int


class VCSProvider(Protocol):
    def fetch_pr_diff(self, pr_url: str) -> PRDiff: ...
    def post_inline_comments(self, pr_url: str, findings: list[dict]) -> int: ...


_GITHUB_RE = re.compile(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)(?:[/?#]|$)")
_GITLAB_RE = re.compile(r"https?://[^/]+/(.+?)/-/merge_requests/(\d+)(?:[/?#]|$)")


_INVALID_URL_MSG = "Invalid URL — must be a GitHub PR or GitLab MR URL"


def parse_vcs_url(url: str) -> tuple[str, int, str]:
    """Parse a VCS URL into (repo_name, pr_number, platform)."""
    m = _GITHUB_RE.match(url)
    if m:
        return m.group(1), int(m.group(2)), "github"
    m = _GITLAB_RE.match(url)
    if m:
        return m.group(1), int(m.group(2)), "gitlab"
    raise ValueError(_INVALID_URL_MSG)


def detect_platform(url: str) -> Literal["github", "gitlab"]:
    """Detect VCS platform from a PR/MR URL."""
    _, _, platform = parse_vcs_url(url)
    return platform


def get_vcs_provider(platform: str) -> VCSProvider:
    """Return a VCS provider instance for the given platform."""
    if platform == "github":
        from app.services.github_service import GitHubService
        return GitHubService()
    elif platform == "gitlab":
        from app.services.gitlab_service import GitLabService
        return GitLabService()
    raise ValueError(f"Unknown platform: {platform}")
