"""SwarmForge CLI — root entry point."""

import click

from ..config import settings
from .cmd_community import community_group
from .cmd_company import company_group
from .cmd_enterprise import enterprise_group
from .cmd_governance import governance_group
from .cmd_marketplace import marketplace_group
from .cmd_memory import memory_group
from .cmd_misc import misc_group
from .cmd_review import review_group
from .cmd_science import science_group
from .cmd_template import template_group
from .cmd_world_model import world_model_group


@click.group()
@click.option(
    "--url",
    envvar="SWARMFORGE_URL",
    default="http://localhost:8000",
    show_default=True,
    help="Base URL of the SwarmForge API.",
)
def cli(url: str) -> None:
    """SwarmForge CLI — AI agent command center."""
    settings.base_url = url


cli.add_command(review_group)
cli.add_command(template_group)
cli.add_command(memory_group)
cli.add_command(company_group)
cli.add_command(governance_group)
cli.add_command(community_group)
cli.add_command(marketplace_group)
cli.add_command(enterprise_group)
cli.add_command(science_group)
cli.add_command(world_model_group)
cli.add_command(misc_group)
