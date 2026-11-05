import asyncio
import logging
from pathlib import Path

from google import genai
from google.genai import types
from rembg import remove
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from config import settings
from core.celery_app import PROCESS_WARDROBE_ITEM_TASK, celery_app
from models.orm import WardrobeItemORM, IngestionStatus
from schemas.wardrobe_metadata import VisionMetadata
from services.embedding import generate_image_embedding
from services.storage import MEDIA_ROOT, local_path_from_url, save_processed_image

logger = logging.getLogger(__name__)
client = genai.Client(api_key=settings.gemini_api_key)

# Each task runs on its own event loop, and a pooled connection can't outlive the
# loop it was opened on, so the worker opens a fresh connection per session.
_engine = create_async_engine(settings.database_url, poolclass=NullPool)
WorkerSessionLocal = async_sessionmaker(_engine, expire_on_commit=False)

VISION_SYSTEM_INSTRUCTION = (
    "You are a garment image metadata extractor. Given a clothing photo, return a JSON object "
    "with category, sub_category, primary_color, pattern, fit, material, formality_score, "
    "and weather_suitability. Use only the information visible in the image."
)


def _extract_metadata(processed_image_path: Path) -> VisionMetadata:
    with processed_image_path.open("rb") as image_file:
        image_bytes = image_file.read()

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            "Analyze the attached clothing image and return structured metadata.",
        ],
        config=types.GenerateContentConfig(
            system_instruction=VISION_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=VisionMetadata,
        ),
    )

    return response.parsed


async def _process_wardrobe_item(item_id: str) -> None:
    async with WorkerSessionLocal() as db:
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
            raw_path = local_path_from_url(item.raw_image_url)
            with raw_path.open("rb") as raw_image_file:
                input_bytes = raw_image_file.read()

            output_bytes = remove(input_bytes)
            processed_image_url = save_processed_image(output_bytes, raw_path.with_suffix(".png").name)
            metadata_path = MEDIA_ROOT / processed_image_url.lstrip("/media/")
            metadata = _extract_metadata(metadata_path)
            embedding = generate_image_embedding(metadata_path)

            await db.execute(
                update(WardrobeItemORM)
                .where(WardrobeItemORM.item_id == item_id)
                .values(
                    processed_image_url=processed_image_url,
                    category=metadata.category,
                    sub_category=metadata.sub_category,
                    primary_color=metadata.primary_color,
                    pattern=metadata.pattern,
                    fit=metadata.fit,
                    material=metadata.material,
                    season_tags=metadata.weather_suitability,
                    style_embedding=embedding,
                    status=IngestionStatus.COMPLETED,
                )
            )
            await db.commit()
        except Exception as exc:
            logger.exception("Failed processing wardrobe item %s", item_id)
            # A database error aborts the transaction, so the update below would fail too.
            await db.rollback()
            await db.execute(
                update(WardrobeItemORM)
                .where(WardrobeItemORM.item_id == item_id)
                .values(status=IngestionStatus.FAILED, failure_reason=str(exc))
            )
            await db.commit()
            raise


@celery_app.task(name=PROCESS_WARDROBE_ITEM_TASK)
def process_wardrobe_item_task(item_id: str) -> None:
    # psycopg's async mode can't use the ProactorEventLoop that Windows defaults to.
    with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
        runner.run(_process_wardrobe_item(item_id))
