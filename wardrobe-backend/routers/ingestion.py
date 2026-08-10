from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.orm import WardrobeItemORM, IngestionStatus
from schemas.wardrobe import WardrobeItemIngestAck
from services.storage import save_raw_upload
from tasks.ingestion import process_wardrobe_item_task

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])


@router.post(
    "/ingest",
    response_model=WardrobeItemIngestAck,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_wardrobe_item(
    user_id: UUID,
    image: UploadFile,
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
