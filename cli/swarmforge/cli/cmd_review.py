"""Review commands — submit, list, inspect, and act on code reviews."""

import asyncio
import json

import click
from rich.console import Console

from ..client import SwarmForgeError, client

console = Console()


def _run(coro):
    return asyncio.run(coro)


def _params(**kw):
    return {k: v for k, v in kw.items() if v is not None}


def _output(data):
    console.print_json(json.dumps(data, default=str))


def _handle_error(e: SwarmForgeError):
    console.print(f"[red]Error {e.status}[/red]: {e}")
    raise SystemExit(1)


@click.group("review")
def review_group():
    """Code review operations."""


@review_group.command("create")
@click.argument("pr_url")
@click.option("--template-id", default=None, help="UUID of a review template to apply.")
@click.option("--post", is_flag=True, default=False, help="Post findings as inline comments on the PR.")
@click.option("--severity-threshold", default="low", help="Minimum severity to post (high/medium/low/info).")
@click.option("--model", default="claude-sonnet-4-6-20250514", help="Anthropic model to use.")
@click.option("--backend", is_flag=True, default=False, help="Force backend proxy mode (requires running backend).")
def create(pr_url, template_id, post, severity_threshold, model, backend):
    """Submit a PR/MR URL for review.

    By default, runs standalone (no backend needed). Uses GITHUB_TOKEN and
    ANTHROPIC_API_KEY environment variables directly.

    Use --backend to route through the SwarmForge backend API instead.
    """
    if backend:
        payload = {"pr_url": pr_url}
        if template_id:
            payload["template_id"] = template_id
        try:
            _output(_run(client.post("/api/reviews", json=payload)))
        except SwarmForgeError as e:
            _handle_error(e)
    else:
        from ..reviewer import run_standalone_review
        run_standalone_review(
            pr_url,
            post=post,
            severity_threshold=severity_threshold,
            model=model,
        )


@review_group.command("list")
@click.option("--status", default=None, help="Filter by review status.")
@click.option("--repo", default=None, help="Filter by repository name or URL.")
@click.option("--platform", default=None, help="Filter by platform (github, gitlab).")
@click.option("--limit", default=None, type=int, help="Maximum number of results.")
def list_reviews(status, repo, platform, limit):
    """List reviews with optional filters."""
    try:
        _output(_run(client.get("/api/reviews", params=_params(status=status, repo=repo, platform=platform, limit=limit))))
    except SwarmForgeError as e:
        _handle_error(e)


@review_group.command("get")
@click.argument("review_id")
def get(review_id):
    """Get a single review by ID."""
    try:
        _output(_run(client.get(f"/api/reviews/{review_id}")))
    except SwarmForgeError as e:
        _handle_error(e)


@review_group.command("cancel")
@click.argument("review_id")
def cancel(review_id):
    """Cancel (delete) a review."""
    try:
        _output(_run(client.delete(f"/api/reviews/{review_id}")))
        console.print(f"[green]Review {review_id} cancelled.[/green]")
    except SwarmForgeError as e:
        _handle_error(e)


@review_group.command("findings")
@click.argument("review_id")
@click.option("--severity", default=None, help="Filter by severity level.")
@click.option("--agent-role", default=None, help="Filter by agent role.")
def findings(review_id, severity, agent_role):
    """List findings for a review."""
    try:
        _output(_run(client.get(
            f"/api/reviews/{review_id}/findings",
            params=_params(severity=severity, agent_role=agent_role),
        )))
    except SwarmForgeError as e:
        _handle_error(e)


@review_group.command("timeline")
@click.argument("review_id")
def timeline(review_id):
    """Show the event timeline for a review."""
    try:
        _output(_run(client.get(f"/api/reviews/{review_id}/timeline")))
    except SwarmForgeError as e:
        _handle_error(e)


@review_group.command("post-comments")
@click.argument("review_id")
@click.option("--severity-threshold", default=None, help="Minimum severity to post (e.g. warning, error).")
def post_comments(review_id, severity_threshold):
    """Post review findings as GitHub/GitLab comments."""
    payload = _params(severity_threshold=severity_threshold)
    try:
        _output(_run(client.post(f"/api/reviews/{review_id}/post-to-github", json=payload or {})))
    except SwarmForgeError as e:
        _handle_error(e)
