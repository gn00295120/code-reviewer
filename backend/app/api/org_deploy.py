"""Org deployment API.

Endpoints
---------
POST /api/orgs/{id}/deploy  - Deploy an org (create agent instance records from topology)
GET  /api/orgs/{id}/status  - Get deployment status of org agents
POST /api/orgs/{id}/stop    - Stop all running agents in org

For MVP, deployment is a status-tracker: it records which agents should be
running based on the org topology.  Real agent spawning (Docker/process
management) can be layered on top later.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import AgentOrg

router = APIRouter(tags=["org-deploy"])

# In-memory deployment state for MVP (keyed by org_id string).
# Shape: { org_id: { status, deployed_at, agents: [{role, status, ...}] } }
_DEPLOYMENTS: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _get_org_or_404(org_id: UUID, db: AsyncSession) -> AgentOrg:
    result = await db.execute(select(AgentOrg).where(AgentOrg.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    return org


def _build_agent_records(topology: dict[str, Any], status: str = "running") -> list[dict[str, Any]]:
    """Build a list of agent instance records from a topology dict."""
    agents = topology.get("agents", [])
    return [
        {
            "role": a.get("role", "unknown"),
            "description": a.get("description", ""),
            "model": a.get("model", ""),
            "status": status,
        }
        for a in agents
    ]


# ===========================================================================
# Endpoints
# ===========================================================================


@router.post("/api/orgs/{org_id}/deploy")
async def deploy_org(org_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Deploy an org: create agent instance records from topology.

    Returns the deployment record with one entry per agent defined in the
    org topology, each marked as ``running``.
    """
    org = await _get_org_or_404(org_id, db)

    topology = org.topology or {}
    agents = _build_agent_records(topology, status="running")

    record: dict[str, Any] = {
        "org_id": str(org.id),
        "status": "running",
        "deployed_at": datetime.now(tz=timezone.utc).isoformat(),
        "agents": agents,
    }
    _DEPLOYMENTS[str(org.id)] = record
    return record


@router.get("/api/orgs/{org_id}/status")
async def get_org_status(org_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return the current deployment status for this org.

    If the org has never been deployed, returns ``status: idle``.
    """
    org = await _get_org_or_404(org_id, db)
    key = str(org.id)

    if key not in _DEPLOYMENTS:
        return {
            "org_id": key,
            "status": "idle",
            "deployed_at": None,
            "agents": [],
        }

    return _DEPLOYMENTS[key]


@router.post("/api/orgs/{org_id}/stop")
async def stop_org(org_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Stop all running agents in org.

    Marks every agent as ``stopped`` and updates the deployment record.
    """
    org = await _get_org_or_404(org_id, db)
    key = str(org.id)

    if key in _DEPLOYMENTS:
        record = _DEPLOYMENTS[key]
        record["status"] = "stopped"
        for agent in record.get("agents", []):
            agent["status"] = "stopped"
        record["stopped_at"] = datetime.now(tz=timezone.utc).isoformat()
    else:
        # Org exists but was never deployed — create a stopped record
        record = {
            "org_id": key,
            "status": "stopped",
            "deployed_at": None,
            "stopped_at": datetime.now(tz=timezone.utc).isoformat(),
            "agents": [],
        }
        _DEPLOYMENTS[key] = record

    return record
