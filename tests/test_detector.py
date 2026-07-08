from unittest.mock import MagicMock, patch

import pytest

from durden.services.detector import Detector


def test_load_models():
    detector = Detector(["model1.pt", "model2.pt"])

    with patch("durden.services.detector.YOLO") as mock_yolo:
        detector.load_models()

    assert detector.active_model == "model1.pt"
    assert len(detector.models) == 2
    assert mock_yolo.call_count == 2


def test_predict_unknown_model():
    detector = Detector(["a.pt"])
    detector.models = {"a.pt": MagicMock()}
    detector.active_model = "a.pt"

    with pytest.raises(ValueError):
        detector.predict(None, "missing.pt")


def test_predict_returns_detection():
    detector = Detector(["a.pt"])

    mock_box = MagicMock()
    mock_box.cls = [0]
    mock_box.conf = [0.91]

    coords = MagicMock()
    coords.tolist.return_value = [1, 2, 3, 4]
    mock_box.xyxy = [coords]

    result = MagicMock()
    result.names = {0: "person"}
    result.boxes = [mock_box]

    model = MagicMock()
    model.return_value = [result]

    detector.models = {"a.pt": model}
    detector.active_model = "a.pt"

    model_name, detections, elapsed = detector.predict(None)

    assert model_name == "a.pt"
    assert len(detections) == 1
    assert detections[0].label == "person"
    assert detections[0].bbox == [1, 2, 3, 4]
    assert elapsed >= 0
