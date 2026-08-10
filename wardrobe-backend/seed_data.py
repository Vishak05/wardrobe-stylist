import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uuid
from database import AsyncSessionLocal
from models.orm import WardrobeItemORM, IngestionStatus, GarmentCategory

SAMPLE_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

SAMPLE_ITEMS = [
    dict(
        raw_image_url="https://placehold.co/400x400?text=White+Tee",
        processed_image_url="https://placehold.co/400x400?text=White+Tee",
        category=GarmentCategory.TOP,
        sub_category="t-shirt",
        primary_color="white",
        pattern="solid",
        fit="regular",
        material="cotton",
        season_tags=["summer", "spring"],
    ),
    dict(
        raw_image_url="https://placehold.co/400x400?text=Denim+Jacket",
        processed_image_url="https://placehold.co/400x400?text=Denim+Jacket",
        category=GarmentCategory.OUTERWEAR,
        sub_category="jacket",
        primary_color="blue",
        pattern="solid",
        fit="regular",
        material="denim",
        season_tags=["spring", "fall"],
    ),
    dict(
        raw_image_url="https://placehold.co/400x400?text=Black+Jeans",
        processed_image_url="https://placehold.co/400x400?text=Black+Jeans",
        category=GarmentCategory.BOTTOM,
        sub_category="jeans",
        primary_color="black",
        pattern="solid",
        fit="slim",
        material="denim",
        season_tags=["fall", "winter", "spring"],
    ),
    dict(
        raw_image_url="https://placehold.co/400x400?text=White+Sneakers",
        processed_image_url="https://placehold.co/400x400?text=White+Sneakers",
        category=GarmentCategory.FOOTWEAR,
        sub_category="sneakers",
        primary_color="white",
        pattern="solid",
        fit=None,
        material="leather",
        season_tags=["summer", "spring", "fall"],
    ),
    dict(
        raw_image_url="https://placehold.co/400x400?text=Navy+Blazer",
        processed_image_url="https://placehold.co/400x400?text=Navy+Blazer",
        category=GarmentCategory.OUTERWEAR,
        sub_category="blazer",
        primary_color="navy",
        pattern="solid",
        fit="slim",
        material="wool",
        season_tags=["fall", "winter"],
    ),
    dict(
        raw_image_url="https://placehold.co/400x400?text=Floral+Dress",
        processed_image_url="https://placehold.co/400x400?text=Floral+Dress",
        category=GarmentCategory.DRESS,
        sub_category="sundress",
        primary_color="yellow",
        pattern="floral",
        fit="regular",
        material="linen",
        season_tags=["summer"],
    ),
]


async def seed():
    async with AsyncSessionLocal() as session:
        for item_data in SAMPLE_ITEMS:
            item = WardrobeItemORM(
                user_id=SAMPLE_USER_ID,
                status=IngestionStatus.COMPLETED,
                **item_data,
            )
            session.add(item)
        await session.commit()
    print(f"Seeded {len(SAMPLE_ITEMS)} items for user_id={SAMPLE_USER_ID}")


if __name__ == "__main__":
    asyncio.run(seed())