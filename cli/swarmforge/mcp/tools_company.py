"""MCP tools for agent company operations."""

import json
from mcp.types import Tool, TextContent

from ..client import client, SwarmForgeError

TOOLS = []


def _text(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _error(e: SwarmForgeError) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error {e.status}: {e}")]


# ---------------------------------------------------------------------------
# company_create
# ---------------------------------------------------------------------------

async def _company_create(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {"name": arguments["name"]}
        if "description" in arguments:
            body["description"] = arguments["description"]
        if "owner" in arguments:
            body["owner"] = arguments["owner"]
        result = await client.post("/api/companies", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="company_create",
        description="Create a new agent company.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Company name (required)."},
                "description": {"type": "string", "description": "Company description."},
                "owner": {"type": "string", "description": "Owner user ID."},
            },
            "required": ["name"],
        },
    ),
    _company_create,
))


# ---------------------------------------------------------------------------
# company_list
# ---------------------------------------------------------------------------

async def _company_list(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "status": arguments.get("status"),
            "owner": arguments.get("owner"),
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get("/api/companies", params=params or None)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="company_list",
        description="List agent companies with optional filters.",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by status (active, paused, inactive)."},
                "owner": {"type": "string", "description": "Filter by owner user ID."},
                "limit": {"type": "integer", "description": "Maximum number of results."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": [],
        },
    ),
    _company_list,
))


# ---------------------------------------------------------------------------
# company_get
# ---------------------------------------------------------------------------

async def _company_get(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/companies/{arguments['company_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="company_get",
        description="Get details of a specific agent company.",
        inputSchema={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "Company ID."},
            },
            "required": ["company_id"],
        },
    ),
    _company_get,
))


# ---------------------------------------------------------------------------
# company_update
# ---------------------------------------------------------------------------

async def _company_update(arguments: dict) -> list[TextContent]:
    try:
        body = {k: v for k, v in {
            "name": arguments.get("name"),
            "description": arguments.get("description"),
        }.items() if v is not None}
        result = await client.put(f"/api/companies/{arguments['company_id']}", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="company_update",
        description="Update an agent company's name or description.",
        inputSchema={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "Company ID to update."},
                "name": {"type": "string", "description": "New company name."},
                "description": {"type": "string", "description": "New description."},
            },
            "required": ["company_id"],
        },
    ),
    _company_update,
))


# ---------------------------------------------------------------------------
# company_activate
# ---------------------------------------------------------------------------

async def _company_activate(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/companies/{arguments['company_id']}/activate")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="company_activate",
        description="Activate a paused or inactive agent company.",
        inputSchema={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "Company ID to activate."},
            },
            "required": ["company_id"],
        },
    ),
    _company_activate,
))


# ---------------------------------------------------------------------------
# company_pause
# ---------------------------------------------------------------------------

async def _company_pause(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/companies/{arguments['company_id']}/pause")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="company_pause",
        description="Pause an active agent company.",
        inputSchema={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "Company ID to pause."},
            },
            "required": ["company_id"],
        },
    ),
    _company_pause,
))


# ---------------------------------------------------------------------------
# company_budget
# ---------------------------------------------------------------------------

async def _company_budget(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/companies/{arguments['company_id']}/budget")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="company_budget",
        description="Get budget and spend information for an agent company.",
        inputSchema={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "Company ID."},
            },
            "required": ["company_id"],
        },
    ),
    _company_budget,
))


# ---------------------------------------------------------------------------
# company_agent_list
# ---------------------------------------------------------------------------

async def _company_agent_list(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/companies/{arguments['company_id']}/agents")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="company_agent_list",
        description="List all agents belonging to an agent company.",
        inputSchema={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "Company ID."},
            },
            "required": ["company_id"],
        },
    ),
    _company_agent_list,
))


# ---------------------------------------------------------------------------
# company_agent_add
# ---------------------------------------------------------------------------

async def _company_agent_add(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {
            "name": arguments["name"],
            "role": arguments["role"],
        }
        if "model" in arguments:
            body["model"] = arguments["model"]
        if "system_prompt" in arguments:
            body["system_prompt"] = arguments["system_prompt"]
        result = await client.post(
            f"/api/companies/{arguments['company_id']}/agents",
            json=body,
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="company_agent_add",
        description="Add a new agent to an agent company.",
        inputSchema={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "Company ID."},
                "name": {"type": "string", "description": "Agent name (required)."},
                "role": {"type": "string", "description": "Agent role (required)."},
                "model": {"type": "string", "description": "LLM model identifier."},
                "system_prompt": {"type": "string", "description": "Custom system prompt for the agent."},
            },
            "required": ["company_id", "name", "role"],
        },
    ),
    _company_agent_add,
))


# ---------------------------------------------------------------------------
# company_agent_update
# ---------------------------------------------------------------------------

async def _company_agent_update(arguments: dict) -> list[TextContent]:
    try:
        body = {k: v for k, v in {
            "name": arguments.get("name"),
            "role": arguments.get("role"),
            "model": arguments.get("model"),
        }.items() if v is not None}
        result = await client.put(
            f"/api/companies/{arguments['company_id']}/agents/{arguments['agent_id']}",
            json=body,
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="company_agent_update",
        description="Update an agent's name, role, or model within a company.",
        inputSchema={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "Company ID."},
                "agent_id": {"type": "string", "description": "Agent ID to update."},
                "name": {"type": "string", "description": "New agent name."},
                "role": {"type": "string", "description": "New agent role."},
                "model": {"type": "string", "description": "New LLM model identifier."},
            },
            "required": ["company_id", "agent_id"],
        },
    ),
    _company_agent_update,
))


# ---------------------------------------------------------------------------
# company_agent_remove
# ---------------------------------------------------------------------------

async def _company_agent_remove(arguments: dict) -> list[TextContent]:
    try:
        result = await client.delete(
            f"/api/companies/{arguments['company_id']}/agents/{arguments['agent_id']}"
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="company_agent_remove",
        description="Remove an agent from an agent company.",
        inputSchema={
            "type": "object",
            "properties": {
                "company_id": {"type": "string", "description": "Company ID."},
                "agent_id": {"type": "string", "description": "Agent ID to remove."},
            },
            "required": ["company_id", "agent_id"],
        },
    ),
    _company_agent_remove,
))
