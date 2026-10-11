import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from durden.schemas import APIStatusResponse, HealthResponse, PredictionResponse
from durden.services.detector import Detector
from durden.settings import settings
from durden.utils import InvalidImageError, load_image

logger = logging.getLogger("durden")

READ_CHUNK_SIZE = 1024 * 1024
MULTIPART_OVERHEAD = 64 * 1024


async def load_detector(app: FastAPI):
    try:
        detector = Detector(model_names=settings.models)
        await asyncio.to_thread(detector.load_models)
    except Exception:
        logger.exception("Model loading failed")
        app.state.model_error = "Model loading failed. Check the server logs."
        return

    app.state.detector = detector
    app.state.model_ready = True
    logger.info("Models ready: %s", ", ".join(settings.models))


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model_ready = False
    app.state.model_error = None
    app.state.detector = None
    app.state.created_at = datetime.now(UTC)

    app.state.load_task = None

    if settings.preload_models:
        await load_detector(app)
    else:
        app.state.load_task = asyncio.create_task(load_detector(app))

    try:
        yield
    finally:
        task = app.state.load_task
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(title="Durden Object Detection API", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if (
        request.method == "POST"
        and content_length
        and content_length.isdigit()
        and int(content_length) > settings.max_upload_bytes + MULTIPART_OVERHEAD
    ):
        return JSONResponse(
            status_code=413,
            content={"detail": _too_large_message()},
        )
    return await call_next(request)


def _too_large_message() -> str:
    return f"File too large. Maximum size is {settings.max_upload_bytes // (1024 * 1024)}MB."


async def read_limited(file: UploadFile, limit: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while chunk := await file.read(READ_CHUNK_SIZE):
        size += len(chunk)
        if size > limit:
            raise HTTPException(status_code=413, detail=_too_large_message())
        chunks.append(chunk)
    return b"".join(chunks)


@app.get("/", response_class=FileResponse, include_in_schema=False)
async def home():
    return FileResponse(settings.static_dir / "index.html")


@app.get("/about", response_class=FileResponse, include_in_schema=False)
async def about():
    return FileResponse(settings.static_dir / "about.html")


@app.get("/api-docs", response_class=FileResponse, include_in_schema=False)
async def api_docs():
    return FileResponse(settings.static_dir / "api_docs.html")


@app.post(
    "/predict",
    response_model=PredictionResponse,
    responses={
        400: {"description": "Invalid image or unknown model"},
        413: {"description": "File too large"},
        503: {"description": "Models are still loading (or failed to load)"},
    },
)
async def predict(
    request: Request,
    file: Annotated[UploadFile, File(description="JPEG, PNG or WEBP image")],
    model_name: Annotated[
        str | None, Query(description="Model to use; defaults to the first one")
    ] = None,
    conf: Annotated[
        float, Query(ge=0.0, le=1.0, description="Minimum confidence of returned boxes")
    ] = 0.25,
):
    state = request.app.state
    if not state.model_ready:
        raise HTTPException(status_code=503, detail="Models currently loading")

    image_bytes = await read_limited(file, settings.max_upload_bytes)

    try:
        image = await asyncio.to_thread(load_image, image_bytes, settings.max_image_pixels)
    except InvalidImageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        model_name, detections, time_ms = await asyncio.to_thread(
            state.detector.predict,
            image,
            model_name=model_name,
            conf=conf,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PredictionResponse(
        filename=file.filename or "upload",
        model_name=model_name,
        detections=detections,
        inference_time_ms=time_ms,
    )


@app.get("/health", response_model=HealthResponse)
async def health(request: Request):
    state = request.app.state
    if state.model_ready:
        status = "ok"
    elif state.model_error:
        status = "error"
    else:
        status = "loading"
    return HealthResponse(status=status, models_ready=state.model_ready)


@app.get("/ready", response_model=HealthResponse)
async def ready(request: Request):
    state = request.app.state
    if not state.model_ready:
        raise HTTPException(
            status_code=503,
            detail=state.model_error or "Models currently loading",
        )
    return HealthResponse(status="ok", models_ready=True)


@app.get("/status", response_model=APIStatusResponse)
async def status(request: Request):
    state = request.app.state
    return APIStatusResponse(
        name=settings.name,
        version=settings.version,
        environment=settings.env,
        started_at=state.created_at,
        models=state.detector.model_names if state.detector else [],
        model_state=state.model_ready,
        model_error=state.model_error,
    )
