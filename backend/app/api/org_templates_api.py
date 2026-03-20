"""Org seed-template management API.

Endpoints
---------
GET  /api/org-templates               - List all built-in seed templates
POST /api/org-templates/{name}/instantiate - Create an AgentOrg from a seed template
"""

import copy
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import AgentOrg
from app.schemas.community import OrgResponse
from app.services.org_templates import get_all_templates, get_template_by_name

router = APIRouter(tags=["org-templates"])


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


def _template_to_response(template: dict[str, Any]) -> dict[str, Any]:
    """Serialize a seed template dict for the list endpoint."""
    return {
        "name": template["name"],
        "description": template.get("description", ""),
        "topology": template.get("topology", {}),
        "config": template.get("config", {}),
    }


# ===========================================================================
# Endpoints
# ===========================================================================


@router.get("/api/org-templates")
async def list_org_templates() -> list[dict[str, Any]]:
    """Return all built-in seed templates (not database records)."""
    return [_template_to_response(t) for t in get_all_templates()]


@router.post("/api/org-templates/{name}/instantiate", response_model=OrgResponse, status_code=201)
async def instantiate_org_template(name: str, db: AsyncSession = Depends(get_db)):
    """Create an AgentOrg database record from a seed template.

    The resulting org is marked ``is_template=True`` so it appears in the
    community template gallery alongside user-forked orgs.
    """
    template = get_template_by_name(name)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found")

    org = AgentOrg(
        name=template["name"],
        description=template.get("description"),
        topology=copy.deepcopy(template.get("topology", {})),
        config=copy.deepcopy(template.get("config", {})),
        is_template=True,
    )
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org
