"""Company commands — manage agent companies and their agents."""

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


@click.group("company")
def company_group():
    """Agent company operations."""


@company_group.command("create")
@click.option("--name", required=True, help="Company name.")
@click.option("--description", default=None, help="Company description.")
@click.option("--owner", default=None, help="Owner user ID.")
def create(name, description, owner):
    """Create a new agent company."""
    payload = {"name": name, **_params(description=description, owner=owner)}
    try:
        _output(_run(client.post("/api/companies", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@company_group.command("list")
@click.option("--status", default=None, help="Filter by status.")
@click.option("--owner", default=None, help="Filter by owner user ID.")
@click.option("--limit", default=None, type=int, help="Maximum number of results.")
def list_companies(status, owner, limit):
    """List agent companies."""
    try:
        _output(_run(client.get("/api/companies", params=_params(status=status, owner=owner, limit=limit))))
    except SwarmForgeError as e:
        _handle_error(e)


@company_group.command("get")
@click.argument("company_id")
def get(company_id):
    """Get a company by ID."""
    try:
        _output(_run(client.get(f"/api/companies/{company_id}")))
    except SwarmForgeError as e:
        _handle_error(e)


@company_group.command("update")
@click.argument("company_id")
@click.option("--name", default=None, help="New company name.")
@click.option("--description", default=None, help="New description.")
def update(company_id, name, description):
    """Update company details."""
    payload = _params(name=name, description=description)
    if not payload:
        console.print("[yellow]Nothing to update. Provide at least one option.[/yellow]")
        raise SystemExit(1)
    try:
        _output(_run(client.put(f"/api/companies/{company_id}", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@company_group.command("activate")
@click.argument("company_id")
def activate(company_id):
    """Activate a paused or draft company."""
    try:
        _output(_run(client.post(f"/api/companies/{company_id}/activate", json={})))
    except SwarmForgeError as e:
        _handle_error(e)


@company_group.command("pause")
@click.argument("company_id")
def pause(company_id):
    """Pause an active company."""
    try:
        _output(_run(client.post(f"/api/companies/{company_id}/pause", json={})))
    except SwarmForgeError as e:
        _handle_error(e)


@company_group.command("budget")
@click.argument("company_id")
def budget(company_id):
    """View budget and cost breakdown for a company."""
    try:
        _output(_run(client.get(f"/api/companies/{company_id}/budget")))
    except SwarmForgeError as e:
        _handle_error(e)


@company_group.command("agent-list")
@click.argument("company_id")
def agent_list(company_id):
    """List agents belonging to a company."""
    try:
        _output(_run(client.get(f"/api/companies/{company_id}/agents")))
    except SwarmForgeError as e:
        _handle_error(e)


@company_group.command("agent-add")
@click.argument("company_id")
@click.option("--name", required=True, help="Agent name.")
@click.option("--role", required=True, help="Agent role.")
@click.option("--model", default=None, help="LLM model identifier.")
def agent_add(company_id, name, role, model):
    """Add an agent to a company."""
    payload = {"name": name, "role": role, **_params(model=model)}
    try:
        _output(_run(client.post(f"/api/companies/{company_id}/agents", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@company_group.command("agent-update")
@click.argument("company_id")
@click.argument("agent_id")
@click.option("--name", default=None, help="New agent name.")
@click.option("--role", default=None, help="New agent role.")
def agent_update(company_id, agent_id, name, role):
    """Update an agent within a company."""
    payload = _params(name=name, role=role)
    if not payload:
        console.print("[yellow]Nothing to update. Provide at least one option.[/yellow]")
        raise SystemExit(1)
    try:
        _output(_run(client.put(f"/api/companies/{company_id}/agents/{agent_id}", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@company_group.command("agent-remove")
@click.argument("company_id")
@click.argument("agent_id")
def agent_remove(company_id, agent_id):
    """Remove an agent from a company."""
    try:
        _output(_run(client.delete(f"/api/companies/{company_id}/agents/{agent_id}")))
        console.print(f"[green]Agent {agent_id} removed from company {company_id}.[/green]")
    except SwarmForgeError as e:
        _handle_error(e)
