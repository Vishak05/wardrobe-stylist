from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.orm import WardrobeItemORM, IngestionStatus
from schemas.outfit import OutfitRequest, OutfitResponse
from schemas.wardrobe import WardrobeItemLLMView
from services.gemini_client import get_outfit_recommendation

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=OutfitResponse)
async def create_recommendation(
    request: OutfitRequest, db: AsyncSession = Depends(get_db)
):
    # --- Workflow B step 2: pre-filter Postgres before touching the LLM ---
    stmt = select(WardrobeItemORM).where(
        WardrobeItemORM.user_id == request.user_id,
        WardrobeItemORM.status == IngestionStatus.COMPLETED,
    )
    result = await db.execute(stmt)
    wardrobe_rows = result.scalars().all()

    if not wardrobe_rows:
        raise HTTPException(
            status_code=404, detail="No completed wardrobe items found for this user."
        )

    # --- Workflow B step 3: format the filtered set into the LLM-facing projection ---
    llm_view_items = [
        WardrobeItemLLMView.model_validate(item) for item in wardrobe_rows
    ]

    # --- Workflow B step 4: structured LLM call, forced to return exact item_ids ---
    selection = await get_outfit_recommendation(request.query, llm_view_items)

    # Guard against the (rare, given constrained decoding) case that the LLM
    # selected an item_id that isn't actually in the filtered set.
    valid_ids = {item.item_id for item in wardrobe_rows}
    returned_ids = set(selection.item_ids)
    if not returned_ids.issubset(valid_ids):
        raise HTTPException(
            status_code=502, detail="LLM returned item_ids not present in wardrobe."
        )

    # --- Workflow B step 5: resolve image URLs for the finalized outfit ---
    id_to_url = {
        item.item_id: item.processed_image_url or item.raw_image_url
        for item in wardrobe_rows
        if item.item_id in returned_ids
    }

    return OutfitResponse(
        item_ids=selection.item_ids,
        styling_notes=selection.styling_notes,
        image_urls=id_to_url,
    )