"""SwarmForge MCP Server entry point.

Run with:
    python -m swarmforge.mcp_server

Or, if installed as a package:
    swarmforge-mcp

Environment variables:
    SWARMFORGE_BASE_URL   -- API base URL (default: http://localhost:8000)
    SWARMFORGE_MODULES    -- Comma-separated module names to enable, or "all" (default: all)
"""

from __future__ import annotations

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server

from .mcp.registry import register_all_tools

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_server() -> Server:
    """Build and configure the MCP server instance."""
    server = Server("swarmforge")
    count = register_all_tools(server)
    logger.info("SwarmForge MCP server ready with %d tools.", count)
    return server


def main() -> None:
    """Start the SwarmForge MCP server over stdio."""
    server = create_server()
    asyncio.run(stdio_server(server))


if __name__ == "__main__":
    main()
