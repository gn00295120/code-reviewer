"""Memory commands — manage agent memory entries."""

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


@click.group("memory")
def memory_group():
    """Agent memory operations."""


@memory_group.command("list")
@click.option("--agent-role", default=None, help="Filter by agent role.")
@click.option("--memory-type", default=None, help="Filter by memory type.")
@click.option("--limit", default=None, type=int, help="Maximum number of results.")
def list_memories(agent_role, memory_type, limit):
    """List agent memory entries."""
    try:
        _output(_run(client.get(
            "/api/memories",
            params=_params(agent_role=agent_role, memory_type=memory_type, limit=limit),
        )))
    except SwarmForgeError as e:
        _handle_error(e)


@memory_group.command("search")
@click.argument("query")
@click.option("--agent-role", default=None, help="Restrict search to this agent role.")
@click.option("--limit", default=None, type=int, help="Maximum number of results.")
def search(query, agent_role, limit):
    """Semantic search across agent memories."""
    try:
        _output(_run(client.get(
            "/api/memories/search",
            params=_params(query=query, agent_role=agent_role, limit=limit),
        )))
    except SwarmForgeError as e:
        _handle_error(e)


@memory_group.command("get")
@click.argument("memory_id")
def get(memory_id):
    """Get a single memory entry by ID."""
    try:
        _output(_run(client.get(f"/api/memories/{memory_id}")))
    except SwarmForgeError as e:
        _handle_error(e)


@memory_group.command("create")
@click.option("--agent-role", required=True, help="Agent role that owns this memory.")
@click.option("--memory-type", required=True, help="Memory type (e.g. episodic, semantic).")
@click.option("--content", required=True, help="JSON-encoded content object.")
def create(agent_role, memory_type, content):
    """Create a new memory entry."""
    try:
        content_obj = json.loads(content)
    except json.JSONDecodeError as exc:
        console.print(f"[red]Invalid JSON for --content:[/red] {exc}")
        raise SystemExit(1)
    payload = {
        "agent_role": agent_role,
        "memory_type": memory_type,
        "content": content_obj,
    }
    try:
        _output(_run(client.post("/api/memories", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@memory_group.command("delete")
@click.argument("memory_id")
def delete(memory_id):
    """Delete a memory entry."""
    try:
        _output(_run(client.delete(f"/api/memories/{memory_id}")))
        console.print(f"[green]Memory {memory_id} deleted.[/green]")
    except SwarmForgeError as e:
        _handle_error(e)


@memory_group.command("consolidate")
@click.option("--agent-role", default=None, help="Consolidate memories for this agent role only.")
def consolidate(agent_role):
    """Trigger memory consolidation (deduplicate + summarise)."""
    payload = _params(agent_role=agent_role)
    try:
        _output(_run(client.post("/api/memories/consolidate", json=payload or {})))
    except SwarmForgeError as e:
        _handle_error(e)
