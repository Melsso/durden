from pydantic import BaseModel
from datetime import datetime
from typing import List


class Detection(BaseModel):
    label: str
    confidence: float
    bbox: List[int]


class PredictionResponse(BaseModel):
    filename: str
    model_name: str
    detections: List[Detection]
    inference_time_ms: float


class APIStatusResponse(BaseModel):
    name: str
    version: str
    environment: str
    started_at: datetime
    models: List[str]
    model_state: bool
