import io

import pytest
from PIL import Image

from app.images import ImageValidationError, process_image
from app.storage import LocalFileStorage


def _img_bytes(fmt: str, size=(2400, 1600)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 120, 80)).save(buf, format=fmt)
    return buf.getvalue()


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
def test_process_allowed_formats(fmt) -> None:
    out = process_image(_img_bytes(fmt))
    web = Image.open(io.BytesIO(out.web))
    thumb = Image.open(io.BytesIO(out.thumb))
    assert max(web.size) == 1600
    assert thumb.size == (480, 320)


def test_rejects_gif_and_garbage() -> None:
    with pytest.raises(ImageValidationError):
        process_image(_img_bytes("GIF", (50, 50)))
    with pytest.raises(ImageValidationError):
        process_image(b"not an image")


def test_rejects_oversize() -> None:
    with pytest.raises(ImageValidationError):
        process_image(b"0" * (5 * 1024 * 1024 + 1))


def test_local_storage_roundtrip_and_traversal(tmp_path) -> None:
    s = LocalFileStorage(str(tmp_path), "/uploads")
    url = s.save("listings/1/abc_web.webp", b"x", "image/webp")
    assert url == "/uploads/listings/1/abc_web.webp"
    assert s.exists("listings/1/abc_web.webp")
    s.delete_prefix("listings/1/abc")
    assert not s.exists("listings/1/abc_web.webp")
    with pytest.raises(ValueError):
        s.save("../escape.txt", b"x", "text/plain")
