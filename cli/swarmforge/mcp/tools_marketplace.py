"""MCP tools for marketplace operations."""

import json
from mcp.types import Tool, TextContent

from ..client import client, SwarmForgeError

TOOLS = []


def _text(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _error(e: SwarmForgeError) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error {e.status}: {e}")]


# ---------------------------------------------------------------------------
# marketplace_browse
# ---------------------------------------------------------------------------

async def _marketplace_browse(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "q": arguments.get("q"),
            "listing_type": arguments.get("listing_type"),
            "tags": arguments.get("tags"),
            "sort": arguments.get("sort"),
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get("/api/marketplace", params=params or None)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="marketplace_browse",
        description="Browse the marketplace for published listings.",
        inputSchema={
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Search query."},
                "listing_type": {
                    "type": "string",
                    "description": "Filter by listing type (agent, template, org, tool).",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags.",
                },
                "sort": {
                    "type": "string",
                    "description": "Sort order (e.g. newest, popular, rating).",
                },
                "limit": {"type": "integer", "description": "Maximum number of results."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": [],
        },
    ),
    _marketplace_browse,
))


# ---------------------------------------------------------------------------
# marketplace_get
# ---------------------------------------------------------------------------

async def _marketplace_get(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/marketplace/{arguments['listing_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="marketplace_get",
        description="Get details of a specific marketplace listing.",
        inputSchema={
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "Marketplace listing ID."},
            },
            "required": ["listing_id"],
        },
    ),
    _marketplace_get,
))


# ---------------------------------------------------------------------------
# marketplace_publish
# ---------------------------------------------------------------------------

async def _marketplace_publish(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {
            "listing_type": arguments["listing_type"],
            "title": arguments["title"],
            "description": arguments["description"],
            "version": arguments["version"],
            "tags": arguments["tags"],
            "config": arguments["config"],
        }
        result = await client.post("/api/marketplace", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="marketplace_publish",
        description="Publish a new listing to the marketplace.",
        inputSchema={
            "type": "object",
            "properties": {
                "listing_type": {
                    "type": "string",
                    "description": "Type of listing: agent, template, org, or tool (required).",
                },
                "title": {"type": "string", "description": "Listing title (required)."},
                "description": {"type": "string", "description": "Listing description (required)."},
                "version": {"type": "string", "description": "Semantic version string, e.g. 1.0.0 (required)."},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tag list (required).",
                },
                "config": {
                    "type": "object",
                    "description": "Listing configuration payload (required).",
                },
            },
            "required": ["listing_type", "title", "description", "version", "tags", "config"],
        },
    ),
    _marketplace_publish,
))


# ---------------------------------------------------------------------------
# marketplace_update
# ---------------------------------------------------------------------------

async def _marketplace_update(arguments: dict) -> list[TextContent]:
    try:
        body = {k: v for k, v in {
            "title": arguments.get("title"),
            "description": arguments.get("description"),
            "version": arguments.get("version"),
            "tags": arguments.get("tags"),
        }.items() if v is not None}
        result = await client.put(f"/api/marketplace/{arguments['listing_id']}", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="marketplace_update",
        description="Update metadata on an existing marketplace listing.",
        inputSchema={
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "Marketplace listing ID to update."},
                "title": {"type": "string", "description": "New title."},
                "description": {"type": "string", "description": "New description."},
                "version": {"type": "string", "description": "New version string."},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Updated tag list.",
                },
            },
            "required": ["listing_id"],
        },
    ),
    _marketplace_update,
))


# ---------------------------------------------------------------------------
# marketplace_install
# ---------------------------------------------------------------------------

async def _marketplace_install(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/marketplace/{arguments['listing_id']}/install")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="marketplace_install",
        description="Install a marketplace listing into the current workspace.",
        inputSchema={
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "Marketplace listing ID to install."},
            },
            "required": ["listing_id"],
        },
    ),
    _marketplace_install,
))


# ---------------------------------------------------------------------------
# marketplace_rate
# ---------------------------------------------------------------------------

async def _marketplace_rate(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {"rating": arguments["rating"]}
        result = await client.post(
            f"/api/marketplace/{arguments['listing_id']}/rate",
            json=body,
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="marketplace_rate",
        description="Rate a marketplace listing (1-5 stars).",
        inputSchema={
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "Marketplace listing ID to rate."},
                "rating": {
                    "type": "integer",
                    "description": "Rating from 1 (lowest) to 5 (highest) — required.",
                    "minimum": 1,
                    "maximum": 5,
                },
            },
            "required": ["listing_id", "rating"],
        },
    ),
    _marketplace_rate,
))
