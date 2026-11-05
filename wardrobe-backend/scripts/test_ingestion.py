import asyncio
import mimetypes
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from pathlib import Path
from uuid import UUID

import httpx
from sqlalchemy import select

from database import AsyncSessionLocal
from models.orm import WardrobeItemORM, IngestionStatus

BACKEND_URL = "http://127.0.0.1:8000"
DEFAULT_IMAGE_PATH = Path("test_data/test_clothing.jpg")


async def poll_item_status(item_id: UUID, timeout: int = 60) -> WardrobeItemORM:
    for _ in range(timeout // 2):
        # A new session per poll: reusing one returns the cached row with its old status.
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WardrobeItemORM).where(WardrobeItemORM.item_id == item_id)
            )
            item = result.scalar_one_or_none()
        if item is None:
            raise RuntimeError(f"Item {item_id} not found")
        if item.status != IngestionStatus.PROCESSING and item.status != IngestionStatus.PENDING:
            return item
        await asyncio.sleep(2)
    raise TimeoutError(f"Item {item_id} still {item.status.value} after {timeout}s")


async def main() -> None:
    image_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IMAGE_PATH
    if not image_path.exists():
        raise FileNotFoundError(f"Missing test image at {image_path}")
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"

    async with httpx.AsyncClient() as client:
        with image_path.open("rb") as image_file:
            response = await client.post(
                f"{BACKEND_URL}/wardrobe/ingest",
                data={"user_id": "00000000-0000-0000-0000-000000000001"},
                files={"image": (image_path.name, image_file, mime_type)},
            )

    response.raise_for_status()
    item_id = UUID(response.json()["item_id"])
    print("Ingestion started for", item_id)

    item = await poll_item_status(item_id)

    print("Final status:", item.status)
    print("Processed image URL:", item.processed_image_url)
    # pgvector returns a numpy array, which has no single truth value.
    print("Embedding length:", len(item.style_embedding) if item.style_embedding is not None else None)
    print("Primary color:", item.primary_color)
    print("Category:", item.category)

    assert item.status == IngestionStatus.COMPLETED
    assert item.processed_image_url is not None
    assert item.style_embedding is not None and len(item.style_embedding) == 768
    assert item.primary_color is not None
    assert item.category is not None


if __name__ == "__main__":
    asyncio.run(main())
