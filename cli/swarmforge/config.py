"""Centralised settings for SwarmForge CLI and MCP Server."""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    base_url: str = os.environ.get("SWARMFORGE_URL", "http://localhost:8000")
    timeout: float = float(os.environ.get("SWARMFORGE_TIMEOUT", "30"))


settings = Settings()
