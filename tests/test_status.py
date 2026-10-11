from unittest.mock import MagicMock

from durden.main import app, settings


def test_status(client):
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
    assert body["model_error"] is None


def test_status_before_detector_exists(client):
    response = client.get("/status")

    assert response.status_code == 200
    body = response.json()
    assert body["models"] == []
    assert body["model_state"] is False


def test_status_reports_model_error(client):
    app.state.model_error = "Model loading failed. Check the server logs."

    body = client.get("/status").json()

    assert body["model_state"] is False
    assert body["model_error"] == "Model loading failed. Check the server logs."
