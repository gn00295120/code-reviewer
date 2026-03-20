"""Enterprise Guard API — audit logs and security policies."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import AuditLog, SecurityPolicy
from app.schemas.enterprise import (
    AuditLogListResponse,
    AuditLogResponse,
    PolicyToggleResponse,
    SecurityPolicyCreate,
    SecurityPolicyResponse,
    SecurityPolicyUpdate,
)

router = APIRouter(prefix="/api", tags=["enterprise"])


# ---------------------------------------------------------------------------
# GET /api/audit
# ---------------------------------------------------------------------------


@router.get("/audit", response_model=AuditLogListResponse)
async def list_audit_logs(
    action: str | None = Query(None, description="Filter by action name"),
    actor: str | None = Query(None, description="Filter by actor"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    since: datetime | None = Query(None, description="Only logs after this ISO datetime"),
    until: datetime | None = Query(None, description="Only logs before this ISO datetime"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List audit log entries with optional filters."""
    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
    if actor:
        query = query.where(AuditLog.actor.ilike(f"%{actor}%"))
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if since:
        query = query.where(AuditLog.created_at >= since)
    if until:
        query = query.where(AuditLog.created_at <= until)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return AuditLogListResponse(items=items, total=total)


# ---------------------------------------------------------------------------
# GET /api/security-policies
# ---------------------------------------------------------------------------


@router.get("/security-policies", response_model=list[SecurityPolicyResponse])
async def list_security_policies(
    policy_type: str | None = Query(None, description="Filter by policy type"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
):
    """List all security policies."""
    query = select(SecurityPolicy).order_by(SecurityPolicy.created_at.desc())
    if policy_type:
        query = query.where(SecurityPolicy.policy_type == policy_type)
    if is_active is not None:
        query = query.where(SecurityPolicy.is_active == is_active)

    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# POST /api/security-policies
# ---------------------------------------------------------------------------


@router.post("/security-policies", response_model=SecurityPolicyResponse, status_code=201)
async def create_security_policy(
    payload: SecurityPolicyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new security policy."""
    # Enforce unique name.
    existing = await db.execute(
        select(SecurityPolicy).where(SecurityPolicy.name == payload.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Policy with name '{payload.name}' already exists",
        )

    policy = SecurityPolicy(
        name=payload.name,
        policy_type=payload.policy_type,
        config=payload.config,
        is_active=payload.is_active,
    )
    db.add(policy)
    await db.flush()
    return policy


# ---------------------------------------------------------------------------
# PUT /api/security-policies/{id}
# ---------------------------------------------------------------------------


@router.put("/security-policies/{policy_id}", response_model=SecurityPolicyResponse)
async def update_security_policy(
    policy_id: UUID,
    payload: SecurityPolicyUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing security policy."""
    result = await db.execute(select(SecurityPolicy).where(SecurityPolicy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Security policy not found")

    if payload.name is not None:
        # Check uniqueness (excluding self).
        dup = await db.execute(
            select(SecurityPolicy).where(
                SecurityPolicy.name == payload.name,
                SecurityPolicy.id != policy_id,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Policy with name '{payload.name}' already exists",
            )
        policy.name = payload.name

    if payload.policy_type is not None:
        policy.policy_type = payload.policy_type
    if payload.config is not None:
        policy.config = payload.config
    if payload.is_active is not None:
        policy.is_active = payload.is_active

    await db.flush()
    return policy


# ---------------------------------------------------------------------------
# POST /api/security-policies/{id}/toggle
# ---------------------------------------------------------------------------


@router.post("/security-policies/{policy_id}/toggle", response_model=PolicyToggleResponse)
async def toggle_security_policy(
    policy_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable a security policy."""
    result = await db.execute(select(SecurityPolicy).where(SecurityPolicy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Security policy not found")

    policy.is_active = not policy.is_active
    await db.flush()

    state = "enabled" if policy.is_active else "disabled"
    return PolicyToggleResponse(
        id=policy.id,
        is_active=policy.is_active,
        message=f"Policy '{policy.name}' {state}",
    )
