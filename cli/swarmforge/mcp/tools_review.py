"""MCP tools for review operations."""

import json
from mcp.types import Tool, TextContent

from ..client import client, SwarmForgeError

TOOLS = []


def _text(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _error(e: SwarmForgeError) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error {e.status}: {e}")]


# ---------------------------------------------------------------------------
# review_create
# ---------------------------------------------------------------------------

async def _review_create(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {"pr_url": arguments["pr_url"]}
        if "config" in arguments:
            body["config"] = arguments["config"]
        if "template_id" in arguments:
            body["template_id"] = arguments["template_id"]
        result = await client.post("/api/reviews", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="review_create",
        description="Create a new code review for a pull request URL.",
        inputSchema={
            "type": "object",
            "properties": {
                "pr_url": {
                    "type": "string",
                    "description": "Pull-request URL to review (required).",
                },
                "config": {
                    "type": "object",
                    "description": "Optional review configuration overrides.",
                },
                "template_id": {
                    "type": "string",
                    "description": "Optional template ID to use for this review.",
                },
            },
            "required": ["pr_url"],
        },
    ),
    _review_create,
))


# ---------------------------------------------------------------------------
# review_list
# ---------------------------------------------------------------------------

async def _review_list(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "status": arguments.get("status"),
            "repo": arguments.get("repo"),
            "platform": arguments.get("platform"),
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get("/api/reviews", params=params or None)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="review_list",
        description="List reviews with optional filters.",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by review status."},
                "repo": {"type": "string", "description": "Filter by repository name."},
                "platform": {"type": "string", "description": "Filter by platform (github, gitlab, etc)."},
                "limit": {"type": "integer", "description": "Maximum number of results."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": [],
        },
    ),
    _review_list,
))


# ---------------------------------------------------------------------------
# review_get
# ---------------------------------------------------------------------------

async def _review_get(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/reviews/{arguments['review_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="review_get",
        description="Get details of a specific review by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "review_id": {"type": "string", "description": "Review ID."},
            },
            "required": ["review_id"],
        },
    ),
    _review_get,
))


# ---------------------------------------------------------------------------
# review_cancel
# ---------------------------------------------------------------------------

async def _review_cancel(arguments: dict) -> list[TextContent]:
    try:
        result = await client.delete(f"/api/reviews/{arguments['review_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="review_cancel",
        description="Cancel (delete) a review by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "review_id": {"type": "string", "description": "Review ID to cancel."},
            },
            "required": ["review_id"],
        },
    ),
    _review_cancel,
))


# ---------------------------------------------------------------------------
# review_findings
# ---------------------------------------------------------------------------

async def _review_findings(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "severity": arguments.get("severity"),
            "agent_role": arguments.get("agent_role"),
        }.items() if v is not None}
        result = await client.get(
            f"/api/reviews/{arguments['review_id']}/findings",
            params=params or None,
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="review_findings",
        description="Get findings for a review, optionally filtered by severity or agent role.",
        inputSchema={
            "type": "object",
            "properties": {
                "review_id": {"type": "string", "description": "Review ID."},
                "severity": {"type": "string", "description": "Filter findings by severity (critical, high, medium, low)."},
                "agent_role": {"type": "string", "description": "Filter findings by the agent role that produced them."},
            },
            "required": ["review_id"],
        },
    ),
    _review_findings,
))


# ---------------------------------------------------------------------------
# review_timeline
# ---------------------------------------------------------------------------

async def _review_timeline(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/reviews/{arguments['review_id']}/timeline")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="review_timeline",
        description="Get the event timeline for a review.",
        inputSchema={
            "type": "object",
            "properties": {
                "review_id": {"type": "string", "description": "Review ID."},
            },
            "required": ["review_id"],
        },
    ),
    _review_timeline,
))


# ---------------------------------------------------------------------------
# review_post_comments
# ---------------------------------------------------------------------------

async def _review_post_comments(arguments: dict) -> list[TextContent]:
    try:
        params = {}
        if "severity_threshold" in arguments:
            params["severity_threshold"] = arguments["severity_threshold"]
        result = await client.post(
            f"/api/reviews/{arguments['review_id']}/post-to-github",
            params=params or None,
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="review_post_comments",
        description="Post review findings as comments to GitHub.",
        inputSchema={
            "type": "object",
            "properties": {
                "review_id": {"type": "string", "description": "Review ID."},
                "severity_threshold": {
                    "type": "string",
                    "description": "Only post findings at or above this severity (critical, high, medium, low).",
                },
            },
            "required": ["review_id"],
        },
    ),
    _review_post_comments,
))
