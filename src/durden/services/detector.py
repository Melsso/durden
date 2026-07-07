import time

from ultralytics import YOLO
from typing import List

from durden.schemas import Detection


class Detector:
    def __init__(self, model_names: List[str]):
        self.model_names = model_names
        self.active_model = None
        self.models = {}

    def load_models(self):
        for name in self.model_names:
            self.models[name] = YOLO(name)
        self.active_model = self.model_names[0]

    def predict(self, image, model_name: str | None = None):
        start = time.perf_counter()

        model_name = model_name or self.active_model
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        model = self.models[model_name]

        results = model(image)
        detections = []
        result = results[0]

        for box in result.boxes:
            class_id = int(box.cls[0])
            label = result.names[class_id]

            detections.append(
                Detection(
                    label=label,
                    confidence=float(box.conf[0]),
                    bbox=[int(x) for x in box.xyxy[0].tolist()],
                )
            )

        elapsed = (time.perf_counter() - start) * 1000

        return model_name, detections, elapsed
