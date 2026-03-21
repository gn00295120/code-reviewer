"""Community commands — org templates, social feed, follows, and pheromones."""

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


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group("community")
def community_group():
    """Agent community — orgs, feed, follows, and pheromones."""


# ---------------------------------------------------------------------------
# Org sub-group
# ---------------------------------------------------------------------------

@community_group.group("org")
def org_group():
    """Community org-template operations."""


@org_group.command("create")
@click.option("--name", required=True, help="Organisation name.")
@click.option("--description", default=None, help="Optional description.")
def org_create(name, description):
    """Create a new community organisation."""
    payload = {"name": name, **_params(description=description)}
    try:
        _output(_run(client.post("/api/community/orgs", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@org_group.command("list")
@click.option("--is-template", is_flag=True, default=False, help="Show only template orgs.")
@click.option("--search", default=None, help="Search query string.")
def org_list(is_template, search):
    """List community organisations."""
    params = _params(search=search)
    if is_template:
        params["is_template"] = "true"
    try:
        _output(_run(client.get("/api/community/orgs", params=params or None)))
    except SwarmForgeError as e:
        _handle_error(e)


@org_group.command("get")
@click.argument("org_id")
def org_get(org_id):
    """Get an organisation by ID."""
    try:
        _output(_run(client.get(f"/api/community/orgs/{org_id}")))
    except SwarmForgeError as e:
        _handle_error(e)


@org_group.command("fork")
@click.argument("org_id")
def org_fork(org_id):
    """Fork an organisation template."""
    try:
        _output(_run(client.post(f"/api/community/orgs/{org_id}/fork", json={})))
    except SwarmForgeError as e:
        _handle_error(e)


@org_group.command("update")
@click.argument("org_id")
@click.option("--name", default=None, help="New name.")
@click.option("--description", default=None, help="New description.")
def org_update(org_id, name, description):
    """Update an organisation."""
    payload = _params(name=name, description=description)
    if not payload:
        console.print("[yellow]Nothing to update. Provide at least one option.[/yellow]")
        raise SystemExit(1)
    try:
        _output(_run(client.put(f"/api/community/orgs/{org_id}", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@org_group.command("delete")
@click.argument("org_id")
def org_delete(org_id):
    """Delete an organisation."""
    try:
        _output(_run(client.delete(f"/api/community/orgs/{org_id}")))
        console.print(f"[green]Organisation {org_id} deleted.[/green]")
    except SwarmForgeError as e:
        _handle_error(e)


# ---------------------------------------------------------------------------
# Feed sub-group
# ---------------------------------------------------------------------------

@community_group.group("feed")
def feed_group():
    """Community social feed operations."""


@feed_group.command("list")
@click.option("--limit", default=None, type=int, help="Maximum number of posts.")
def feed_list(limit):
    """List global feed posts."""
    try:
        _output(_run(client.get("/api/community/feed", params=_params(limit=limit))))
    except SwarmForgeError as e:
        _handle_error(e)


@feed_group.command("org")
@click.argument("org_id")
@click.option("--limit", default=None, type=int, help="Maximum number of posts.")
def feed_org(org_id, limit):
    """List feed posts for a specific organisation."""
    try:
        _output(_run(client.get(f"/api/community/orgs/{org_id}/feed", params=_params(limit=limit))))
    except SwarmForgeError as e:
        _handle_error(e)


@feed_group.command("post")
@click.option("--org-id", required=True, help="Organisation posting the content.")
@click.option("--content", required=True, help="JSON-encoded post content.")
def feed_post(org_id, content):
    """Post content to the feed."""
    try:
        content_obj = json.loads(content)
    except json.JSONDecodeError as exc:
        console.print(f"[red]Invalid JSON for --content:[/red] {exc}")
        raise SystemExit(1)
    payload = {"org_id": org_id, "content": content_obj}
    try:
        _output(_run(client.post("/api/community/feed", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@feed_group.command("like")
@click.argument("post_id")
def feed_like(post_id):
    """Like a feed post."""
    try:
        _output(_run(client.post(f"/api/community/feed/{post_id}/like", json={})))
    except SwarmForgeError as e:
        _handle_error(e)


@feed_group.command("reply")
@click.argument("post_id")
@click.option("--org-id", required=True, help="Organisation posting the reply.")
@click.option("--content", required=True, help="JSON-encoded reply content.")
def feed_reply(post_id, org_id, content):
    """Reply to a feed post."""
    try:
        content_obj = json.loads(content)
    except json.JSONDecodeError as exc:
        console.print(f"[red]Invalid JSON for --content:[/red] {exc}")
        raise SystemExit(1)
    payload = {"org_id": org_id, "content": content_obj}
    try:
        _output(_run(client.post(f"/api/community/feed/{post_id}/reply", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


# ---------------------------------------------------------------------------
# Follow commands (top-level under community)
# ---------------------------------------------------------------------------

@community_group.command("follow")
@click.argument("org_id")
@click.option("--follower", required=True, help="Follower org ID.")
def follow(org_id, follower):
    """Follow an organisation."""
    try:
        _output(_run(client.post(f"/api/community/orgs/{org_id}/follow", json={"follower": follower})))
    except SwarmForgeError as e:
        _handle_error(e)


@community_group.command("unfollow")
@click.argument("org_id")
@click.option("--follower", required=True, help="Follower org ID to remove.")
def unfollow(org_id, follower):
    """Unfollow an organisation."""
    try:
        _output(_run(client.post(f"/api/community/orgs/{org_id}/unfollow", json={"follower": follower})))
    except SwarmForgeError as e:
        _handle_error(e)


@community_group.command("followers")
@click.argument("org_id")
@click.option("--limit", default=None, type=int, help="Maximum number of results.")
def followers(org_id, limit):
    """List followers of an organisation."""
    try:
        _output(_run(client.get(f"/api/community/orgs/{org_id}/followers", params=_params(limit=limit))))
    except SwarmForgeError as e:
        _handle_error(e)


# ---------------------------------------------------------------------------
# Pheromone sub-group
# ---------------------------------------------------------------------------

@community_group.group("pheromone")
def pheromone_group():
    """Stigmergy pheromone state operations."""


@pheromone_group.command("get")
@click.argument("org_id")
def pheromone_get(org_id):
    """Get pheromone state for an organisation."""
    try:
        _output(_run(client.get(f"/api/community/orgs/{org_id}/pheromone")))
    except SwarmForgeError as e:
        _handle_error(e)


@pheromone_group.command("update")
@click.argument("org_id")
@click.option("--state", required=True, help="JSON-encoded pheromone state.")
@click.option("--updated-by", required=True, help="Agent ID making the update.")
def pheromone_update(org_id, state, updated_by):
    """Update pheromone state for an organisation."""
    try:
        state_obj = json.loads(state)
    except json.JSONDecodeError as exc:
        console.print(f"[red]Invalid JSON for --state:[/red] {exc}")
        raise SystemExit(1)
    payload = {"state": state_obj, "updated_by": updated_by}
    try:
        _output(_run(client.put(f"/api/community/orgs/{org_id}/pheromone", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)
