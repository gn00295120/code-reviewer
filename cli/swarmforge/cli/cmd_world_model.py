"""World Model commands — manage and run physics simulation models."""

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


@click.group("world-model")
def world_model_group():
    """World Model sandbox (MuJoCo) operations."""


@world_model_group.command("create")
@click.option("--name", required=True, help="Model name.")
@click.option("--description", default=None, help="Model description.")
@click.option("--model-type", default=None, help="Model type (e.g. mujoco, custom).")
@click.option("--mujoco-xml", default=None, help="Path or inline MuJoCo XML definition.")
def create(name, description, model_type, mujoco_xml):
    """Create a new world model."""
    payload = {"name": name, **_params(description=description, model_type=model_type, mujoco_xml=mujoco_xml)}
    try:
        _output(_run(client.post("/api/world-models", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@world_model_group.command("list")
@click.option("--status", default=None, help="Filter by model status.")
@click.option("--model-type", default=None, help="Filter by model type.")
def list_models(status, model_type):
    """List world models."""
    try:
        _output(_run(client.get(
            "/api/world-models",
            params=_params(status=status, model_type=model_type),
        )))
    except SwarmForgeError as e:
        _handle_error(e)


@world_model_group.command("get")
@click.argument("model_id")
def get(model_id):
    """Get a world model by ID."""
    try:
        _output(_run(client.get(f"/api/world-models/{model_id}")))
    except SwarmForgeError as e:
        _handle_error(e)


@world_model_group.command("delete")
@click.argument("model_id")
def delete(model_id):
    """Delete a world model."""
    try:
        _output(_run(client.delete(f"/api/world-models/{model_id}")))
        console.print(f"[green]World model {model_id} deleted.[/green]")
    except SwarmForgeError as e:
        _handle_error(e)


@world_model_group.command("start")
@click.argument("model_id")
@click.option("--max-steps", default=None, type=int, help="Maximum simulation steps.")
def start(model_id, max_steps):
    """Start a world model simulation."""
    payload = _params(max_steps=max_steps)
    try:
        _output(_run(client.post(f"/api/world-models/{model_id}/start", json=payload or {})))
    except SwarmForgeError as e:
        _handle_error(e)


@world_model_group.command("pause")
@click.argument("model_id")
def pause(model_id):
    """Pause a running simulation."""
    try:
        _output(_run(client.post(f"/api/world-models/{model_id}/pause", json={})))
    except SwarmForgeError as e:
        _handle_error(e)


@world_model_group.command("step")
@click.argument("model_id")
def step(model_id):
    """Advance the simulation by one step."""
    try:
        _output(_run(client.post(f"/api/world-models/{model_id}/step", json={})))
    except SwarmForgeError as e:
        _handle_error(e)


@world_model_group.command("reset")
@click.argument("model_id")
def reset(model_id):
    """Reset a simulation to its initial state."""
    try:
        _output(_run(client.post(f"/api/world-models/{model_id}/reset", json={})))
    except SwarmForgeError as e:
        _handle_error(e)


@world_model_group.command("events")
@click.argument("model_id")
@click.option("--limit", default=None, type=int, help="Maximum number of events.")
def events(model_id, limit):
    """List simulation events for a world model."""
    try:
        _output(_run(client.get(
            f"/api/world-models/{model_id}/events",
            params=_params(limit=limit),
        )))
    except SwarmForgeError as e:
        _handle_error(e)
