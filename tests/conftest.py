from contextlib import asynccontextmanager
from datetime import UTC, datetime
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from durden.main import app


@asynccontextmanager
async def lifespan_fixture(app):
    app.state.model_ready = False
    app.state.model_error = None
    app.state.created_at = datetime.now(UTC)
    app.state.detector = None
    yield


@pytest.fixture
def client():
    original = app.router.lifespan_context
    app.router.lifespan_context = lifespan_fixture

    with TestClient(app) as client:
        yield client

    app.router.lifespan_context = original


@pytest.fixture
def png_bytes():
    buffer = BytesIO()
    Image.new("RGB", (32, 32)).save(buffer, format="PNG")
    return buffer.getvalue()
