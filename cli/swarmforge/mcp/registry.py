"""Tool registry: imports all module TOOLS lists and registers them on the MCP Server.

Environment variable ``SWARMFORGE_MODULES`` controls which modules are loaded.
Set it to a comma-separated list of module names (e.g. ``review,template``) or
leave it unset / set to ``all`` to enable every module.

Example:
    SWARMFORGE_MODULES=review,memory python -m swarmforge.mcp_server
"""

from __future__ import annotations

import logging
import os
from typing import Callable

from mcp.server import Server
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy module loaders — avoids importing everything at import time so that a
# broken module does not prevent the rest from loading.
# ---------------------------------------------------------------------------

def _load_review():
    from .tools_review import TOOLS
    return TOOLS


def _load_template():
    from .tools_template import TOOLS
    return TOOLS


def _load_memory():
    from .tools_memory import TOOLS
    return TOOLS


def _load_company():
    from .tools_company import TOOLS
    return TOOLS


def _load_governance():
    from .tools_governance import TOOLS
    return TOOLS


def _load_community():
    from .tools_community import TOOLS
    return TOOLS


def _load_marketplace():
    from .tools_marketplace import TOOLS
    return TOOLS


def _load_enterprise():
    from .tools_enterprise import TOOLS
    return TOOLS


def _load_science():
    from .tools_science import TOOLS
    return TOOLS


def _load_world_model():
    from .tools_world_model import TOOLS
    return TOOLS


def _load_misc():
    from .tools_misc import TOOLS
    return TOOLS


# Ordered dict of module_name -> loader callable
_MODULES: dict[str, Callable[[], list[tuple[Tool, Callable]]]] = {
    "review": _load_review,
    "template": _load_template,
    "memory": _load_memory,
    "company": _load_company,
    "governance": _load_governance,
    "community": _load_community,
    "marketplace": _load_marketplace,
    "enterprise": _load_enterprise,
    "science": _load_science,
    "world_model": _load_world_model,
    "misc": _load_misc,
}


def _enabled_modules() -> set[str]:
    """Return the set of module names that should be loaded."""
    raw = os.environ.get("SWARMFORGE_MODULES", "all").strip()
    if not raw or raw == "all":
        return set(_MODULES.keys())
    return {name.strip() for name in raw.split(",")}


def register_all_tools(server: Server) -> int:
    """Register tools from all enabled modules onto *server*.

    Returns the total number of tools registered.
    """
    enabled = _enabled_modules()
    registered = 0

    # Build a flat mapping of tool-name -> handler so we can wire up the
    # server's call_tool handler after collecting everything.
    tool_handlers: dict[str, Callable] = {}
    tool_definitions: list[Tool] = []

    for module_name, loader in _MODULES.items():
        if module_name not in enabled:
            logger.debug("Skipping module %r (not in SWARMFORGE_MODULES)", module_name)
            continue

        try:
            tools = loader()
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to load module %r: %s", module_name, exc)
            continue

        for tool, handler in tools:
            if tool.name in tool_handlers:
                logger.warning("Duplicate tool name %r from module %r — skipping", tool.name, module_name)
                continue
            tool_definitions.append(tool)
            tool_handlers[tool.name] = handler
            registered += 1
            logger.debug("Registered tool %r", tool.name)

    # Register the list_tools handler
    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        return tool_definitions

    # Register the call_tool handler
    @server.call_tool()
    async def _call_tool(name: str, arguments: dict) -> list[TextContent]:
        handler = tool_handlers.get(name)
        if handler is None:
            from mcp.types import TextContent as TC
            return [TC(type="text", text=f"Unknown tool: {name!r}")]
        return await handler(arguments)

    logger.info("SwarmForge MCP: registered %d tools from modules %s", registered, sorted(enabled & set(_MODULES)))
    return registered
