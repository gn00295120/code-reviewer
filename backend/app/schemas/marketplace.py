from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request schemas ---


class MarketplaceListingCreate(BaseModel):
    listing_type: str = Field(..., max_length=64, description="Listing type: template | org | agent")
    title: str = Field(..., max_length=256, description="Human-readable listing title")
    description: str | None = Field(None, description="Detailed description of the listing")
    author: str | None = Field(None, max_length=128, description="Author / publisher name")
    version: str = Field("1.0.0", max_length=32, description="Semantic version string")
    config: dict[str, Any] = Field(default_factory=dict, description="Template / org / agent definition")
    tags: list[str] = Field(default_factory=list, description='Searchable tags, e.g. ["security", "python"]')
    is_published: bool = Field(True, description="Whether the listing is publicly visible")


class MarketplaceListingUpdate(BaseModel):
    title: str | None = Field(None, max_length=256)
    description: str | None = None
    version: str | None = Field(None, max_length=32)
    config: dict[str, Any] | None = None
    tags: list[str] | None = None
    is_published: bool | None = None


class RateListingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 (worst) to 5 (best)")


# --- Response schemas ---


class MarketplaceListingResponse(BaseModel):
    id: UUID
    listing_type: str
    title: str
    description: str | None
    author: str | None
    version: str
    config: dict[str, Any]
    tags: list[str]
    downloads: int
    rating: float
    rating_count: int
    is_published: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class MarketplaceListResponse(BaseModel):
    items: list[MarketplaceListingResponse]
    total: int


class InstallListingResponse(BaseModel):
    listing_id: UUID
    listing_type: str
    message: str
    installed_config: dict[str, Any]


class RateListingResponse(BaseModel):
    listing_id: UUID
    new_rating: float
    rating_count: int
