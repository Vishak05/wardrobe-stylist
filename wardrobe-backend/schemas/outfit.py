from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field


class OutfitRequest(BaseModel):
    """Inbound request — Workflow B step 1: 'Core API parses the natural language query.'"""
    user_id: UUID
    query: str = Field(..., min_length=1, max_length=500)
    # Optional structured hints, distinct from the free-text query — lets the frontend
    # pass known filters (e.g. a weather widget) without stuffing everything into `query`.
    occasion: Optional[str] = None
    max_temperature_celsius: Optional[float] = None


class LLMOutfitSelection(BaseModel):
    """
    The EXACT shape we force Gemini to return via response_schema.
    This is the contract for Workflow B step 4: 'strict JSON structured output
    that returns exact item_ids, not conversational text.'
    """
    item_ids: list[UUID] = Field(..., description="Wardrobe item_ids selected for this outfit")
    styling_notes: str = Field(..., description="Brief rationale for why these items work together")


class OutfitResponse(BaseModel):
    """Final payload returned to the client — Workflow B step 5."""
    item_ids: list[UUID]
    styling_notes: str
    image_urls: dict[UUID, str]  # item_id -> processed_image_url, resolved post-LLM