from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.orm import WardrobeItemORM, IngestionStatus
from schemas.wardrobe import WardrobeItem, WardrobeItemIngestAck
from services.storage import save_raw_upload
from tasks.ingestion import process_wardrobe_item_task

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])


@router.post(
    "/ingest",
    response_model=WardrobeItemIngestAck,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_wardrobe_item(
    image: UploadFile,
    user_id: UUID = Form(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        raw_image_url = await save_raw_upload(image)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc))

    item = WardrobeItemORM(
        user_id=user_id,
        raw_image_url=raw_image_url,
        status=IngestionStatus.PENDING,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    process_wardrobe_item_task.delay(str(item.item_id))

    return WardrobeItemIngestAck(item_id=item.item_id, status=item.status)


@router.get("/completed", response_model=list[WardrobeItem])
async def get_completed_items(
    user_id: str = Query(..., description="User ID to fetch completed wardrobe items for"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WardrobeItemORM).where(
        WardrobeItemORM.user_id == user_id,
        WardrobeItemORM.status == IngestionStatus.COMPLETED,
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    return items


@router.get("/{item_id}", response_model=WardrobeItem)
async def get_wardrobe_item(item_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(WardrobeItemORM).where(WardrobeItemORM.item_id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Wardrobe item not found.")
    return item
