"""Miscellaneous commands — health, stats, org-templates, and org-deploy."""

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
# Root misc group
# ---------------------------------------------------------------------------

@click.group("misc")
def misc_group():
    """Miscellaneous platform utilities."""


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@misc_group.command("health")
def health():
    """Check the health of the SwarmForge API."""
    try:
        _output(_run(client.get("/api/health")))
    except SwarmForgeError as e:
        _handle_error(e)


# ---------------------------------------------------------------------------
# Stats sub-group
# ---------------------------------------------------------------------------

@misc_group.group("stats")
def stats_group():
    """Platform statistics."""


@stats_group.command("queue")
def stats_queue():
    """Show current task queue statistics."""
    try:
        _output(_run(client.get("/api/stats/queue")))
    except SwarmForgeError as e:
        _handle_error(e)


@stats_group.command("overview")
def stats_overview():
    """Show an overview of platform-wide statistics."""
    try:
        _output(_run(client.get("/api/stats/overview")))
    except SwarmForgeError as e:
        _handle_error(e)


# ---------------------------------------------------------------------------
# Org-template sub-group
# ---------------------------------------------------------------------------

@misc_group.group("org-template")
def org_template_group():
    """Built-in org template operations."""


@org_template_group.command("list")
def org_template_list():
    """List available built-in org templates."""
    try:
        _output(_run(client.get("/api/org-templates")))
    except SwarmForgeError as e:
        _handle_error(e)


@org_template_group.command("instantiate")
@click.argument("name")
def org_template_instantiate(name):
    """Instantiate a built-in org template by name."""
    try:
        _output(_run(client.post("/api/org-templates/instantiate", json={"name": name})))
    except SwarmForgeError as e:
        _handle_error(e)


# ---------------------------------------------------------------------------
# Org-deploy sub-group
# ---------------------------------------------------------------------------

@misc_group.group("org-deploy")
def org_deploy_group():
    """Deploy and manage running org instances."""


@org_deploy_group.command("deploy")
@click.argument("org_id")
def org_deploy_deploy(org_id):
    """Deploy an organisation into a live runtime."""
    try:
        _output(_run(client.post(f"/api/org-deploy/{org_id}/deploy", json={})))
    except SwarmForgeError as e:
        _handle_error(e)


@org_deploy_group.command("status")
@click.argument("org_id")
def org_deploy_status(org_id):
    """Get the deployment status of an organisation."""
    try:
        _output(_run(client.get(f"/api/org-deploy/{org_id}/status")))
    except SwarmForgeError as e:
        _handle_error(e)


@org_deploy_group.command("stop")
@click.argument("org_id")
def org_deploy_stop(org_id):
    """Stop a deployed organisation."""
    try:
        _output(_run(client.post(f"/api/org-deploy/{org_id}/stop", json={})))
    except SwarmForgeError as e:
        _handle_error(e)
