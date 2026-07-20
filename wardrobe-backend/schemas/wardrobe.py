from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.orm import IngestionStatus, GarmentCategory, EMBEDDING_DIM

class WardrobeItemCreate(BaseModel):
    """Inbound payload at ingestion — Workflow A step 1, before worker enrichment."""
    user_id: UUID
    raw_image_url: str

class WardrobeItemIngestAck(BaseModel):
    """202 Accepted response body."""
    item_id: UUID
    status: IngestionStatus = IngestionStatus.PENDING

class WardrobeItem(BaseModel):
    """Full read model — general API-facing representation."""
    model_config = ConfigDict(from_attributes=True)

    item_id: UUID
    user_id: UUID
    raw_image_url: str
    processed_image_url: Optional[str] = None
    status: IngestionStatus
    failure_reason: Optional[str] = None

    category: Optional[GarmentCategory] = None
    sub_category: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    pattern: Optional[str] = None
    fit: Optional[str] = None
    material: Optional[str] = None
    season_tags: Optional[list[str]] = None

    created_at: datetime
    updated_at: datetime

class WardrobeItemInternal(WardrobeItem):
    """Worker-internal use only — adds the embedding. Never used as a FastAPI response_model."""
    style_embedding: Optional[list[float]] = None

    @field_validator("style_embedding")
    @classmethod
    def validate_dim(cls, v: Optional[list[float]]) -> Optional[list[float]]:
        if v is not None and len(v) != EMBEDDING_DIM:
            raise ValueError(f"Embedding must be {EMBEDDING_DIM}-dim, got {len(v)}")
        return v

class WardrobeItemLLMView(BaseModel):
    """
    Minimal projection sent into LLM context window for Workflow B.
    Deliberately excludes URLs/timestamps/embedding to keep token cost down.
    """
    item_id: UUID
    category: GarmentCategory
    sub_category: str
    primary_color: str
    pattern: Optional[str] = None
    fit: Optional[str] = None
    season_tags: list[str] = Field(default_factory=list)