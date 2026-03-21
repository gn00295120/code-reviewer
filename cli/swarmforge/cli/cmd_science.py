"""Science commands — manage and run agent experiments."""

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


@click.group("science")
def science_group():
    """Agent science experiment operations."""


@science_group.command("create")
@click.option("--title", required=True, help="Experiment title.")
@click.option("--hypothesis", required=True, help="Hypothesis being tested.")
@click.option("--company-id", default=None, help="Associate with a company.")
@click.option("--parameters", default=None, help="JSON-encoded experiment parameters.")
def create(title, hypothesis, company_id, parameters):
    """Create a new experiment."""
    payload = {"title": title, "hypothesis": hypothesis, **_params(company_id=company_id)}
    if parameters:
        try:
            payload["parameters"] = json.loads(parameters)
        except json.JSONDecodeError as exc:
            console.print(f"[red]Invalid JSON for --parameters:[/red] {exc}")
            raise SystemExit(1)
    try:
        _output(_run(client.post("/api/science/experiments", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@science_group.command("list")
@click.option("--status", default=None, help="Filter by experiment status.")
@click.option("--company-id", default=None, help="Filter by company ID.")
def list_experiments(status, company_id):
    """List experiments."""
    try:
        _output(_run(client.get(
            "/api/science/experiments",
            params=_params(status=status, company_id=company_id),
        )))
    except SwarmForgeError as e:
        _handle_error(e)


@science_group.command("get")
@click.argument("experiment_id")
def get(experiment_id):
    """Get an experiment by ID."""
    try:
        _output(_run(client.get(f"/api/science/experiments/{experiment_id}")))
    except SwarmForgeError as e:
        _handle_error(e)


@science_group.command("run")
@click.argument("experiment_id")
@click.option("--parameters", default=None, help="JSON-encoded run-time parameter overrides.")
def run(experiment_id, parameters):
    """Start a new run of an experiment."""
    payload = {}
    if parameters:
        try:
            payload["parameters"] = json.loads(parameters)
        except json.JSONDecodeError as exc:
            console.print(f"[red]Invalid JSON for --parameters:[/red] {exc}")
            raise SystemExit(1)
    try:
        _output(_run(client.post(f"/api/science/experiments/{experiment_id}/run", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@science_group.command("runs")
@click.argument("experiment_id")
def runs(experiment_id):
    """List all runs of an experiment."""
    try:
        _output(_run(client.get(f"/api/science/experiments/{experiment_id}/runs")))
    except SwarmForgeError as e:
        _handle_error(e)


@science_group.command("analyze")
@click.argument("experiment_id")
def analyze(experiment_id):
    """Trigger analysis of experiment results."""
    try:
        _output(_run(client.post(f"/api/science/experiments/{experiment_id}/analyze", json={})))
    except SwarmForgeError as e:
        _handle_error(e)


@science_group.command("publish")
@click.argument("experiment_id")
def publish(experiment_id):
    """Publish experiment findings to the community."""
    try:
        _output(_run(client.post(f"/api/science/experiments/{experiment_id}/publish", json={})))
    except SwarmForgeError as e:
        _handle_error(e)
