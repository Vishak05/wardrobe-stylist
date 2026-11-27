import asyncio
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image

MEDIA_ROOT = Path(__file__).resolve().parents[1] / "media"
RAW_DIR = MEDIA_ROOT / "raw"
PROCESSED_DIR = MEDIA_ROOT / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 50_000_000

_DECODERS = ("JPEG", "PNG", "WEBP")
# Phone cameras often write multi-picture JPEGs, which the JPEG decoder reports as MPO.
_EXTENSION_BY_FORMAT = {"JPEG": ".jpg", "MPO": ".jpg", "PNG": ".png", "WEBP": ".webp"}


class UploadTooLargeError(ValueError):
    pass


def _validated_extension(data: bytes) -> str:
    """Identify the image from its bytes, as the client's filename and Content-Type are untrusted."""
    try:
        with Image.open(BytesIO(data), formats=_DECODERS) as image:
            image_format = image.format
            width, height = image.size
            image.verify()
    except Image.DecompressionBombError as exc:
        raise UploadTooLargeError(f"Image exceeds {MAX_IMAGE_PIXELS} pixels.") from exc
    except (OSError, SyntaxError, ValueError) as exc:
        raise ValueError("File is not a valid JPEG, PNG or WebP image.") from exc

    # Checked from the header, as the worker would otherwise decode it all into memory.
    if width * height > MAX_IMAGE_PIXELS:
        raise UploadTooLargeError(f"Image exceeds {MAX_IMAGE_PIXELS} pixels.")
    return _EXTENSION_BY_FORMAT[image_format]


def _store_raw_image(data: bytes) -> str:
    file_name = f"{uuid4().hex}{_validated_extension(data)}"
    (RAW_DIR / file_name).write_bytes(data)
    return f"/media/raw/{file_name}"


async def save_raw_upload(upload_file: UploadFile) -> str:
    contents = await upload_file.read(MAX_UPLOAD_BYTES + 1)
    if len(contents) > MAX_UPLOAD_BYTES:
        raise UploadTooLargeError(f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    return await asyncio.to_thread(_store_raw_image, contents)


def save_processed_image(data: bytes, filename: str | None = None) -> str:
    ext = filename and Path(filename).suffix.lower() or ".png"
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        ext = ".png"

    file_name = filename or f"{uuid4().hex}{ext}"
    target_path = PROCESSED_DIR / file_name
    target_path.write_bytes(data)
    return f"/media/processed/{file_name}"


def local_path_from_url(url: str) -> Path:
    if url.startswith("/media/"):
        relative = url[len("/media/"):].lstrip("/\\")
        return MEDIA_ROOT / relative
    raise ValueError(f"Cannot resolve non-media URL to local path: {url}")
