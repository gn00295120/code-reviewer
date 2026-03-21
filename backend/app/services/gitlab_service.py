"""GitLab VCS provider for fetching MR diffs and posting review comments."""

import re

import gitlab

from app.core.config import get_settings
from app.services.vcs_provider import FileDiff, PRDiff

_GITLAB_MR_RE = re.compile(r"https?://([^/]+)/(.+?)/-/merge_requests/(\d+)")


def _map_status(change: dict) -> str:
    if change.get("new_file"):
        return "added"
    if change.get("deleted_file"):
        return "removed"
    if change.get("renamed_file"):
        return "renamed"
    return "modified"


class GitLabService:
    """GitLab VCS provider using python-gitlab."""

    def __init__(self) -> None:
        settings = get_settings()
        self._token = settings.gitlab_token

    def _parse_mr_url(self, mr_url: str) -> tuple[str, str, int]:
        """Parse a GitLab MR URL into (base_url, project_path, mr_iid)."""
        match = _GITLAB_MR_RE.match(mr_url)
        if not match:
            raise ValueError(f"Invalid GitLab MR URL: {mr_url}")
        host = match.group(1)
        project_path = match.group(2)
        mr_iid = int(match.group(3))
        base_url = f"https://{host}"
        return base_url, project_path, mr_iid

    def _get_client(self, base_url: str) -> gitlab.Gitlab:
        return gitlab.Gitlab(base_url, private_token=self._token)

    def fetch_pr_diff(self, pr_url: str) -> PRDiff:
        """Fetch structured diff from a GitLab MR URL."""
        base_url, project_path, mr_iid = self._parse_mr_url(pr_url)
        gl = self._get_client(base_url)
        project = gl.projects.get(project_path)
        mr = project.mergerequests.get(mr_iid)
        changes = mr.changes()["changes"]

        files = []
        total_add = 0
        total_del = 0

        for change in changes:
            patch = change.get("diff", "")
            lines = patch.splitlines()
            additions = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
            deletions = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))
            files.append(
                FileDiff(
                    filename=change["new_path"],
                    patch=patch,
                    additions=additions,
                    deletions=deletions,
                    status=_map_status(change),
                )
            )
            total_add += additions
            total_del += deletions

        return PRDiff(
            repo_name=project_path,
            pr_number=mr_iid,
            title=mr.title,
            body=mr.description or "",
            base_branch=mr.target_branch,
            head_branch=mr.source_branch,
            files=files,
            total_additions=total_add,
            total_deletions=total_del,
        )

    def post_inline_comments(self, pr_url: str, findings: list[dict]) -> int:
        """Post review findings as inline comments on a GitLab MR."""
        base_url, project_path, mr_iid = self._parse_mr_url(pr_url)
        gl = self._get_client(base_url)
        project = gl.projects.get(project_path)
        mr = project.mergerequests.get(mr_iid)

        diff_refs = mr.diff_refs
        posted = 0

        for finding in findings:
            body = f"**[{finding['severity'].upper()}]** {finding['title']}\n\n{finding['description']}"
            if finding.get("suggested_fix"):
                body += f"\n\n```suggestion:-0+0\n{finding['suggested_fix']}\n```"
            body += f"\n\n_Agent: {finding['agent_role']} | Confidence: {finding['confidence']:.0%}_"

            discussion_data: dict = {"body": body}

            if diff_refs and finding.get("line_number") and finding.get("file_path"):
                discussion_data["position"] = {
                    "base_sha": diff_refs["base_sha"],
                    "start_sha": diff_refs["start_sha"],
                    "head_sha": diff_refs["head_sha"],
                    "position_type": "text",
                    "new_path": finding["file_path"],
                    "new_line": finding["line_number"],
                }

            mr.discussions.create(discussion_data)
            posted += 1

        # Post summary note
        if posted > 0:
            unique_files = len(set(f["file_path"] for f in findings if f.get("file_path")))
            mr.notes.create({
                "body": f"## SwarmForge Code Review\n\nFound **{posted}** issues across {unique_files} files.",
            })

        return posted
