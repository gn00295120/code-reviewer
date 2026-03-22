"""AI CLI provider auto-detection and abstraction.

Priority order: codex -> claude -> gemini -> opencode
Each provider wraps a locally installed AI CLI tool.
"""

import asyncio
import json
import re
import shutil
import subprocess
from dataclasses import dataclass

from rich.console import Console

console = Console()


@dataclass
class ProviderInfo:
    name: str
    command: str
    model: str
    priority: int


# Priority order: lower number = higher priority
PROVIDERS = [
    ProviderInfo("codex", "codex", "gpt-5.4", 1),
    ProviderInfo("claude", "claude", "opus", 2),
    ProviderInfo("gemini", "gemini", "gemini-3", 3),
    ProviderInfo("opencode", "opencode", "opencode", 4),
]


def detect_providers() -> list[ProviderInfo]:
    """Detect which AI CLI tools are installed, sorted by priority."""
    available = []
    for p in PROVIDERS:
        if shutil.which(p.command):
            available.append(p)
    return sorted(available, key=lambda p: p.priority)


def get_best_provider() -> ProviderInfo | None:
    """Return the highest-priority available provider."""
    providers = detect_providers()
    return providers[0] if providers else None


def show_providers():
    """Print detected providers to console."""
    providers = detect_providers()
    if not providers:
        console.print("[red]No AI CLI tools found. Install codex, claude, gemini, or opencode.[/red]")
        return
    console.print("[bold]Detected AI CLI providers:[/bold]")
    for i, p in enumerate(providers):
        marker = " [green](active)[/green]" if i == 0 else ""
        console.print(f"  {p.priority}. [bold]{p.name}[/bold] ({p.command}) — {p.model}{marker}")


async def _run_codex(system_prompt: str, user_prompt: str) -> str:
    """Run review via Codex CLI (codex exec)."""
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    proc = await asyncio.create_subprocess_exec(
        "codex", "exec",
        "--full-auto",
        "-q", full_prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode("utf-8", errors="replace")


async def _run_claude(system_prompt: str, user_prompt: str) -> str:
    """Run review via Claude Code SDK."""
    from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage

    full_text = ""
    try:
        async for message in query(
            prompt=user_prompt,
            options=ClaudeCodeOptions(
                system_prompt=system_prompt,
                max_turns=1,
                allowed_tools=[],
            ),
        ):
            if not isinstance(message, AssistantMessage):
                continue
            for block in message.content:
                if hasattr(block, "text"):
                    full_text += block.text
    except Exception:
        pass  # Collect whatever text we got
    return full_text


async def _run_gemini(system_prompt: str, user_prompt: str) -> str:
    """Run review via Gemini CLI (non-interactive mode)."""
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    proc = await asyncio.create_subprocess_exec(
        "gemini",
        "-p", full_prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode("utf-8", errors="replace")


async def _run_opencode(system_prompt: str, user_prompt: str) -> str:
    """Run review via OpenCode CLI."""
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    proc = await asyncio.create_subprocess_exec(
        "opencode",
        "-p", full_prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode("utf-8", errors="replace")


_RUNNERS = {
    "codex": _run_codex,
    "claude": _run_claude,
    "gemini": _run_gemini,
    "opencode": _run_opencode,
}


async def run_with_provider(
    provider: ProviderInfo,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Run a prompt through the specified provider and return raw text."""
    runner = _RUNNERS.get(provider.name)
    if not runner:
        raise ValueError(f"No runner for provider: {provider.name}")
    return await runner(system_prompt, user_prompt)
