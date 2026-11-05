from celery import Celery

from config import settings

PROCESS_WARDROBE_ITEM_TASK = "tasks.ingestion.process_wardrobe_item_task"

celery_app = Celery(
    "wardrobe_stylist",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks.ingestion"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    result_expires=3600,
    task_acks_late=True,
)
