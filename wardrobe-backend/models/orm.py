import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum as SAEnum, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from pgvector.sqlalchemy import Vector

EMBEDDING_DIM = 768  # SigLIP base — see Step 3 note

class Base(DeclarativeBase):
    pass

class IngestionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GarmentCategory(str, enum.Enum):
    TOP = "top"
    BOTTOM = "bottom"
    OUTERWEAR = "outerwear"
    DRESS = "dress"
    FOOTWEAR = "footwear"
    ACCESSORY = "accessory"

class WardrobeItemORM(Base):
    __tablename__ = "wardrobe_items"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    raw_image_url: Mapped[str] = mapped_column(Text, nullable=False)
    processed_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[IngestionStatus] = mapped_column(
        SAEnum(IngestionStatus, name="ingestion_status"),
        default=IngestionStatus.PENDING,
        nullable=False,
        index=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[GarmentCategory | None] = mapped_column(
        SAEnum(GarmentCategory, name="garment_category"), nullable=True, index=True
    )
    sub_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pattern: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    material: Mapped[str | None] = mapped_column(String(64), nullable=True)
    season_tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    style_embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index(
            "ix_wardrobe_items_style_embedding",
            "style_embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"style_embedding": "vector_cosine_ops"},
        ),
        Index("ix_wardrobe_user_category", "user_id", "category"),
    )