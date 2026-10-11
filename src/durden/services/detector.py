import threading
import time

from ultralytics import YOLO

from durden.schemas import Detection


class Detector:
    def __init__(self, model_names: list[str]):
        self.model_names = model_names
        self.active_model = None
        self.models: dict[str, YOLO] = {}
        self._lock = threading.Lock()

    def load_models(self):
        for name in self.model_names:
            self.models[name] = YOLO(name)
        self.active_model = self.model_names[0]

    def predict(self, image, model_name: str | None = None, conf: float = 0.25):
        model_name = model_name or self.active_model
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        model = self.models[model_name]

        with self._lock:
            start = time.perf_counter()
            results = model(image, conf=conf, verbose=False)
            elapsed = (time.perf_counter() - start) * 1000

        result = results[0]
        detections = []

        for box in result.boxes:
            class_id = int(box.cls[0])

            detections.append(
                Detection(
                    label=result.names[class_id],
                    confidence=float(box.conf[0]),
                    bbox=[int(x) for x in box.xyxy[0].tolist()],
                )
            )

        return model_name, detections, elapsed
