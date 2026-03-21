"""MCP tools for DAO governance / proposal operations."""

import json
from mcp.types import Tool, TextContent

from ..client import client, SwarmForgeError

TOOLS = []


def _text(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _error(e: SwarmForgeError) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error {e.status}: {e}")]


# ---------------------------------------------------------------------------
# proposal_create
# ---------------------------------------------------------------------------

async def _proposal_create(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {
            "title": arguments["title"],
            "description": arguments["description"],
            "proposal_type": arguments["proposal_type"],
            "proposed_changes": arguments["proposed_changes"],
        }
        result = await client.post(
            f"/api/companies/{arguments['company_id']}/proposals",
            json=body,
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="proposal_create",
        description="Create a governance proposal for an agent company.",
        inputSchema={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "Company ID to create the proposal in."},
                "title": {"type": "string", "description": "Proposal title (required)."},
                "description": {"type": "string", "description": "Proposal description (required)."},
                "proposal_type": {
                    "type": "string",
                    "description": "Type of proposal (e.g. config_change, agent_add, budget_change) — required.",
                },
                "proposed_changes": {
                    "type": "object",
                    "description": "Structured object describing the proposed changes (required).",
                },
            },
            "required": ["company_id", "title", "description", "proposal_type", "proposed_changes"],
        },
    ),
    _proposal_create,
))


# ---------------------------------------------------------------------------
# proposal_list
# ---------------------------------------------------------------------------

async def _proposal_list(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "status": arguments.get("status"),
            "proposal_type": arguments.get("proposal_type"),
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get(
            f"/api/companies/{arguments['company_id']}/proposals",
            params=params or None,
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="proposal_list",
        description="List governance proposals for an agent company.",
        inputSchema={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "Company ID."},
                "status": {"type": "string", "description": "Filter by status (open, passed, rejected, executed)."},
                "proposal_type": {"type": "string", "description": "Filter by proposal type."},
                "limit": {"type": "integer", "description": "Maximum number of results."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": ["company_id"],
        },
    ),
    _proposal_list,
))


# ---------------------------------------------------------------------------
# proposal_get
# ---------------------------------------------------------------------------

async def _proposal_get(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/proposals/{arguments['proposal_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="proposal_get",
        description="Get details of a specific governance proposal.",
        inputSchema={
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string", "description": "Proposal ID."},
            },
            "required": ["proposal_id"],
        },
    ),
    _proposal_get,
))


# ---------------------------------------------------------------------------
# proposal_vote
# ---------------------------------------------------------------------------

async def _proposal_vote(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {
            "voter_id": arguments["voter_id"],
            "vote": arguments["vote"],
        }
        if "reason" in arguments:
            body["reason"] = arguments["reason"]
        result = await client.post(
            f"/api/proposals/{arguments['proposal_id']}/vote",
            json=body,
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="proposal_vote",
        description="Cast a vote on a governance proposal.",
        inputSchema={
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string", "description": "Proposal ID."},
                "voter_id": {"type": "string", "description": "ID of the voter (agent or user) — required."},
                "vote": {
                    "type": "string",
                    "description": "Vote value: 'yes', 'no', or 'abstain' (required).",
                    "enum": ["yes", "no", "abstain"],
                },
                "reason": {"type": "string", "description": "Optional reason for the vote."},
            },
            "required": ["proposal_id", "voter_id", "vote"],
        },
    ),
    _proposal_vote,
))


# ---------------------------------------------------------------------------
# proposal_execute
# ---------------------------------------------------------------------------

async def _proposal_execute(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/proposals/{arguments['proposal_id']}/execute")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="proposal_execute",
        description="Execute a passed governance proposal, applying its proposed changes.",
        inputSchema={
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string", "description": "Proposal ID to execute."},
            },
            "required": ["proposal_id"],
        },
    ),
    _proposal_execute,
))


# ---------------------------------------------------------------------------
# proposal_close
# ---------------------------------------------------------------------------

async def _proposal_close(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/proposals/{arguments['proposal_id']}/close")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="proposal_close",
        description="Close a governance proposal without executing it.",
        inputSchema={
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string", "description": "Proposal ID to close."},
            },
            "required": ["proposal_id"],
        },
    ),
    _proposal_close,
))
