"""Image validation and resizing for listing photos."""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import get_settings

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class ImageValidationError(ValueError):
    pass


@dataclass
class ProcessedImage:
    web: bytes
    thumb: bytes
    content_type: str = "image/webp"
    extension: str = "webp"


def process_image(data: bytes) -> ProcessedImage:
    """Validate (jpg/png/webp, <= max size) and produce a web-size and a thumbnail WebP."""
    s = get_settings()
    if len(data) > s.max_image_bytes:
        raise ImageValidationError(f"Image is larger than {s.max_image_bytes // (1024 * 1024)} MB")
    try:
        img = Image.open(io.BytesIO(data))
        fmt = img.format
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageValidationError("File is not a valid image") from exc
    if fmt not in ALLOWED_FORMATS:
        raise ImageValidationError("Only JPG, PNG and WebP images are allowed")

    img = ImageOps.exif_transpose(img).convert("RGB")

    web = img.copy()
    web.thumbnail((s.image_web_max_px, s.image_web_max_px), Image.Resampling.LANCZOS)
    thumb = ImageOps.fit(img, s.image_thumb_size, Image.Resampling.LANCZOS)

    return ProcessedImage(web=_to_webp(web, 82), thumb=_to_webp(thumb, 75))


def _to_webp(img: Image.Image, quality: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=4)
    return buf.getvalue()
