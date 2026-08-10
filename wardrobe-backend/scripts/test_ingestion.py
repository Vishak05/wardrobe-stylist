import asyncio
from pathlib import Path
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models.orm import WardrobeItemORM, IngestionStatus

BACKEND_URL = "http://127.0.0.1:8000"
TEST_IMAGE_PATH = Path("test_data/test_clothing.jpg")


async def poll_item_status(item_id: UUID, timeout: int = 60) -> WardrobeItemORM | None:
    async with AsyncSessionLocal() as session:
        for _ in range(timeout // 2):
            result = await session.execute(
                select(WardrobeItemORM).where(WardrobeItemORM.item_id == item_id)
            )
            item = result.scalar_one_or_none()
            if item is None:
                return None
            if item.status != IngestionStatus.PROCESSING and item.status != IngestionStatus.PENDING:
                return item
            await asyncio.sleep(2)
    return None


async def main() -> None:
    if not TEST_IMAGE_PATH.exists():
        raise FileNotFoundError(f"Missing test image at {TEST_IMAGE_PATH}")

    async with httpx.AsyncClient() as client:
        with TEST_IMAGE_PATH.open("rb") as image_file:
            response = await client.post(
                f"{BACKEND_URL}/wardrobe/ingest",
                data={"user_id": "00000000-0000-0000-0000-000000000001"},
                files={"image": (TEST_IMAGE_PATH.name, image_file, "image/jpeg")},
            )

    response.raise_for_status()
    item_id = UUID(response.json()["item_id"])
    print("Ingestion started for", item_id)

    item = await poll_item_status(item_id)
    if item is None:
        raise RuntimeError("Item was not found during polling")

    print("Final status:", item.status)
    print("Processed image URL:", item.processed_image_url)
    print("Embedding length:", len(item.style_embedding) if item.style_embedding else None)
    print("Primary color:", item.primary_color)
    print("Category:", item.category)

    assert item.status == IngestionStatus.COMPLETED
    assert item.processed_image_url is not None
    assert item.style_embedding is not None and len(item.style_embedding) == 768
    assert item.primary_color is not None
    assert item.category is not None


if __name__ == "__main__":
    asyncio.run(main())
