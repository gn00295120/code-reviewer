"""MCP tools for science engine / experiment operations."""

import json
from mcp.types import Tool, TextContent

from ..client import client, SwarmForgeError

TOOLS = []


def _text(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _error(e: SwarmForgeError) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error {e.status}: {e}")]


# ---------------------------------------------------------------------------
# experiment_create
# ---------------------------------------------------------------------------

async def _experiment_create(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {
            "title": arguments["title"],
            "hypothesis": arguments["hypothesis"],
        }
        for opt in ("company_id", "parameters"):
            if opt in arguments:
                body[opt] = arguments[opt]
        result = await client.post("/api/experiments", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="experiment_create",
        description="Create a new science experiment.",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Experiment title (required)."},
                "hypothesis": {"type": "string", "description": "Hypothesis to test (required)."},
                "company_id": {"type": "string", "description": "Optional owning company ID."},
                "parameters": {
                    "type": "object",
                    "description": "Initial experiment parameter configuration.",
                },
            },
            "required": ["title", "hypothesis"],
        },
    ),
    _experiment_create,
))


# ---------------------------------------------------------------------------
# experiment_list
# ---------------------------------------------------------------------------

async def _experiment_list(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "status": arguments.get("status"),
            "company_id": arguments.get("company_id"),
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get("/api/experiments", params=params or None)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="experiment_list",
        description="List experiments with optional filters.",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by status (draft, running, completed, failed)."},
                "company_id": {"type": "string", "description": "Filter by owning company ID."},
                "limit": {"type": "integer", "description": "Maximum number of results."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": [],
        },
    ),
    _experiment_list,
))


# ---------------------------------------------------------------------------
# experiment_get
# ---------------------------------------------------------------------------

async def _experiment_get(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/experiments/{arguments['experiment_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="experiment_get",
        description="Get details of a specific experiment.",
        inputSchema={
            "type": "object",
            "properties": {
                "experiment_id": {"type": "string", "description": "Experiment ID."},
            },
            "required": ["experiment_id"],
        },
    ),
    _experiment_get,
))


# ---------------------------------------------------------------------------
# experiment_run
# ---------------------------------------------------------------------------

async def _experiment_run(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {}
        if "parameters" in arguments:
            body["parameters"] = arguments["parameters"]
        result = await client.post(
            f"/api/experiments/{arguments['experiment_id']}/run",
            json=body,
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="experiment_run",
        description="Start a new run of an experiment, optionally overriding parameters.",
        inputSchema={
            "type": "object",
            "properties": {
                "experiment_id": {"type": "string", "description": "Experiment ID to run."},
                "parameters": {
                    "type": "object",
                    "description": "Parameter overrides for this specific run.",
                },
            },
            "required": ["experiment_id"],
        },
    ),
    _experiment_run,
))


# ---------------------------------------------------------------------------
# experiment_runs
# ---------------------------------------------------------------------------

async def _experiment_runs(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/experiments/{arguments['experiment_id']}/runs")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="experiment_runs",
        description="List all runs for an experiment.",
        inputSchema={
            "type": "object",
            "properties": {
                "experiment_id": {"type": "string", "description": "Experiment ID."},
            },
            "required": ["experiment_id"],
        },
    ),
    _experiment_runs,
))


# ---------------------------------------------------------------------------
# experiment_analyze
# ---------------------------------------------------------------------------

async def _experiment_analyze(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/experiments/{arguments['experiment_id']}/analyze")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="experiment_analyze",
        description="Trigger analysis of experiment results.",
        inputSchema={
            "type": "object",
            "properties": {
                "experiment_id": {"type": "string", "description": "Experiment ID to analyze."},
            },
            "required": ["experiment_id"],
        },
    ),
    _experiment_analyze,
))


# ---------------------------------------------------------------------------
# experiment_publish
# ---------------------------------------------------------------------------

async def _experiment_publish(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/experiments/{arguments['experiment_id']}/publish")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="experiment_publish",
        description="Publish experiment results to the community.",
        inputSchema={
            "type": "object",
            "properties": {
                "experiment_id": {"type": "string", "description": "Experiment ID to publish."},
            },
            "required": ["experiment_id"],
        },
    ),
    _experiment_publish,
))
