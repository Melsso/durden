from io import BytesIO

import pytest
from PIL import Image

from durden.utils import load_image


def test_load_image_returns_rgb():
    image = Image.new("RGBA", (20, 20), "red")

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    loaded = load_image(buffer.getvalue())

    assert loaded.mode == "RGB"
    assert loaded.size == (20, 20)


def test_load_image_invalid_bytes():
    with pytest.raises(Exception):
        load_image(b"not an image")
