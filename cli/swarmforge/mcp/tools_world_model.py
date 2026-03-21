"""MCP tools for world-model / simulation operations."""

import json
from mcp.types import Tool, TextContent

from ..client import client, SwarmForgeError

TOOLS = []


def _text(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _error(e: SwarmForgeError) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error {e.status}: {e}")]


# ---------------------------------------------------------------------------
# world_model_create
# ---------------------------------------------------------------------------

async def _world_model_create(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {"name": arguments["name"]}
        for opt in ("description", "model_type", "mujoco_xml"):
            if opt in arguments:
                body[opt] = arguments[opt]
        result = await client.post("/api/world-models", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="world_model_create",
        description="Create a new world model / simulation environment.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "World model name (required)."},
                "description": {"type": "string", "description": "Human-readable description."},
                "model_type": {
                    "type": "string",
                    "description": "Model type (e.g. mujoco, custom).",
                },
                "mujoco_xml": {
                    "type": "string",
                    "description": "MuJoCo XML definition string (used when model_type is mujoco).",
                },
            },
            "required": ["name"],
        },
    ),
    _world_model_create,
))


# ---------------------------------------------------------------------------
# world_model_list
# ---------------------------------------------------------------------------

async def _world_model_list(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "status": arguments.get("status"),
            "model_type": arguments.get("model_type"),
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get("/api/world-models", params=params or None)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="world_model_list",
        description="List world models with optional filters.",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by status (idle, running, paused)."},
                "model_type": {"type": "string", "description": "Filter by model type."},
                "limit": {"type": "integer", "description": "Maximum number of results."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": [],
        },
    ),
    _world_model_list,
))


# ---------------------------------------------------------------------------
# world_model_get
# ---------------------------------------------------------------------------

async def _world_model_get(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/world-models/{arguments['model_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="world_model_get",
        description="Get details of a specific world model.",
        inputSchema={
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "World model ID."},
            },
            "required": ["model_id"],
        },
    ),
    _world_model_get,
))


# ---------------------------------------------------------------------------
# world_model_delete
# ---------------------------------------------------------------------------

async def _world_model_delete(arguments: dict) -> list[TextContent]:
    try:
        result = await client.delete(f"/api/world-models/{arguments['model_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="world_model_delete",
        description="Delete a world model.",
        inputSchema={
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "World model ID to delete."},
            },
            "required": ["model_id"],
        },
    ),
    _world_model_delete,
))


# ---------------------------------------------------------------------------
# world_model_start
# ---------------------------------------------------------------------------

async def _world_model_start(arguments: dict) -> list[TextContent]:
    try:
        params = {}
        if "max_steps" in arguments:
            params["max_steps"] = arguments["max_steps"]
        result = await client.post(
            f"/api/world-models/{arguments['model_id']}/start",
            params=params or None,
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="world_model_start",
        description="Start a world model simulation.",
        inputSchema={
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "World model ID to start."},
                "max_steps": {
                    "type": "integer",
                    "description": "Maximum simulation steps before auto-stop.",
                },
            },
            "required": ["model_id"],
        },
    ),
    _world_model_start,
))


# ---------------------------------------------------------------------------
# world_model_pause
# ---------------------------------------------------------------------------

async def _world_model_pause(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/world-models/{arguments['model_id']}/pause")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="world_model_pause",
        description="Pause a running world model simulation.",
        inputSchema={
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "World model ID to pause."},
            },
            "required": ["model_id"],
        },
    ),
    _world_model_pause,
))


# ---------------------------------------------------------------------------
# world_model_step
# ---------------------------------------------------------------------------

async def _world_model_step(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/world-models/{arguments['model_id']}/step")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="world_model_step",
        description="Advance a paused world model simulation by one step.",
        inputSchema={
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "World model ID to step."},
            },
            "required": ["model_id"],
        },
    ),
    _world_model_step,
))


# ---------------------------------------------------------------------------
# world_model_reset
# ---------------------------------------------------------------------------

async def _world_model_reset(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/world-models/{arguments['model_id']}/reset")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="world_model_reset",
        description="Reset a world model simulation to its initial state.",
        inputSchema={
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "World model ID to reset."},
            },
            "required": ["model_id"],
        },
    ),
    _world_model_reset,
))


# ---------------------------------------------------------------------------
# world_model_events
# ---------------------------------------------------------------------------

async def _world_model_events(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get(
            f"/api/world-models/{arguments['model_id']}/events",
            params=params or None,
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="world_model_events",
        description="Get simulation events emitted by a world model.",
        inputSchema={
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "World model ID."},
                "limit": {"type": "integer", "description": "Maximum number of events to return."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": ["model_id"],
        },
    ),
    _world_model_events,
))
