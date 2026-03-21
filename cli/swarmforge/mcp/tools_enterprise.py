"""MCP tools for enterprise audit and security-policy operations."""

import json
from mcp.types import Tool, TextContent

from ..client import client, SwarmForgeError

TOOLS = []


def _text(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _error(e: SwarmForgeError) -> list[TextContent]:
    return [TextContent(type="text", text=f"Error {e.status}: {e}")]


# ---------------------------------------------------------------------------
# audit_list
# ---------------------------------------------------------------------------

async def _audit_list(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "action": arguments.get("action"),
            "actor": arguments.get("actor"),
            "resource_type": arguments.get("resource_type"),
            "since": arguments.get("since"),
            "until": arguments.get("until"),
            "limit": arguments.get("limit"),
            "offset": arguments.get("offset"),
        }.items() if v is not None}
        result = await client.get("/api/audit", params=params or None)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="audit_list",
        description="List audit log entries with optional filters.",
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Filter by action type."},
                "actor": {"type": "string", "description": "Filter by actor ID (user or agent)."},
                "resource_type": {"type": "string", "description": "Filter by resource type."},
                "since": {"type": "string", "description": "ISO-8601 start datetime (inclusive)."},
                "until": {"type": "string", "description": "ISO-8601 end datetime (inclusive)."},
                "limit": {"type": "integer", "description": "Maximum number of results."},
                "offset": {"type": "integer", "description": "Pagination offset."},
            },
            "required": [],
        },
    ),
    _audit_list,
))


# ---------------------------------------------------------------------------
# policy_list
# ---------------------------------------------------------------------------

async def _policy_list(arguments: dict) -> list[TextContent]:
    try:
        params = {k: v for k, v in {
            "policy_type": arguments.get("policy_type"),
            "is_active": arguments.get("is_active"),
        }.items() if v is not None}
        result = await client.get("/api/security-policies", params=params or None)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="policy_list",
        description="List security policies with optional filters.",
        inputSchema={
            "type": "object",
            "properties": {
                "policy_type": {"type": "string", "description": "Filter by policy type."},
                "is_active": {"type": "boolean", "description": "Filter by active status."},
            },
            "required": [],
        },
    ),
    _policy_list,
))


# ---------------------------------------------------------------------------
# policy_create
# ---------------------------------------------------------------------------

async def _policy_create(arguments: dict) -> list[TextContent]:
    try:
        body: dict = {
            "name": arguments["name"],
            "policy_type": arguments["policy_type"],
            "config": arguments["config"],
        }
        if "is_active" in arguments:
            body["is_active"] = arguments["is_active"]
        result = await client.post("/api/security-policies", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="policy_create",
        description="Create a new security policy.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Policy name (required)."},
                "policy_type": {
                    "type": "string",
                    "description": "Type of policy (e.g. rate_limit, access_control, content_filter) — required.",
                },
                "config": {
                    "type": "object",
                    "description": "Policy configuration object (required).",
                },
                "is_active": {"type": "boolean", "description": "Whether the policy is active immediately (default true)."},
            },
            "required": ["name", "policy_type", "config"],
        },
    ),
    _policy_create,
))


# ---------------------------------------------------------------------------
# policy_update
# ---------------------------------------------------------------------------

async def _policy_update(arguments: dict) -> list[TextContent]:
    try:
        body = {k: v for k, v in {
            "name": arguments.get("name"),
            "config": arguments.get("config"),
        }.items() if v is not None}
        result = await client.put(f"/api/security-policies/{arguments['policy_id']}", json=body)
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="policy_update",
        description="Update an existing security policy's name or configuration.",
        inputSchema={
            "type": "object",
            "properties": {
                "policy_id": {"type": "string", "description": "Security policy ID to update."},
                "name": {"type": "string", "description": "New policy name."},
                "config": {"type": "object", "description": "Updated configuration object."},
            },
            "required": ["policy_id"],
        },
    ),
    _policy_update,
))


# ---------------------------------------------------------------------------
# policy_toggle
# ---------------------------------------------------------------------------

async def _policy_toggle(arguments: dict) -> list[TextContent]:
    try:
        result = await client.post(f"/api/security-policies/{arguments['policy_id']}/toggle")
        return _text(result)
    except SwarmForgeError as e:
        return _error(e)


TOOLS.append((
    Tool(
        name="policy_toggle",
        description="Toggle a security policy between active and inactive.",
        inputSchema={
            "type": "object",
            "properties": {
                "policy_id": {"type": "string", "description": "Security policy ID to toggle."},
            },
            "required": ["policy_id"],
        },
    ),
    _policy_toggle,
))
