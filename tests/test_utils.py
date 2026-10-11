from io import BytesIO

import pytest
from PIL import Image

from durden.utils import InvalidImageError, load_image


def encode(image, fmt):
    buffer = BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


def test_load_image_returns_rgb():
    data = encode(Image.new("RGBA", (20, 20), "red"), "PNG")

    loaded = load_image(data)

    assert loaded.mode == "RGB"
    assert loaded.size == (20, 20)


@pytest.mark.parametrize("fmt", ["JPEG", "WEBP"])
def test_load_image_accepts_other_supported_formats(fmt):
    loaded = load_image(encode(Image.new("RGB", (8, 8)), fmt))

    assert loaded.size == (8, 8)


def test_load_image_invalid_bytes():
    with pytest.raises(InvalidImageError):
        load_image(b"not an image")


def test_load_image_unsupported_format():
    with pytest.raises(InvalidImageError, match="Unsupported"):
        load_image(encode(Image.new("RGB", (8, 8)), "GIF"))


def test_load_image_too_many_pixels():
    data = encode(Image.new("RGB", (20, 20)), "PNG")

    with pytest.raises(InvalidImageError, match="too large"):
        load_image(data, max_pixels=100)


def test_load_image_truncated_file():
    data = encode(Image.new("RGB", (64, 64), "red"), "PNG")

    with pytest.raises(InvalidImageError):
        load_image(data[:40])
