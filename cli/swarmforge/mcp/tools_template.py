"""MCP tools for review template operations."""

import json
from mcp.types import Tool, TextContent

from ..client import client, SwarmForgeError

TOOLS = []


def _text(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _error(e: SwarmForgeError) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error {e.status}: {e}")]


# ---------------------------------------------------------------------------
# template_list
# ---------------------------------------------------------------------------

async def _template_list(arguments: dict) -> list[TextContent]:
    try:
        params = {}
        if "created_by" in arguments:
            params["created_by"] = arguments["created_by"]
        result = await client.get("/api/templates", params=params or None)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="template_list",
        description="List all review templates, optionally filtered by creator.",
        inputSchema={
            "type": "object",
            "properties": {
                "created_by": {"type": "string", "description": "Filter templates by creator user ID."},
            },
            "required": [],
        },
    ),
    _template_list,
))


# ---------------------------------------------------------------------------
# template_create
# ---------------------------------------------------------------------------

async def _template_create(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {"name": arguments["name"]}
        if "description" in arguments:
            body["description"] = arguments["description"]
        if "rules" in arguments:
            body["rules"] = arguments["rules"]
        result = await client.post("/api/templates", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="template_create",
        description="Create a new review template.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Template name (required)."},
                "description": {"type": "string", "description": "Human-readable description."},
                "rules": {
                    "type": "object",
                    "description": "Template rules configuration.",
                },
            },
            "required": ["name"],
        },
    ),
    _template_create,
))


# ---------------------------------------------------------------------------
# template_get
# ---------------------------------------------------------------------------

async def _template_get(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/templates/{arguments['template_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="template_get",
        description="Get a review template by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "Template ID."},
            },
            "required": ["template_id"],
        },
    ),
    _template_get,
))


# ---------------------------------------------------------------------------
# template_update
# ---------------------------------------------------------------------------

async def _template_update(arguments: dict) -> list[TextContent]:
    try:
        body = {k: v for k, v in {
            "name": arguments.get("name"),
            "description": arguments.get("description"),
            "rules": arguments.get("rules"),
        }.items() if v is not None}
        result = await client.put(f"/api/templates/{arguments['template_id']}", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="template_update",
        description="Update an existing review template.",
        inputSchema={
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "Template ID to update."},
                "name": {"type": "string", "description": "New template name."},
                "description": {"type": "string", "description": "New description."},
                "rules": {"type": "object", "description": "Updated rules configuration."},
            },
            "required": ["template_id"],
        },
    ),
    _template_update,
))


# ---------------------------------------------------------------------------
# template_delete
# ---------------------------------------------------------------------------

async def _template_delete(arguments: dict) -> list[TextContent]:
    try:
        result = await client.delete(f"/api/templates/{arguments['template_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="template_delete",
        description="Delete a review template by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "Template ID to delete."},
            },
            "required": ["template_id"],
        },
    ),
    _template_delete,
))


# ---------------------------------------------------------------------------
# template_fork
# ---------------------------------------------------------------------------

async def _template_fork(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/templates/{arguments['template_id']}/fork")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="template_fork",
        description="Fork an existing review template to create a personal copy.",
        inputSchema={
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "Template ID to fork."},
            },
            "required": ["template_id"],
        },
    ),
    _template_fork,
))
