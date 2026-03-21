"""Enterprise commands — audit logs and policy management."""

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


@click.group("enterprise")
def enterprise_group():
    """Enterprise audit and policy operations."""


@enterprise_group.command("audit")
@click.option("--action", default=None, help="Filter by action type.")
@click.option("--actor", default=None, help="Filter by actor user/agent ID.")
@click.option("--since", default=None, help="ISO datetime lower bound.")
@click.option("--until", default=None, help="ISO datetime upper bound.")
@click.option("--limit", default=None, type=int, help="Maximum number of results.")
def audit(action, actor, since, until, limit):
    """Query the enterprise audit log."""
    try:
        _output(_run(client.get(
            "/api/enterprise/audit",
            params=_params(action=action, actor=actor, since=since, until=until, limit=limit),
        )))
    except SwarmForgeError as e:
        _handle_error(e)


@enterprise_group.command("policy-list")
@click.option("--type", "policy_type", default=None, help="Filter by policy type.")
@click.option("--active", is_flag=True, default=False, help="Show only active policies.")
def policy_list(policy_type, active):
    """List enterprise policies."""
    params = _params(type=policy_type)
    if active:
        params["active"] = "true"
    try:
        _output(_run(client.get("/api/enterprise/policies", params=params or None)))
    except SwarmForgeError as e:
        _handle_error(e)


@enterprise_group.command("policy-create")
@click.option("--name", required=True, help="Policy name.")
@click.option("--type", "policy_type", required=True, help="Policy type.")
@click.option("--config", required=True, help="JSON-encoded policy configuration.")
def policy_create(name, policy_type, config):
    """Create a new enterprise policy."""
    try:
        config_obj = json.loads(config)
    except json.JSONDecodeError as exc:
        console.print(f"[red]Invalid JSON for --config:[/red] {exc}")
        raise SystemExit(1)
    payload = {"name": name, "type": policy_type, "config": config_obj}
    try:
        _output(_run(client.post("/api/enterprise/policies", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@enterprise_group.command("policy-update")
@click.argument("policy_id")
@click.option("--name", default=None, help="New policy name.")
@click.option("--config", default=None, help="JSON-encoded updated configuration.")
def policy_update(policy_id, name, config):
    """Update an enterprise policy."""
    payload = _params(name=name)
    if config:
        try:
            payload["config"] = json.loads(config)
        except json.JSONDecodeError as exc:
            console.print(f"[red]Invalid JSON for --config:[/red] {exc}")
            raise SystemExit(1)
    if not payload:
        console.print("[yellow]Nothing to update. Provide at least one option.[/yellow]")
        raise SystemExit(1)
    try:
        _output(_run(client.put(f"/api/enterprise/policies/{policy_id}", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@enterprise_group.command("policy-toggle")
@click.argument("policy_id")
def policy_toggle(policy_id):
    """Toggle the active/inactive state of a policy."""
    try:
        _output(_run(client.post(f"/api/enterprise/policies/{policy_id}/toggle", json={})))
    except SwarmForgeError as e:
        _handle_error(e)
