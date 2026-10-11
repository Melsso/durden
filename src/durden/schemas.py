from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Detection(BaseModel):
    label: str
    confidence: float
    bbox: list[int]


class PredictionResponse(BaseModel):
    filename: str
    model_name: str
    detections: list[Detection]
    inference_time_ms: float

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "filename": "city_street.jpg",
                    "model_name": "yolov8n.pt",
                    "detections": [
                        {
                            "label": "car",
                            "confidence": 0.94,
                            "bbox": [120, 280, 420, 520],
                        }
                    ],
                    "inference_time_ms": 132.4,
                }
            ]
        }
    )


class HealthResponse(BaseModel):
    status: str
    models_ready: bool

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "ok", "models_ready": True}]}
    )


class APIStatusResponse(BaseModel):
    name: str
    version: str
    environment: str
    started_at: datetime
    models: list[str]
    model_state: bool
    model_error: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Durden Object Detection API",
                    "version": "0.1.0",
                    "environment": "production",
                    "started_at": "2026-07-09T08:12:43Z",
                    "models": ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"],
                    "model_state": True,
                    "model_error": None,
                }
            ]
        }
    )
