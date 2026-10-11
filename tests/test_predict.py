from unittest.mock import MagicMock

from durden.main import app
from durden.schemas import Detection
from durden.settings import settings


def make_detector(model_name="yolov8n.pt"):
    detector = MagicMock()
    detector.predict.return_value = (
        model_name,
        [Detection(label="person", confidence=0.95, bbox=[1, 2, 3, 4])],
        12.4,
    )
    return detector


def post_image(client, content, url="/predict", filename="image.png"):
    return client.post(url, files={"file": (filename, content, "image/png")})


def test_predict_models_not_ready(client, png_bytes):
    response = post_image(client, png_bytes)

    assert response.status_code == 503


def test_predict_unknown_model(client, png_bytes):
    app.state.model_ready = True
    detector = MagicMock()
    detector.predict.side_effect = ValueError("Unknown model")
    app.state.detector = detector

    response = post_image(client, png_bytes, url="/predict?model_name=test.pt")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown model"


def test_predict_success(client, png_bytes):
    app.state.model_ready = True
    app.state.detector = make_detector()

    response = post_image(client, png_bytes)

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "image.png"
    assert body["model_name"] == "yolov8n.pt"
    assert body["inference_time_ms"] == 12.4
    assert body["detections"] == [{"label": "person", "confidence": 0.95, "bbox": [1, 2, 3, 4]}]


def test_predict_forwards_model_name_and_conf(client, png_bytes):
    app.state.model_ready = True
    detector = make_detector("yolov8s.pt")
    app.state.detector = detector

    response = post_image(client, png_bytes, url="/predict?model_name=yolov8s.pt&conf=0.4")

    assert response.status_code == 200
    _, kwargs = detector.predict.call_args
    assert kwargs["model_name"] == "yolov8s.pt"
    assert kwargs["conf"] == 0.4


def test_predict_rejects_out_of_range_conf(client, png_bytes):
    app.state.model_ready = True
    app.state.detector = make_detector()

    response = post_image(client, png_bytes, url="/predict?conf=1.5")

    assert response.status_code == 422


def test_predict_rejects_non_image(client):
    app.state.model_ready = True
    app.state.detector = make_detector()

    response = post_image(client, b"definitely not an image", filename="notes.txt")

    assert response.status_code == 400
    assert "valid image" in response.json()["detail"]
    app.state.detector.predict.assert_not_called()


def test_predict_rejects_oversized_file(client, png_bytes, monkeypatch):
    app.state.model_ready = True
    app.state.detector = make_detector()
    monkeypatch.setattr(settings, "max_upload_bytes", 10)
    monkeypatch.setattr("durden.main.MULTIPART_OVERHEAD", 10_000)

    response = post_image(client, png_bytes)

    assert response.status_code == 413


def test_predict_rejects_huge_content_length(client, png_bytes, monkeypatch):
    app.state.model_ready = True
    app.state.detector = make_detector()
    monkeypatch.setattr(settings, "max_upload_bytes", 10)
    monkeypatch.setattr("durden.main.MULTIPART_OVERHEAD", 0)

    response = post_image(client, png_bytes)

    assert response.status_code == 413
    assert "too large" in response.json()["detail"]


def test_predict_rejects_oversized_dimensions(client, png_bytes, monkeypatch):
    app.state.model_ready = True
    app.state.detector = make_detector()
    monkeypatch.setattr(settings, "max_image_pixels", 100)

    response = post_image(client, png_bytes)

    assert response.status_code == 400
    assert "too large" in response.json()["detail"]
