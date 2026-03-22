"""Standalone review engine — runs locally using Claude Code SDK.

Uses the user's Claude Code subscription (no API key needed).
PyGithub fetches PR diffs, Claude Code SDK runs the review agents.
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass, field

from github import Auth, Github
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner

console = Console()

AGENT_PROMPTS = {
    "logic": """You are an expert code reviewer specializing in LOGIC and CORRECTNESS.
Review the code diff for:
- Logical errors, off-by-one errors, incorrect conditions
- Missing null/undefined checks where needed
- Race conditions or concurrency issues
- Incorrect algorithm implementations
- Wrong variable usage or scope issues""",

    "security": """You are an expert code reviewer specializing in SECURITY.
Review the code diff for:
- SQL injection, XSS, command injection vulnerabilities
- Authentication/authorization flaws
- Sensitive data exposure (hardcoded secrets, logging PII)
- Insecure cryptographic usage
- CSRF, SSRF, path traversal vulnerabilities""",

    "edge_case": """You are an expert code reviewer specializing in EDGE CASES and ROBUSTNESS.
Review the code diff for:
- Unhandled edge cases (empty inputs, boundary values, overflow)
- Missing error handling for expected failure modes
- Incomplete input validation at system boundaries
- Resource leaks (unclosed connections, file handles)""",

    "convention": """You are an expert code reviewer specializing in CODE CONVENTIONS and MAINTAINABILITY.
Review the code diff for:
- Naming convention violations
- Inconsistent code style within the codebase context
- Dead code or unnecessary complexity
- Violations of DRY, SOLID, or other design principles""",

    "performance": """You are an expert code reviewer specializing in PERFORMANCE.
Review the code diff for:
- N+1 query patterns or unnecessary database calls
- Missing indexes for queried fields
- Unnecessary memory allocations or copies
- Blocking operations in async contexts
- Inefficient algorithms (O(n^2) where O(n) is possible)""",
}

FINDING_INSTRUCTION = """
For each issue found, respond with ONLY a JSON object (no markdown, no explanation, just raw JSON):
{"findings": [{"severity": "high|medium|low|info", "file_path": "path/to/file", "line_number": 42, "title": "Short title", "description": "Detailed explanation", "suggested_fix": "Code suggestion or null", "confidence": 0.9}]}

If no issues found, respond with: {"findings": []}
"""

SKIP_PATTERNS = {
    ".lock", ".sum", ".mod", "package-lock.json", "yarn.lock",
    "pnpm-lock.yaml", ".min.js", ".min.css", ".map",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot",
}


@dataclass
class Finding:
    agent_role: str
    severity: str
    file_path: str
    line_number: int | None
    title: str
    description: str
    suggested_fix: str | None
    confidence: float


@dataclass
class ReviewResult:
    repo_name: str
    pr_number: int
    title: str
    findings: list[Finding] = field(default_factory=list)
    agents_completed: int = 0
    total_agents: int = 5


def _should_skip(filename: str) -> bool:
    return any(filename.endswith(ext) for ext in SKIP_PATTERNS)


def _fetch_pr_diff(pr_url: str, token: str) -> dict:
    """Fetch PR diff from GitHub."""
    match = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}")

    repo_name = match.group(1)
    pr_number = int(match.group(2))

    gh = Github(auth=Auth.Token(token))
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    files = []
    for f in pr.get_files():
        if _should_skip(f.filename):
            continue
        if not f.patch:
            continue
        files.append({
            "filename": f.filename,
            "patch": f.patch,
            "additions": f.additions,
            "deletions": f.deletions,
        })

    return {
        "repo_name": repo_name,
        "pr_number": pr_number,
        "title": pr.title,
        "body": pr.body or "",
        "files": files,
    }


def _build_diff_context(files: list[dict]) -> str:
    parts = []
    for f in files:
        parts.append(f"### {f['filename']}\n```diff\n{f['patch']}\n```")
    return "\n\n".join(parts)


async def _run_agent_claude_code(agent_role: str, diff_context: str) -> list[Finding]:
    """Run a single review agent via Claude Code SDK (uses local subscription)."""
    from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage

    system_prompt = AGENT_PROMPTS[agent_role] + "\n\n" + FINDING_INSTRUCTION
    prompt = f"Review this PR diff and respond with ONLY the JSON findings:\n\n{diff_context}"

    full_text = ""
    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(
                system_prompt=system_prompt,
                max_turns=1,
                allowed_tools=[],
            ),
        ):
            if not isinstance(message, AssistantMessage):
                continue
            for block in message.content:
                if hasattr(block, "text"):
                    full_text += block.text
    except Exception as e:
        # Claude Code SDK may raise on unknown event types (e.g. rate_limit_event)
        # If we already collected text, continue with parsing
        if not full_text:
            console.print(f"  [yellow]Warning: {agent_role} agent failed: {e}[/yellow]")
            return []

    if not full_text:
        return []

    # Parse JSON from response
    try:
        result = json.loads(full_text)
    except json.JSONDecodeError:
        json_match = re.search(r'\{[\s\S]*"findings"[\s\S]*\}', full_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            return []

    findings = []
    for f in result.get("findings", []):
        findings.append(Finding(
            agent_role=agent_role,
            severity=f.get("severity", "info"),
            file_path=f.get("file_path", ""),
            line_number=f.get("line_number"),
            title=f.get("title", ""),
            description=f.get("description", ""),
            suggested_fix=f.get("suggested_fix"),
            confidence=f.get("confidence", 0.5),
        ))
    return findings


def _post_comments(pr_url: str, token: str, findings: list[Finding]) -> int:
    """Post findings as inline PR comments on GitHub."""
    match = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_url)
    if not match:
        return 0

    gh = Github(auth=Auth.Token(token))
    repo = gh.get_repo(match.group(1))
    pr = repo.get_pull(int(match.group(2)))

    comments = []
    for f in findings:
        body = f"**[{f.severity.upper()}]** {f.title}\n\n{f.description}"
        if f.suggested_fix:
            body += f"\n\n```suggestion\n{f.suggested_fix}\n```"
        body += f"\n\n_Agent: {f.agent_role} | Confidence: {f.confidence:.0%}_"

        comment = {"path": f.file_path, "body": body}
        if f.line_number:
            comment["line"] = f.line_number
            comment["side"] = "RIGHT"
        comments.append(comment)

    if not comments:
        return 0

    pr.create_review(
        body=f"## SwarmForge Code Review\n\nFound **{len(comments)}** issues across {len(set(c['path'] for c in comments))} files.",
        event="COMMENT",
        comments=comments,
    )
    return len(comments)


SEVERITY_COLORS = {"high": "red", "medium": "yellow", "low": "cyan", "info": "dim"}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}


def _display_results(result: ReviewResult):
    """Pretty-print review results to terminal."""
    if not result.findings:
        console.print(Panel(
            "[green]No issues found![/green]",
            title=f"{result.repo_name} #{result.pr_number}",
        ))
        return

    severity_counts = {}
    for f in result.findings:
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

    summary = Table(title=f"{result.repo_name} #{result.pr_number}: {result.title}")
    summary.add_column("Severity", style="bold")
    summary.add_column("Count", justify="right")
    for sev in ["high", "medium", "low", "info"]:
        count = severity_counts.get(sev, 0)
        if count:
            summary.add_row(f"[{SEVERITY_COLORS[sev]}]{sev.upper()}[/{SEVERITY_COLORS[sev]}]", str(count))
    summary.add_row("[bold]Total[/bold]", f"[bold]{len(result.findings)}[/bold]")
    console.print(summary)
    console.print()

    sorted_findings = sorted(result.findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 3))
    for f in sorted_findings:
        color = SEVERITY_COLORS.get(f.severity, "white")
        header = f"[{color}][{f.severity.upper()}][/{color}] {f.title}"
        body = f"[dim]{f.file_path}"
        if f.line_number:
            body += f":{f.line_number}"
        body += f" | {f.agent_role} | {f.confidence:.0%}[/dim]\n\n{f.description}"
        if f.suggested_fix:
            body += f"\n\n[green]Suggested fix:[/green]\n```\n{f.suggested_fix}\n```"
        console.print(Panel(body, title=header, border_style=color))


def run_standalone_review(
    pr_url: str,
    *,
    post: bool = False,
    severity_threshold: str = "low",
    model: str = "claude-sonnet-4-6-20250514",
) -> ReviewResult:
    """Run a standalone code review using Claude Code SDK (no API key needed)."""
    github_token = os.environ.get("GITHUB_TOKEN", "")

    if not github_token:
        # Try reading from .env in common locations
        for env_path in [".env", "../.env", os.path.expanduser("~/.env")]:
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("GITHUB_TOKEN=") and line.strip().split("=", 1)[1]:
                            github_token = line.strip().split("=", 1)[1]
                            break
            if github_token:
                break

    if not github_token:
        console.print("[red]Error: GITHUB_TOKEN is required (set env var or .env file)[/red]")
        raise SystemExit(1)

    # Step 1: Fetch PR diff
    console.print(f"[bold]Fetching PR diff...[/bold]")
    pr_data = _fetch_pr_diff(pr_url, github_token)
    console.print(f"  {pr_data['repo_name']} #{pr_data['pr_number']}: {pr_data['title']}")
    console.print(f"  {len(pr_data['files'])} files to review")

    if not pr_data["files"]:
        console.print("[yellow]No reviewable files found.[/yellow]")
        return ReviewResult(
            repo_name=pr_data["repo_name"],
            pr_number=pr_data["pr_number"],
            title=pr_data["title"],
        )

    diff_context = _build_diff_context(pr_data["files"])

    # Step 2: Run 5 agents sequentially via Claude Code SDK
    # (Claude Code SDK spawns subprocesses, so we run sequentially to avoid overload)
    console.print(f"\n[bold]Running 5 review agents via Claude Code...[/bold]")
    result = ReviewResult(
        repo_name=pr_data["repo_name"],
        pr_number=pr_data["pr_number"],
        title=pr_data["title"],
    )

    for role in AGENT_PROMPTS:
        console.print(f"  Running [bold]{role}[/bold] agent...", end="")
        findings = asyncio.run(_run_agent_claude_code(role, diff_context))
        result.findings.extend(findings)
        result.agents_completed += 1
        console.print(f" {len(findings)} findings")

    # Step 3: Display results
    console.print()
    _display_results(result)

    # Step 4: Post comments if requested
    if post and result.findings:
        threshold_order = SEVERITY_ORDER.get(severity_threshold, 2)
        postable = [f for f in result.findings if SEVERITY_ORDER.get(f.severity, 3) <= threshold_order]
        if postable:
            console.print(f"\n[bold]Posting {len(postable)} comments to GitHub...[/bold]")
            posted = _post_comments(pr_url, github_token, postable)
            console.print(f"[green]Posted {posted} inline comments.[/green]")
        else:
            console.print(f"[dim]No findings above {severity_threshold} threshold to post.[/dim]")

    return result
