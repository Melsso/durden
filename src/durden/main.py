import asyncio

from fastapi import FastAPI, UploadFile, File, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from datetime import datetime, timezone

from durden.schemas import PredictionResponse, APIStatusResponse
from durden.services.detector import Detector
from durden.utils import load_image

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


async def load_detector(app: FastAPI):
    await asyncio.to_thread(app.state.detector.load_models)
    app.state.model_ready = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    detector = Detector(model_names=["yolov8n.pt", "yolov8s.pt"])

    app.state.detector = detector
    app.state.created_at = datetime.now(timezone.utc)
    app.state.model_ready = False

    asyncio.create_task(load_detector(app))

    yield


app = FastAPI(title="Durden Object Detection API", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(html_path.read_text())


@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: Request,
    file: UploadFile = File(...),
    model_name: Annotated[str | None, Query()] = None,
):
    if not request.app.state.model_ready:
        raise HTTPException(status_code=503, detail="Models currently loading")
    image_bytes = await file.read()
    image = load_image(image_bytes)

    try:
        model_name, detections, time_ms = request.app.state.detector.predict(
            image,
            model_name=model_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return PredictionResponse(
        filename=file.filename,
        model_name=model_name,
        detections=detections,
        inference_time_ms=time_ms,
    )


@app.get("/health")
async def health(request: Request):
    return {"status": "ok", "models_ready": request.app.state.model_ready}


@app.get("/status")
async def status(request: Request):
    return APIStatusResponse(
        name="Durden Object Detection API",
        version="0.1.0",
        environment="development",
        started_at=request.app.state.created_at,
        models=request.app.state.detector.model_names,
        model_state=request.app.state.model_ready,
    )
