from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image

from durden.main import app
from durden.schemas import Detection


def make_image():
    image = Image.new("RGB", (32, 32))

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return buffer.getvalue()


def test_predict_models_not_ready(client):
    app.state.model_ready = False

    response = client.post(
        "/predict",
        files={"file": ("image.png", make_image(), "image/png")},
    )

    assert response.status_code == 503


def test_predict_unknown_model(client):
    app.state.model_ready = True

    detector = MagicMock()
    detector.predict.side_effect = ValueError("Unknown model")

    app.state.detector = detector

    response = client.post(
        "/predict?model_name=test.pt",
        files={"file": ("image.png", make_image(), "image/png")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown model"


def test_predict_success(client):
    app.state.model_ready = True

    detector = MagicMock()

    detector.predict.return_value = (
        "yolov8n.pt",
        [
            Detection(
                label="person",
                confidence=0.95,
                bbox=[1, 2, 3, 4],
            )
        ],
        12.4,
    )

    app.state.detector = detector

    with patch("durden.main.load_image") as mock_load:
        mock_load.return_value = MagicMock()

        response = client.post(
            "/predict",
            files={"file": ("image.png", make_image(), "image/png")},
        )

    assert response.status_code == 200

    body = response.json()

    assert body["filename"] == "image.png"
    assert body["model_name"] == "yolov8n.pt"
    assert len(body["detections"]) == 1
    assert body["detections"][0] == {
        "label": "person",
        "confidence": 0.95,
        "bbox": [1, 2, 3, 4],
    }
