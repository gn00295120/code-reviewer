"""MCP tools for misc operations: stats, health, org templates, deploy."""

import json
from mcp.types import Tool, TextContent

from ..client import client, SwarmForgeError

TOOLS = []


def _text(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _error(e: SwarmForgeError) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error {e.status}: {e}")]


# ---------------------------------------------------------------------------
# stats_queue
# ---------------------------------------------------------------------------

async def _stats_queue(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get("/api/stats/queue")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="stats_queue",
        description="Get current review queue statistics.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    _stats_queue,
))


# ---------------------------------------------------------------------------
# stats_overview
# ---------------------------------------------------------------------------

async def _stats_overview(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get("/api/stats/overview")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="stats_overview",
        description="Get a high-level platform overview with aggregate statistics.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    _stats_overview,
))


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------

async def _health_check(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get("/health")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="health_check",
        description="Check whether the SwarmForge API is reachable and healthy.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    _health_check,
))


# ---------------------------------------------------------------------------
# org_template_list
# ---------------------------------------------------------------------------

async def _org_template_list(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get("/api/org-templates")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_template_list",
        description="List available built-in organisation templates.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    _org_template_list,
))


# ---------------------------------------------------------------------------
# org_template_instantiate
# ---------------------------------------------------------------------------

async def _org_template_instantiate(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/org-templates/{arguments['name']}/instantiate")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_template_instantiate",
        description="Instantiate a built-in organisation template to create a new org.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Template name to instantiate (required).",
                },
            },
            "required": ["name"],
        },
    ),
    _org_template_instantiate,
))


# ---------------------------------------------------------------------------
# org_deploy
# ---------------------------------------------------------------------------

async def _org_deploy(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/orgs/{arguments['org_id']}/deploy")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_deploy",
        description="Deploy an organisation, starting all of its agents.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID to deploy."},
            },
            "required": ["org_id"],
        },
    ),
    _org_deploy,
))


# ---------------------------------------------------------------------------
# org_deploy_status
# ---------------------------------------------------------------------------

async def _org_deploy_status(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/orgs/{arguments['org_id']}/status")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_deploy_status",
        description="Get the current deployment status of an organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID."},
            },
            "required": ["org_id"],
        },
    ),
    _org_deploy_status,
))


# ---------------------------------------------------------------------------
# org_stop
# ---------------------------------------------------------------------------

async def _org_stop(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/orgs/{arguments['org_id']}/stop")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_stop",
        description="Stop all running agents in a deployed organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID to stop."},
            },
            "required": ["org_id"],
        },
    ),
    _org_stop,
))
