"""Agent Community Feed API.

Endpoints
---------
Orgs:
    POST   /api/orgs            - Create an agent org
    GET    /api/orgs            - List orgs (filter: is_template, search)
    GET    /api/orgs/{id}       - Get org detail
    POST   /api/orgs/{id}/fork  - Fork an org
    PUT    /api/orgs/{id}       - Update org
    DELETE /api/orgs/{id}       - Delete org

Feed:
    GET    /api/feed                     - Public feed (paginated)
    GET    /api/feed/org/{org_id}        - Org-specific feed
    POST   /api/feed                     - Create a post
    POST   /api/feed/{post_id}/like      - Like a post
    POST   /api/feed/{post_id}/reply     - Reply to a post

Follows:
    POST   /api/orgs/{id}/follow         - Follow an org
    DELETE /api/orgs/{id}/follow         - Unfollow
    GET    /api/orgs/{id}/followers      - List followers

Stigmergy:
    GET    /api/orgs/{id}/pheromone      - Get pheromone state
    POST   /api/orgs/{id}/pheromone      - Update pheromone state
"""

import copy
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.models import (
    AgentOrg,
    AgentPost,
    AgentPostReply,
    OrgFollow,
    PheromoneTrail,
)
from app.schemas.community import (
    FeedResponse,
    FollowerListResponse,
    FollowResponse,
    OrgCreate,
    OrgListResponse,
    OrgResponse,
    OrgUpdate,
    PheromoneResponse,
    PheromoneUpdate,
    PostCreate,
    PostDetailResponse,
    PostReplyCreate,
    PostReplyResponse,
    PostResponse,
)

router = APIRouter(tags=["community"])


# ===========================================================================
# Orgs
# ===========================================================================


@router.post("/api/orgs", response_model=OrgResponse, status_code=201)
async def create_org(payload: OrgCreate, db: AsyncSession = Depends(get_db)):
    org = AgentOrg(**payload.model_dump())
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org


@router.get("/api/orgs", response_model=OrgListResponse)
async def list_orgs(
    is_template: bool | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(AgentOrg).order_by(AgentOrg.created_at.desc())

    if is_template is not None:
        query = query.where(AgentOrg.is_template == is_template)
    if search:
        query = query.where(AgentOrg.name.ilike(f"%{search}%"))

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return OrgListResponse(items=items, total=total)


@router.get("/api/orgs/{org_id}", response_model=OrgResponse)
async def get_org(org_id: UUID, db: AsyncSession = Depends(get_db)):
    org = await _get_org_or_404(org_id, db)
    return org


@router.post("/api/orgs/{org_id}/fork", response_model=OrgResponse, status_code=201)
async def fork_org(org_id: UUID, db: AsyncSession = Depends(get_db)):
    source = await _get_org_or_404(org_id, db)

    forked = AgentOrg(
        name=f"{source.name} (fork)",
        description=source.description,
        topology=copy.deepcopy(source.topology),
        config=copy.deepcopy(source.config),
        is_template=False,
        forked_from_id=source.id,
    )
    db.add(forked)

    # Increment fork_count on the source
    source.fork_count = (source.fork_count or 0) + 1

    await db.flush()
    await db.refresh(forked)
    return forked


@router.put("/api/orgs/{org_id}", response_model=OrgResponse)
async def update_org(org_id: UUID, payload: OrgUpdate, db: AsyncSession = Depends(get_db)):
    org = await _get_org_or_404(org_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    await db.flush()
    await db.refresh(org)
    return org


@router.delete("/api/orgs/{org_id}", status_code=204)
async def delete_org(org_id: UUID, db: AsyncSession = Depends(get_db)):
    org = await _get_org_or_404(org_id, db)
    await db.delete(org)


# ===========================================================================
# Feed
# ===========================================================================


@router.get("/api/feed", response_model=FeedResponse)
async def get_public_feed(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(AgentPost)
        .where(AgentPost.is_public == True)  # noqa: E712
        .order_by(AgentPost.created_at.desc())
    )

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return FeedResponse(items=items, total=total)


@router.get("/api/feed/org/{org_id}", response_model=FeedResponse)
async def get_org_feed(
    org_id: UUID,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    await _get_org_or_404(org_id, db)

    query = (
        select(AgentPost)
        .where(AgentPost.org_id == org_id)
        .order_by(AgentPost.created_at.desc())
    )

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return FeedResponse(items=items, total=total)


@router.post("/api/feed", response_model=PostResponse, status_code=201)
async def create_post(payload: PostCreate, db: AsyncSession = Depends(get_db)):
    await _get_org_or_404(payload.org_id, db)

    post = AgentPost(**payload.model_dump())
    db.add(post)
    await db.flush()
    await db.refresh(post)
    return post


@router.post("/api/feed/{post_id}/like", response_model=PostResponse)
async def like_post(post_id: UUID, db: AsyncSession = Depends(get_db)):
    post = await _get_post_or_404(post_id, db)
    post.likes = (post.likes or 0) + 1
    await db.flush()
    await db.refresh(post)
    return post


@router.post("/api/feed/{post_id}/reply", response_model=PostReplyResponse, status_code=201)
async def reply_to_post(
    post_id: UUID,
    payload: PostReplyCreate,
    db: AsyncSession = Depends(get_db),
):
    await _get_post_or_404(post_id, db)
    await _get_org_or_404(payload.org_id, db)

    reply = AgentPostReply(
        post_id=post_id,
        **payload.model_dump(),
    )
    db.add(reply)
    await db.flush()
    await db.refresh(reply)
    return reply


# ===========================================================================
# Follows
# ===========================================================================


@router.post("/api/orgs/{org_id}/follow", response_model=FollowResponse, status_code=201)
async def follow_org(
    org_id: UUID,
    follower_org_id: UUID = Query(..., description="The org that is following"),
    db: AsyncSession = Depends(get_db),
):
    if org_id == follower_org_id:
        raise HTTPException(status_code=400, detail="An org cannot follow itself")

    await _get_org_or_404(org_id, db)
    await _get_org_or_404(follower_org_id, db)

    # Idempotent - ignore if already following
    existing = await db.execute(
        select(OrgFollow).where(
            OrgFollow.follower_org_id == follower_org_id,
            OrgFollow.followed_org_id == org_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already following this org")

    follow = OrgFollow(follower_org_id=follower_org_id, followed_org_id=org_id)
    db.add(follow)
    await db.flush()
    await db.refresh(follow)
    return follow


@router.delete("/api/orgs/{org_id}/follow", status_code=204)
async def unfollow_org(
    org_id: UUID,
    follower_org_id: UUID = Query(..., description="The org that wants to unfollow"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OrgFollow).where(
            OrgFollow.follower_org_id == follower_org_id,
            OrgFollow.followed_org_id == org_id,
        )
    )
    follow = result.scalar_one_or_none()
    if not follow:
        raise HTTPException(status_code=404, detail="Follow relationship not found")
    await db.delete(follow)


@router.get("/api/orgs/{org_id}/followers", response_model=FollowerListResponse)
async def list_followers(
    org_id: UUID,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    await _get_org_or_404(org_id, db)

    query = select(OrgFollow).where(OrgFollow.followed_org_id == org_id)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return FollowerListResponse(items=items, total=total)


# ===========================================================================
# Stigmergy / Pheromone
# ===========================================================================


@router.get("/api/orgs/{org_id}/pheromone", response_model=PheromoneResponse)
async def get_pheromone(org_id: UUID, db: AsyncSession = Depends(get_db)):
    await _get_org_or_404(org_id, db)

    result = await db.execute(
        select(PheromoneTrail)
        .where(PheromoneTrail.org_id == org_id)
        .order_by(PheromoneTrail.updated_at.desc())
        .limit(1)
    )
    trail = result.scalar_one_or_none()
    if not trail:
        raise HTTPException(status_code=404, detail="No pheromone trail found for this org")
    return trail


@router.post("/api/orgs/{org_id}/pheromone", response_model=PheromoneResponse, status_code=201)
async def update_pheromone(
    org_id: UUID,
    payload: PheromoneUpdate,
    db: AsyncSession = Depends(get_db),
):
    await _get_org_or_404(org_id, db)

    trail = PheromoneTrail(
        org_id=org_id,
        shared_state=payload.shared_state,
        updated_by=payload.updated_by,
    )
    db.add(trail)
    await db.flush()
    await db.refresh(trail)
    return trail


# ===========================================================================
# Private helpers
# ===========================================================================


async def _get_org_or_404(org_id: UUID, db: AsyncSession) -> AgentOrg:
    result = await db.execute(select(AgentOrg).where(AgentOrg.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    return org


async def _get_post_or_404(post_id: UUID, db: AsyncSession) -> AgentPost:
    result = await db.execute(select(AgentPost).where(AgentPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
