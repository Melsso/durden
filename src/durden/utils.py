from io import BytesIO

from PIL import Image, UnidentifiedImageError

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
DEFAULT_MAX_PIXELS = 50_000_000


class InvalidImageError(ValueError):
    """Raised when uploaded bytes are not a supported, reasonably sized image."""


def load_image(image_bytes: bytes, max_pixels: int = DEFAULT_MAX_PIXELS):
    try:
        image = Image.open(BytesIO(image_bytes))

        if image.format not in ALLOWED_FORMATS:
            raise InvalidImageError("Unsupported image format. Use JPEG, PNG or WEBP.")

        if image.width * image.height > max_pixels:
            raise InvalidImageError("Image dimensions are too large.")

        return image.convert("RGB")
    except InvalidImageError:
        raise
    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        OSError,
        SyntaxError,
        ValueError,
    ) as exc:
        raise InvalidImageError("Uploaded file is not a valid image.") from exc
