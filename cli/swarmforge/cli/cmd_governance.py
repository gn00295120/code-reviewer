"""Governance commands — DAO proposals and voting."""

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


@click.group("governance")
def governance_group():
    """DAO governance proposal operations."""


@governance_group.command("create")
@click.argument("company_id")
@click.option("--title", required=True, help="Proposal title.")
@click.option("--description", required=True, help="Proposal description.")
@click.option("--type", "proposal_type", required=True, help="Proposal type (e.g. rule_change, budget).")
@click.option("--changes", required=True, help="JSON-encoded changes object.")
def create(company_id, title, description, proposal_type, changes):
    """Create a governance proposal for a company."""
    try:
        changes_obj = json.loads(changes)
    except json.JSONDecodeError as exc:
        console.print(f"[red]Invalid JSON for --changes:[/red] {exc}")
        raise SystemExit(1)
    payload = {
        "company_id": company_id,
        "title": title,
        "description": description,
        "type": proposal_type,
        "changes": changes_obj,
    }
    try:
        _output(_run(client.post("/api/governance/proposals", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@governance_group.command("list")
@click.argument("company_id")
@click.option("--status", default=None, help="Filter by proposal status.")
@click.option("--type", "proposal_type", default=None, help="Filter by proposal type.")
def list_proposals(company_id, status, proposal_type):
    """List governance proposals for a company."""
    try:
        _output(_run(client.get(
            f"/api/governance/proposals",
            params=_params(company_id=company_id, status=status, type=proposal_type),
        )))
    except SwarmForgeError as e:
        _handle_error(e)


@governance_group.command("get")
@click.argument("proposal_id")
def get(proposal_id):
    """Get a governance proposal by ID."""
    try:
        _output(_run(client.get(f"/api/governance/proposals/{proposal_id}")))
    except SwarmForgeError as e:
        _handle_error(e)


@governance_group.command("vote")
@click.argument("proposal_id")
@click.option("--voter-id", required=True, help="ID of the voter.")
@click.option(
    "--vote",
    "vote_choice",
    required=True,
    type=click.Choice(["for", "against", "abstain"], case_sensitive=False),
    help="Vote choice.",
)
@click.option("--reason", default=None, help="Optional reason for the vote.")
def vote(proposal_id, voter_id, vote_choice, reason):
    """Cast a vote on a proposal."""
    payload = {"voter_id": voter_id, "vote": vote_choice, **_params(reason=reason)}
    try:
        _output(_run(client.post(f"/api/governance/proposals/{proposal_id}/vote", json=payload)))
    except SwarmForgeError as e:
        _handle_error(e)


@governance_group.command("execute")
@click.argument("proposal_id")
def execute(proposal_id):
    """Execute an approved proposal."""
    try:
        _output(_run(client.post(f"/api/governance/proposals/{proposal_id}/execute", json={})))
    except SwarmForgeError as e:
        _handle_error(e)


@governance_group.command("close")
@click.argument("proposal_id")
def close(proposal_id):
    """Close a proposal (ends voting without execution)."""
    try:
        _output(_run(client.post(f"/api/governance/proposals/{proposal_id}/close", json={})))
    except SwarmForgeError as e:
        _handle_error(e)
