from datetime import datetime, timezone
from unittest.mock import MagicMock

from durden.main import app, settings


def test_status(client):
    app.state.created_at = datetime.now(timezone.utc)

    detector = MagicMock()
    detector.model_names = ["yolov8n.pt"]

    app.state.detector = detector
    app.state.model_ready = True

    response = client.get("/status")

    assert response.status_code == 200

    body = response.json()

    assert body["name"] == settings.name
    assert body["version"] == settings.version
    assert body["environment"] == settings.env
    assert body["models"] == ["yolov8n.pt"]
    assert body["model_state"] is True
