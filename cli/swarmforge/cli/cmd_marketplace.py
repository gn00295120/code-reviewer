"""Marketplace commands — browse, publish, and install agent listings."""

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


@click.group("marketplace")
def marketplace_group():
    """Marketplace listing operations."""


@marketplace_group.command("browse")
@click.option("--query", default=None, help="Full-text search query.")
@click.option("--type", "listing_type", default=None, help="Filter by listing type.")
@click.option("--sort", default=None, help="Sort order (e.g. stars, newest).")
@click.option("--limit", default=None, type=int, help="Maximum number of results.")
def browse(query, listing_type, sort, limit):
    """Browse marketplace listings."""
    try:
        _output(_run(client.get(
            "/api/marketplace",
            params=_params(query=query, type=listing_type, sort=sort, limit=limit),
        )))
    except SwarmForgeError as e:
        _handle_error(e)


@marketplace_group.command("get")
@click.argument("listing_id")
def get(listing_id):
    """Get a marketplace listing by ID."""
    try:
        _output(_run(client.get(f"/api/marketplace/{listing_id}")))
    except SwarmForgeError as e:
        _handle_error(e)


@marketplace_group.command("publish")
@click.option("--type", "listing_type", required=True, help="Listing type (agent, template, tool).")
@click.option("--title", required=True, help="Listing title.")
@click.option("--description", required=True, help="Listing description.")
@click.option("--version", required=True, help="Semantic version string.")
@click.option("--tags", default=None, help="Comma-separated list of tags.")
def publish(listing_type, title, description, version, tags):
    """Publish a new marketplace listing."""
    payload = {
        "type": listing_type,
        "title": title,
        "description": description,
        "version": version,
    }
    if tags:
        payload["tags"] = [t.strip() for t in tags.split(",")]
    try:
        _output(_run(client.post("/api/marketplace", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@marketplace_group.command("update")
@click.argument("listing_id")
@click.option("--title", default=None, help="New title.")
@click.option("--description", default=None, help="New description.")
def update(listing_id, title, description):
    """Update an existing marketplace listing."""
    payload = _params(title=title, description=description)
    if not payload:
        console.print("[yellow]Nothing to update. Provide at least one option.[/yellow]")
        raise SystemExit(1)
    try:
        _output(_run(client.put(f"/api/marketplace/{listing_id}", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@marketplace_group.command("install")
@click.argument("listing_id")
def install(listing_id):
    """Install a marketplace listing into your workspace."""
    try:
        _output(_run(client.post(f"/api/marketplace/{listing_id}/install", json={})))
    except SwarmForgeError as e:
        _handle_error(e)


@marketplace_group.command("rate")
@click.argument("listing_id")
@click.option("--stars", required=True, type=click.IntRange(1, 5), help="Rating from 1 to 5.")
def rate(listing_id, stars):
    """Rate a marketplace listing."""
    try:
        _output(_run(client.post(f"/api/marketplace/{listing_id}/rate", json={"stars": stars})))
    except SwarmForgeError as e:
        _handle_error(e)
