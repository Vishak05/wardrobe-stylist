import logging

from celery import shared_task
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.celery_app import celery_app
from database import AsyncSessionLocal
from models.orm import WardrobeItemORM, IngestionStatus

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.ingestion.process_wardrobe_item_task")
async def process_wardrobe_item_task(item_id: str) -> None:
    async with AsyncSessionLocal() as db:
        stmt = select(WardrobeItemORM).where(WardrobeItemORM.item_id == item_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if item is None:
            logger.error("Wardrobe item not found for ingestion: %s", item_id)
            return

        await db.execute(
            update(WardrobeItemORM)
            .where(WardrobeItemORM.item_id == item_id)
            .values(status=IngestionStatus.PROCESSING)
        )
        await db.commit()

        try:
            # Placeholder for future ingestion steps.
            logger.info("Processing wardrobe item %s", item_id)
            # Worker should perform background removal, metadata extraction, and embedding.
        except Exception as exc:
            logger.exception("Failed processing wardrobe item %s", item_id)
            await db.execute(
                update(WardrobeItemORM)
                .where(WardrobeItemORM.item_id == item_id)
                .values(status=IngestionStatus.FAILED, failure_reason=str(exc))
            )
            await db.commit()
            raise
