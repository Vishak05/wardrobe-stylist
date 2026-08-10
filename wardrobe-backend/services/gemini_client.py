from google import genai
from google.genai import types

from config import settings
from schemas.outfit import LLMOutfitSelection
from schemas.wardrobe import WardrobeItemLLMView

client = genai.Client(api_key=settings.gemini_api_key)

SYSTEM_INSTRUCTION = (
    "You are a wardrobe stylist. You will be given a user's styling request and a JSON "
    "array representing their available wardrobe items. Select the item_ids that best "
    "form a coherent outfit matching the request. You MUST only select item_ids that "
    "appear in the provided wardrobe array — never invent an item_id."
)


async def get_outfit_recommendation(
    query: str, wardrobe_items: list[WardrobeItemLLMView]
) -> LLMOutfitSelection:
    wardrobe_json = [item.model_dump(mode="json") for item in wardrobe_items]

    response = await client.aio.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            f"User request: {query}",
            f"Available wardrobe items: {wardrobe_json}",
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=LLMOutfitSelection,
        ),
    )

    return response.parsed