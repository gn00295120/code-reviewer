import re

from github import Github, Auth

from app.core.config import get_settings
from app.services.vcs_provider import FileDiff, PRDiff


class GitHubService:
    """GitHub VCS provider using PyGithub."""

    def __init__(self) -> None:
        self._token = get_settings().github_token

    def _get_client(self) -> Github:
        return Github(auth=Auth.Token(self._token))

    def fetch_pr_diff(self, pr_url: str) -> PRDiff:
        """Fetch structured diff from a GitHub PR URL."""
        match = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_url)
        if not match:
            raise ValueError(f"Invalid PR URL: {pr_url}")

        repo_name = match.group(1)
        pr_number = int(match.group(2))

        gh = self._get_client()
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        files = []
        total_add = 0
        total_del = 0

        for f in pr.get_files():
            files.append(
                FileDiff(
                    filename=f.filename,
                    patch=f.patch or "",
                    additions=f.additions,
                    deletions=f.deletions,
                    status=f.status,
                )
            )
            total_add += f.additions
            total_del += f.deletions

        return PRDiff(
            repo_name=repo_name,
            pr_number=pr_number,
            title=pr.title,
            body=pr.body or "",
            base_branch=pr.base.ref,
            head_branch=pr.head.ref,
            files=files,
            total_additions=total_add,
            total_deletions=total_del,
        )

    def post_inline_comments(self, pr_url: str, findings: list[dict]) -> int:
        """Post review findings as inline comments on a GitHub PR."""
        match = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_url)
        if not match:
            raise ValueError(f"Invalid PR URL: {pr_url}")

        repo_name = match.group(1)
        pr_number = int(match.group(2))

        gh = self._get_client()
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # Build review comments
        comments = []
        for finding in findings:
            body = f"**[{finding['severity'].upper()}]** {finding['title']}\n\n{finding['description']}"
            if finding.get("suggested_fix"):
                body += f"\n\n```suggestion\n{finding['suggested_fix']}\n```"
            body += f"\n\n_Agent: {finding['agent_role']} | Confidence: {finding['confidence']:.0%}_"

            comment = {
                "path": finding["file_path"],
                "body": body,
            }
            if finding.get("line_number"):
                comment["line"] = finding["line_number"]
                comment["side"] = "RIGHT"

            comments.append(comment)

        if not comments:
            return 0

        # Post as a single review with all comments
        pr.create_review(
            body=f"## SwarmForge Code Review\n\nFound **{len(comments)}** issues across {len(set(c['path'] for c in comments))} files.",
            event="COMMENT",
            comments=comments,
        )

        return len(comments)
