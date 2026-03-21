"""MCP tools for community operations: orgs, feed, follow, pheromone."""

import json
from mcp.types import Tool, TextContent

from ..client import client, SwarmForgeError

TOOLS = []


def _text(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _error(e: SwarmForgeError) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error {e.status}: {e}")]


# ===========================================================================
# Orgs
# ===========================================================================

async def _org_create(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {"name": arguments["name"]}
        for opt in ("description", "topology", "config"):
            if opt in arguments:
                body[opt] = arguments[opt]
        result = await client.post("/api/orgs", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_create",
        description="Create a new agent organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Organisation name (required)."},
                "description": {"type": "string", "description": "Organisation description."},
                "topology": {
                    "type": "string",
                    "description": "Agent topology type (e.g. hierarchical, flat, swarm).",
                },
                "config": {"type": "object", "description": "Additional organisation configuration."},
            },
            "required": ["name"],
        },
    ),
    _org_create,
))


async def _org_list(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "is_template": arguments.get("is_template"),
            "search": arguments.get("search"),
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get("/api/orgs", params=params or None)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_list",
        description="List agent organisations, optionally filtering by template flag or search query.",
        inputSchema={
            "type": "object",
            "properties": {
                "is_template": {"type": "boolean", "description": "If true, only return template orgs."},
                "search": {"type": "string", "description": "Search string to filter organisations."},
                "limit": {"type": "integer", "description": "Maximum number of results."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": [],
        },
    ),
    _org_list,
))


async def _org_get(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/orgs/{arguments['org_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_get",
        description="Get details of a specific organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID."},
            },
            "required": ["org_id"],
        },
    ),
    _org_get,
))


async def _org_fork(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/orgs/{arguments['org_id']}/fork")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_fork",
        description="Fork an existing organisation as a new personal copy.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID to fork."},
            },
            "required": ["org_id"],
        },
    ),
    _org_fork,
))


async def _org_update(arguments: dict) -> list[TextContent]:
    try:
        body = {k: v for k, v in {
            "name": arguments.get("name"),
            "description": arguments.get("description"),
            "topology": arguments.get("topology"),
        }.items() if v is not None}
        result = await client.put(f"/api/orgs/{arguments['org_id']}", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_update",
        description="Update an organisation's name, description, or topology.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID to update."},
                "name": {"type": "string", "description": "New name."},
                "description": {"type": "string", "description": "New description."},
                "topology": {"type": "string", "description": "New topology type."},
            },
            "required": ["org_id"],
        },
    ),
    _org_update,
))


async def _org_delete(arguments: dict) -> list[TextContent]:
    try:
        result = await client.delete(f"/api/orgs/{arguments['org_id']}")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_delete",
        description="Delete an organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID to delete."},
            },
            "required": ["org_id"],
        },
    ),
    _org_delete,
))


# ===========================================================================
# Feed
# ===========================================================================

async def _feed_list(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get("/api/feed", params=params or None)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="feed_list",
        description="Get the global public activity feed.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum number of posts to return."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": [],
        },
    ),
    _feed_list,
))


async def _feed_org(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get(f"/api/feed/org/{arguments['org_id']}", params=params or None)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="feed_org",
        description="Get the activity feed for a specific organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID."},
                "limit": {"type": "integer", "description": "Maximum number of posts."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": ["org_id"],
        },
    ),
    _feed_org,
))


async def _feed_post(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {
            "org_id": arguments["org_id"],
            "content": arguments["content"],
        }
        if "is_public" in arguments:
            body["is_public"] = arguments["is_public"]
        result = await client.post("/api/feed", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="feed_post",
        description="Publish a new post to the activity feed on behalf of an organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID posting the content (required)."},
                "content": {"type": "string", "description": "Post content text (required)."},
                "is_public": {"type": "boolean", "description": "Whether the post is publicly visible (default true)."},
            },
            "required": ["org_id", "content"],
        },
    ),
    _feed_post,
))


async def _feed_like(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/feed/{arguments['post_id']}/like")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="feed_like",
        description="Like a feed post.",
        inputSchema={
            "type": "object",
            "properties": {
                "post_id": {"type": "string", "description": "Feed post ID to like."},
            },
            "required": ["post_id"],
        },
    ),
    _feed_like,
))


async def _feed_reply(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {
            "org_id": arguments["org_id"],
            "content": arguments["content"],
        }
        result = await client.post(f"/api/feed/{arguments['post_id']}/reply", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="feed_reply",
        description="Reply to a feed post on behalf of an organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "post_id": {"type": "string", "description": "Feed post ID to reply to."},
                "org_id": {"type": "string", "description": "Organisation ID posting the reply (required)."},
                "content": {"type": "string", "description": "Reply content text (required)."},
            },
            "required": ["post_id", "org_id", "content"],
        },
    ),
    _feed_reply,
))


# ===========================================================================
# Follow / Pheromone
# ===========================================================================

async def _org_follow(arguments: dict) -> list[TextContent]:
    try:
        params = {"follower_org_id": arguments["follower_org_id"]}
        result = await client.post(f"/api/orgs/{arguments['org_id']}/follow", params=params)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_follow",
        description="Follow an organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID to follow."},
                "follower_org_id": {
                    "type": "string",
                    "description": "Organisation ID of the follower (required).",
                },
            },
            "required": ["org_id", "follower_org_id"],
        },
    ),
    _org_follow,
))


async def _org_unfollow(arguments: dict) -> list[TextContent]:
    try:
        params = {"follower_org_id": arguments["follower_org_id"]}
        result = await client.delete(f"/api/orgs/{arguments['org_id']}/follow", params=params)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_unfollow",
        description="Unfollow an organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID to unfollow."},
                "follower_org_id": {
                    "type": "string",
                    "description": "Organisation ID of the follower (required).",
                },
            },
            "required": ["org_id", "follower_org_id"],
        },
    ),
    _org_unfollow,
))


async def _org_followers(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get(
            f"/api/orgs/{arguments['org_id']}/followers",
            params=params or None,
        )
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="org_followers",
        description="List followers of an organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID."},
                "limit": {"type": "integer", "description": "Maximum number of results."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": ["org_id"],
        },
    ),
    _org_followers,
))


async def _pheromone_get(arguments: dict) -> list[TextContent]:
    try:
        result = await client.get(f"/api/orgs/{arguments['org_id']}/pheromone")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="pheromone_get",
        description="Get the current pheromone (shared state) for an organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID."},
            },
            "required": ["org_id"],
        },
    ),
    _pheromone_get,
))


async def _pheromone_update(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {
            "shared_state": arguments["shared_state"],
            "updated_by": arguments["updated_by"],
        }
        result = await client.post(f"/api/orgs/{arguments['org_id']}/pheromone", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="pheromone_update",
        description="Update the pheromone (shared state) for an organisation.",
        inputSchema={
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID."},
                "shared_state": {
                    "type": "object",
                    "description": "New shared state object (required).",
                },
                "updated_by": {
                    "type": "string",
                    "description": "ID of the agent or user performing the update (required).",
                },
            },
            "required": ["org_id", "shared_state", "updated_by"],
        },
    ),
    _pheromone_update,
))
