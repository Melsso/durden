from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient

from durden.main import app


@asynccontextmanager
async def lifespan_fixture(app):
    app.state.model_ready = False
    app.state.created_at = None
    app.state.detector = None

    yield


@pytest.fixture
def client():
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = lifespan_fixture

    with TestClient(app) as client:
        yield client

    app.router.lifespan_context = original_lifespan

def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "models_ready": False,
    }