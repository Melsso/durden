import asyncio

from fastapi import FastAPI, UploadFile, File, Request, Query, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager
from typing import Annotated
from datetime import datetime, timezone

from durden.schemas import PredictionResponse, APIStatusResponse
from durden.services.detector import Detector
from durden.utils import load_image
from durden.settings import settings


async def load_detector(app: FastAPI):
    detector = Detector(model_names=settings.models)

    await asyncio.to_thread(detector.load_models)
    app.state.detector = detector
    app.state.model_ready = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model_ready = False
    app.state.detector = None
    app.state.created_at = datetime.now(timezone.utc)

    asyncio.create_task(load_detector(app))

    yield


app = FastAPI(title="Durden Object Detection API", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")


@app.get("/", response_class=FileResponse)
async def home():
    return FileResponse(settings.static_dir / "index.html")


@app.get("/about", response_class=FileResponse)
async def about():
    return FileResponse(settings.static_dir / "about.html")


@app.get("/api-docs", response_class=FileResponse)
async def api_docs():
    return FileResponse(settings.static_dir / "api_docs.html")


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
        name=settings.name,
        version=settings.version,
        environment=settings.env,
        started_at=request.app.state.created_at,
        models=request.app.state.detector.model_names
        if request.app.state.detector
        else [],
        model_state=request.app.state.model_ready,
    )
