import time
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from durden.main import app
from durden.settings import settings


def wait_for(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_real_lifespan_loads_models_in_background():
    with patch("durden.main.Detector") as mock_detector_cls:
        mock_detector_cls.return_value = MagicMock(model_names=["a.pt"])

        with TestClient(app) as client:
            assert wait_for(lambda: client.get("/health").json()["models_ready"])

            assert client.get("/health").json()["status"] == "ok"
            assert client.get("/ready").status_code == 200
            assert client.get("/status").json()["models"] == ["a.pt"]

    mock_detector_cls.return_value.load_models.assert_called_once()


def test_preload_models_are_ready_before_first_request(monkeypatch):
    monkeypatch.setattr(settings, "preload_models", True)

    with patch("durden.main.Detector") as mock_detector_cls:
        mock_detector_cls.return_value = MagicMock(model_names=["a.pt"])

        with TestClient(app) as client:
            assert client.get("/health").json() == {"status": "ok", "models_ready": True}
            assert client.get("/ready").status_code == 200


def test_preload_failure_still_starts_and_reports_error(monkeypatch):
    monkeypatch.setattr(settings, "preload_models", True)

    with patch("durden.main.Detector") as mock_detector_cls:
        mock_detector_cls.return_value.load_models.side_effect = RuntimeError("no weights")

        with TestClient(app) as client:
            assert client.get("/health").json()["status"] == "error"
            assert client.get("/ready").status_code == 503


def test_real_lifespan_reports_model_loading_failure():
    with patch("durden.main.Detector") as mock_detector_cls:
        mock_detector_cls.return_value.load_models.side_effect = RuntimeError("no weights")

        with TestClient(app) as client:
            assert wait_for(lambda: client.get("/health").json()["status"] == "error")

            assert client.get("/ready").status_code == 503
            status = client.get("/status").json()
            assert status["model_state"] is False
            assert "no weights" not in status["model_error"]
