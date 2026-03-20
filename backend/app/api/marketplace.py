"""Marketplace API — browse, publish, install, and rate listings."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.models import MarketplaceListing
from app.schemas.marketplace import (
    InstallListingResponse,
    MarketplaceListingCreate,
    MarketplaceListingResponse,
    MarketplaceListingUpdate,
    MarketplaceListResponse,
    RateListingRequest,
    RateListingResponse,
)

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

_VALID_SORT = {"downloads", "rating", "created_at"}


# ---------------------------------------------------------------------------
# GET /api/marketplace
# ---------------------------------------------------------------------------


@router.get("", response_model=MarketplaceListResponse)
async def browse_marketplace(
    q: str | None = Query(None, description="Full-text search in title / description"),
    listing_type: str | None = Query(None, description="Filter by type: template | org | agent"),
    tags: list[str] = Query(default=[], description="Filter listings that contain ALL of these tags"),
    sort: str = Query("downloads", description="Sort field: downloads | rating | created_at"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Browse publicly published marketplace listings."""
    if sort not in _VALID_SORT:
        raise HTTPException(status_code=400, detail=f"Invalid sort field. Choose from: {_VALID_SORT}")

    query = select(MarketplaceListing).where(MarketplaceListing.is_published.is_(True))

    if q:
        query = query.where(
            MarketplaceListing.title.ilike(f"%{q}%")
            | MarketplaceListing.description.ilike(f"%{q}%")
        )
    if listing_type:
        query = query.where(MarketplaceListing.listing_type == listing_type)

    # Tag filtering: each requested tag must appear in the JSONB tags array.
    for tag in tags:
        from sqlalchemy import cast, Text
        query = query.where(
            cast(MarketplaceListing.tags, Text).ilike(f"%{tag}%")
        )

    sort_col = getattr(MarketplaceListing, sort)
    query = query.order_by(sort_col.desc())

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    result = await db.execute(query.limit(limit).offset(offset))
    items = result.scalars().all()

    return MarketplaceListResponse(items=items, total=total)


# ---------------------------------------------------------------------------
# GET /api/marketplace/{id}
# ---------------------------------------------------------------------------


@router.get("/{listing_id}", response_model=MarketplaceListingResponse)
async def get_listing(listing_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single marketplace listing by ID."""
    result = await db.execute(
        select(MarketplaceListing).where(MarketplaceListing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


# ---------------------------------------------------------------------------
# POST /api/marketplace
# ---------------------------------------------------------------------------


@router.post("", response_model=MarketplaceListingResponse, status_code=201)
async def publish_listing(
    payload: MarketplaceListingCreate,
    db: AsyncSession = Depends(get_db),
):
    """Publish a new marketplace listing."""
    listing = MarketplaceListing(
        listing_type=payload.listing_type,
        title=payload.title,
        description=payload.description,
        author=payload.author,
        version=payload.version,
        config=payload.config,
        tags=payload.tags,
        is_published=payload.is_published,
    )
    db.add(listing)
    await db.flush()
    return listing


# ---------------------------------------------------------------------------
# PUT /api/marketplace/{id}
# ---------------------------------------------------------------------------


@router.put("/{listing_id}", response_model=MarketplaceListingResponse)
async def update_listing(
    listing_id: UUID,
    payload: MarketplaceListingUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a marketplace listing."""
    result = await db.execute(
        select(MarketplaceListing).where(MarketplaceListing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if payload.title is not None:
        listing.title = payload.title
    if payload.description is not None:
        listing.description = payload.description
    if payload.version is not None:
        listing.version = payload.version
    if payload.config is not None:
        listing.config = payload.config
    if payload.tags is not None:
        listing.tags = payload.tags
    if payload.is_published is not None:
        listing.is_published = payload.is_published

    await db.flush()
    return listing


# ---------------------------------------------------------------------------
# POST /api/marketplace/{id}/install
# ---------------------------------------------------------------------------


@router.post("/{listing_id}/install", response_model=InstallListingResponse)
async def install_listing(listing_id: UUID, db: AsyncSession = Depends(get_db)):
    """Install a listing — increments download counter and returns the config."""
    result = await db.execute(
        select(MarketplaceListing).where(MarketplaceListing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if not listing.is_published:
        raise HTTPException(status_code=400, detail="Listing is not published")

    listing.downloads += 1
    await db.flush()

    return InstallListingResponse(
        listing_id=listing.id,
        listing_type=listing.listing_type,
        message=f"'{listing.title}' installed successfully",
        installed_config=listing.config,
    )


# ---------------------------------------------------------------------------
# POST /api/marketplace/{id}/rate
# ---------------------------------------------------------------------------


@router.post("/{listing_id}/rate", response_model=RateListingResponse)
async def rate_listing(
    listing_id: UUID,
    payload: RateListingRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rate a marketplace listing (1–5 stars). Updates rolling average."""
    result = await db.execute(
        select(MarketplaceListing).where(MarketplaceListing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Rolling average: new_avg = (old_avg * old_count + new_rating) / (old_count + 1)
    new_count = listing.rating_count + 1
    new_rating = (listing.rating * listing.rating_count + payload.rating) / new_count

    listing.rating = round(new_rating, 2)
    listing.rating_count = new_count
    await db.flush()

    return RateListingResponse(
        listing_id=listing.id,
        new_rating=listing.rating,
        rating_count=listing.rating_count,
    )
