from pydantic import BaseModel, Field


class VisionMetadata(BaseModel):
    category: str = Field(..., description="High-level garment category")
    sub_category: str = Field(..., description="More specific garment type")
    primary_color: str = Field(..., description="Dominant color of the garment")
    pattern: str | None = Field(None, description="Detected pattern or print")
    fit: str | None = Field(None, description="Fit or silhouette description")
    material: str | None = Field(None, description="Primary fabric/material")
    formality_score: float = Field(..., description="Formality score from 0 to 1")
    weather_suitability: list[str] = Field(..., description="Weather tags like warm, rain, cold")
