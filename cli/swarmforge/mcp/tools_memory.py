"""MCP tools for agent memory operations."""

import json
from mcp.types import Tool, TextContent

from ..client import client, SwarmForgeError

TOOLS = []


def _text(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _error(e: SwarmForgeError) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error {e.status}: {e}")]


# ---------------------------------------------------------------------------
# memory_list
# ---------------------------------------------------------------------------

async def _memory_list(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "agent_role": arguments.get("agent_role"),
            "memory_type": arguments.get("memory_type"),
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get("/api/memory", params=params or None)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="memory_list",
        description="List agent memory entries with optional filters.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_role": {"type": "string", "description": "Filter by agent role."},
                "memory_type": {"type": "string", "description": "Filter by memory type (episodic, semantic, procedural)."},
                "limit": {"type": "integer", "description": "Maximum number of results."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": [],
        },
    ),
    _memory_list,
))


# ---------------------------------------------------------------------------
# memory_search
# ---------------------------------------------------------------------------

async def _memory_search(arguments: dict) -> list[TextContent]:
    try:
        params: dict = {"q": arguments["q"]}
        if "agent_role" in arguments:
            params["agent_role"] = arguments["agent_role"]
        if "limit" in arguments:
            params["limit"] = arguments["limit"]
        result = await client.get("/api/memory/search", params=params)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="memory_search",
        description="Full-text search across agent memory entries.",
        inputSchema={
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Search query string (required)."},
                "agent_role": {"type": "string", "description": "Restrict search to a specific agent role."},
                "limit": {"type": "integer", "description": "Maximum number of results."},
            },
            "required": ["q"],
        },
    ),
    _memory_search,
))


# ---------------------------------------------------------------------------
# memory_get
# ---------------------------------------------------------------------------

async def _memory_get(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/memory/{arguments['memory_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="memory_get",
        description="Get a specific memory entry by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "memory_id": {"type": "string", "description": "Memory entry ID."},
            },
            "required": ["memory_id"],
        },
    ),
    _memory_get,
))


# ---------------------------------------------------------------------------
# memory_create
# ---------------------------------------------------------------------------

async def _memory_create(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {
            "agent_role": arguments["agent_role"],
            "memory_type": arguments["memory_type"],
            "content": arguments["content"],
        }
        if "metadata" in arguments:
            body["metadata"] = arguments["metadata"]
        result = await client.post("/api/memory", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="memory_create",
        description="Create a new agent memory entry.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_role": {"type": "string", "description": "Role of the agent that owns this memory (required)."},
                "memory_type": {
                    "type": "string",
                    "description": "Memory type: episodic, semantic, or procedural (required).",
                },
                "content": {"type": "string", "description": "Memory content text (required)."},
                "metadata": {"type": "object", "description": "Optional key-value metadata."},
            },
            "required": ["agent_role", "memory_type", "content"],
        },
    ),
    _memory_create,
))


# ---------------------------------------------------------------------------
# memory_delete
# ---------------------------------------------------------------------------

async def _memory_delete(arguments: dict) -> list[TextContent]:
    try:
        result = await client.delete(f"/api/memory/{arguments['memory_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="memory_delete",
        description="Delete a memory entry by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "memory_id": {"type": "string", "description": "Memory entry ID to delete."},
            },
            "required": ["memory_id"],
        },
    ),
    _memory_delete,
))


# ---------------------------------------------------------------------------
# memory_consolidate
# ---------------------------------------------------------------------------

async def _memory_consolidate(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {}
        if "agent_role" in arguments:
            body["agent_role"] = arguments["agent_role"]
        result = await client.post("/api/memory/consolidate", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="memory_consolidate",
        description="Trigger memory consolidation to compress and deduplicate entries.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_role": {
                    "type": "string",
                    "description": "Only consolidate memory for this agent role. Omit to consolidate all.",
                },
            },
            "required": [],
        },
    ),
    _memory_consolidate,
))
