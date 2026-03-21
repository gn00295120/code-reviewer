"""Template commands — manage review templates."""

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


@click.group("template")
def template_group():
    """Review template operations."""


@template_group.command("list")
@click.option("--created-by", default=None, help="Filter by creator user ID.")
def list_templates(created_by):
    """List all review templates."""
    try:
        _output(_run(client.get("/api/templates", params=_params(created_by=created_by))))
    except SwarmForgeError as e:
        _handle_error(e)


@template_group.command("create")
@click.option("--name", required=True, help="Template name.")
@click.option("--description", default=None, help="Optional description.")
@click.option("--rules", default=None, help="JSON-encoded rules object.")
def create(name, description, rules):
    """Create a new review template."""
    payload = {"name": name}
    if description:
        payload["description"] = description
    if rules:
        try:
            payload["rules"] = json.loads(rules)
        except json.JSONDecodeError as exc:
            console.print(f"[red]Invalid JSON for --rules:[/red] {exc}")
            raise SystemExit(1)
    try:
        _output(_run(client.post("/api/templates", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@template_group.command("get")
@click.argument("template_id")
def get(template_id):
    """Get a template by ID."""
    try:
        _output(_run(client.get(f"/api/templates/{template_id}")))
    except SwarmForgeError as e:
        _handle_error(e)


@template_group.command("update")
@click.argument("template_id")
@click.option("--name", default=None, help="New template name.")
@click.option("--description", default=None, help="New description.")
@click.option("--rules", default=None, help="JSON-encoded rules object.")
def update(template_id, name, description, rules):
    """Update an existing template."""
    payload = _params(name=name, description=description)
    if rules:
        try:
            payload["rules"] = json.loads(rules)
        except json.JSONDecodeError as exc:
            console.print(f"[red]Invalid JSON for --rules:[/red] {exc}")
            raise SystemExit(1)
    if not payload:
        console.print("[yellow]Nothing to update. Provide at least one option.[/yellow]")
        raise SystemExit(1)
    try:
        _output(_run(client.put(f"/api/templates/{template_id}", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@template_group.command("delete")
@click.argument("template_id")
def delete(template_id):
    """Delete a template."""
    try:
        _output(_run(client.delete(f"/api/templates/{template_id}")))
        console.print(f"[green]Template {template_id} deleted.[/green]")
    except SwarmForgeError as e:
        _handle_error(e)


@template_group.command("fork")
@click.argument("template_id")
def fork(template_id):
    """Fork an existing template into a new copy."""
    try:
        _output(_run(client.post(f"/api/templates/{template_id}/fork", json={})))
    except SwarmForgeError as e:
        _handle_error(e)
