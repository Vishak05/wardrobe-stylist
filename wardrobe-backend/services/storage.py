from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

MEDIA_ROOT = Path(__file__).resolve().parents[1] / "media"
RAW_DIR = MEDIA_ROOT / "raw"
PROCESSED_DIR = MEDIA_ROOT / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _ensure_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return suffix if suffix else ".jpg"


async def save_raw_upload(upload_file: UploadFile, filename: str | None = None) -> str:
    if upload_file.content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported MIME type: {upload_file.content_type}")

    ext = _ensure_extension(upload_file.filename)
    file_name = filename or f"{uuid4().hex}{ext}"
    target_path = RAW_DIR / file_name

    contents = await upload_file.read()
    target_path.write_bytes(contents)
    return f"/media/raw/{file_name}"


def save_processed_image(data: bytes, filename: str | None = None) -> str:
    ext = filename and Path(filename).suffix.lower() or ".png"
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        ext = ".png"

    file_name = filename or f"{uuid4().hex}{ext}"
    target_path = PROCESSED_DIR / file_name
    target_path.write_bytes(data)
    return f"/media/processed/{file_name}"
