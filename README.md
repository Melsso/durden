# Durden
![CI](https://github.com/Melsso/durden/actions/workflows/ci.yml/badge.svg)

A production-style object detection API built with **FastAPI** and **YOLO**. Durden exposes a REST interface for image analysis, plus a small web UI: upload an image, pick a model, and get labels, confidence scores and bounding boxes drawn on top of it.

The project demonstrates backend engineering practices alongside machine learning inference: background model loading, input validation, containerisation, automated testing, CI/CD and cloud deployment.

## Demo

![Durden Demo](https://github.com/user-attachments/assets/80968b90-f4f0-4162-9c13-e7d59695bc92)

## Features

- REST API for object detection (`POST /predict`)
- Multiple YOLO models, selectable per request (`model_name`)
- Adjustable confidence threshold (`conf`)
- Models load in the background at startup, so the API answers `/health` immediately and `/predict` returns `503` until they are ready (a failed load is reported instead of hanging forever)
- Inference runs in a worker thread, so health and status endpoints stay responsive under load
- Input validation: JPEG/PNG/WEBP only, 10 MB size limit, decompression-bomb protection
- Structured responses: labels, confidence scores, bounding boxes, inference time
- `/health`, `/ready` and `/status` endpoints
- Plain HTML/CSS/JS frontend (no build step) with live system status
- Automated tests with `pytest` and coverage
- Docker image with model weights baked in, running as a non-root user
- CI/CD with GitHub Actions: lint, format check, dependency check and tests on every branch; tag-triggered image build, Cloud Run deploy, smoke test and GitHub Release

---

## Architecture

```text
             +-------------+
             |   Client    |
             +------+------+
                    |
                    v
             +------+------+
             |   FastAPI   |   validation, size limits, status
             +------+------+
                    |   (worker thread)
                    v
             +------+------+
             |  Detector   |   one lock around inference
             |   Service   |
             +------+------+
                    |
                    v
             +------+------+
             | YOLO Models |   loaded once, in the background
             +-------------+
```

---

## API Endpoints

Interactive docs are available at `/docs` (Swagger UI) and `/redoc`.

### `POST /predict`

Performs object detection on an uploaded image.

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `file` | form | Image | yes | JPEG, PNG or WEBP, up to 10 MB |
| `model_name` | query | string | no | Model to use (defaults to the first configured model) |
| `conf` | query | float 0-1 | no | Minimum confidence of returned boxes (default `0.25`) |

```bash
curl -X POST "http://localhost:8000/predict?model_name=yolov8n.pt&conf=0.25" \
  -F "file=@city_street.jpg"
```

```json
{
  "filename": "city_street.jpg",
  "model_name": "yolov8n.pt",
  "detections": [
    {
      "label": "car",
      "confidence": 0.94,
      "bbox": [120, 280, 420, 520]
    }
  ],
  "inference_time_ms": 132.4
}
```

`bbox` is `[x1, y1, x2, y2]` in pixels of the original image.

| Status | Meaning |
|--------|---------|
| 400 | Not a valid JPEG/PNG/WEBP image, or unknown `model_name` |
| 413 | File larger than 10 MB |
| 422 | Invalid query parameter (e.g. `conf` outside 0-1) |
| 503 | Models still loading, or failed to load |

### `GET /health`

Liveness check. Always `200` while the process is up.

```json
{ "status": "ok", "models_ready": true }
```

`status` is `loading`, `ok` or `error`.

### `GET /ready`

Readiness check: `200` once all models are loaded, `503` until then. Used as the post-deploy smoke test.

### `GET /status`

Runtime information: API name and version, environment, start time, loaded models, readiness and (if loading failed) an error message.

---

## Configuration

All settings have defaults and can be overridden with `DURDEN_`-prefixed environment variables or a `.env` file (see [`.env.example`](.env.example)).

| Variable | Default | Description |
|----------|---------|-------------|
| `DURDEN_MODELS` | `["yolov8n.pt","yolov8s.pt","yolov8m.pt"]` | JSON list of YOLO weights; the first is the default |
| `DURDEN_ENV` | `production` | Environment label shown in the UI |
| `DURDEN_NAME` | `Durden Object Detection API` | Service name |
| `DURDEN_VERSION` | `0.1.0` | Reported version |
| `DURDEN_PRELOAD_MODELS` | `false` | `false`: load models in the background and show a loading state; `true`: finish loading before accepting traffic (used on Cloud Run) |
| `DURDEN_MAX_UPLOAD_BYTES` | `10485760` | Maximum upload size |
| `DURDEN_MAX_IMAGE_PIXELS` | `50000000` | Maximum decoded image size (width x height) |

---

## Local Development

Requirements: Python 3.11+, [Poetry](https://python-poetry.org/), Docker (optional).

```bash
poetry install
cp .env.example .env        # optional
poetry run uvicorn durden.main:app --reload
```

Open <http://localhost:8000>. On first run the YOLO weights are downloaded automatically, so the UI shows "Loading models" for a moment.

## Docker

```bash
docker build -t durden .
docker run -p 8000:8000 durden
```

The weights listed in the `MODELS` build argument are downloaded at build time, so containers start without any network access to the model hub. If you change `DURDEN_MODELS`, build with a matching list:

```bash
docker build --build-arg MODELS="yolov8n.pt" -t durden .
```

## Testing

```bash
poetry run pytest --cov            # tests + coverage
poetry run ruff check .            # lint
poetry run ruff format --check .   # formatting
poetry run deptry .                # unused / missing dependencies
```

The suite runs without GPU or model weights: YOLO is mocked, and the real startup path (background loading and the load-failure case) is tested against a stubbed detector.

---

## CI/CD

GitHub Actions on every push, branch and pull request:

- Lint, format check, dependency check
- Tests with coverage

When a version tag (`v*.*.*`) is pushed on a commit that is on `main`, and the tests pass:

- Build the Docker image (with layer caching) and push it to Google Artifact Registry
- Deploy it to Google Cloud Run, authenticated with Workload Identity Federation (no stored keys)
- Smoke test the deployed service against `/ready`
- Publish a GitHub Release with generated notes

Release flow: develop on a branch, merge to `main`, then `git tag v0.1.0 && git push origin v0.1.0`.

## Deployment

The application runs as a container on **Google Cloud Run**:

- Automatic scaling, scale-to-zero when idle, revision-based deployments
- 1 vCPU / 2 GiB and `--max-instances=1` to keep a public demo within the free tier
- `DURDEN_PRELOAD_MODELS=true`: models finish loading before Cloud Run routes any traffic to the instance, so CPU throttling outside requests is not a problem

## Design notes and limitations

- **CPU-only inference.** Latency is hundreds of milliseconds per image on a small CPU instance; the lock around inference serialises requests per instance, which is the honest model for CPU-bound work. Scale out with more instances rather than higher concurrency.
- **Cold starts.** With scale-to-zero, the first request after idle waits (a few seconds to tens of seconds) for the container to start and load the models; Cloud Run holds the request until the instance is ready. Locally, models load in the background instead, and the UI shows a loading state while `/predict` answers `503`.
- **No authentication or rate limiting.** Suitable for a demo; put it behind an API gateway or add auth before exposing it for real traffic.

## Tech Stack

- Python 3.11
- FastAPI, Pydantic
- Ultralytics YOLO, PyTorch (CPU)
- Poetry
- Docker
- GitHub Actions
- Google Artifact Registry, Google Cloud Run
- pytest, ruff, deptry

## License

MIT, see [LICENSE](LICENSE).
