# Durden

A production-style object detection API built with **FastAPI** and **YOLO**. Durden exposes a REST interface for image analysis, allowing clients to upload images and receive structured object detection results.

The project demonstrates backend engineering practices alongside machine learning inference, including containerization, automated testing, CI/CD, and cloud deployment.

## Features

- REST API for object detection
- Multiple YOLO model support
- Optional model selection per request
- Asynchronous model loading during startup
- Structured detection responses
  - Object labels
  - Confidence scores
  - Bounding boxes
  - Inference time
- Health and status endpoints
- Automated test suite with `pytest`
- Dockerized deployment
- CI/CD with GitHub Actions
- Deployment to Google Cloud Run

---

## Architecture

```text
             +-------------+
             |   Client    |
             +------+------+
                    |
                    v
             +------+------+
             |   FastAPI   |
             +------+------+
                    |
                    v
             +------+------+
             |  Detector   |
             |   Service   |
             +------+------+
                    |
                    v
             +------+------+
             | YOLO Models |
             +-------------+
```

---

## API Endpoints

### `GET /health`

Returns the API health and model loading status.

Example response:

```json
{
  "status": "ok",
  "models_ready": true
}
```

---

### `GET /status`

Returns runtime information including:

- API version
- Environment
- Loaded models
- Startup time
- Model readiness

---

### `POST /predict`

Performs object detection on an uploaded image.

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| file | Image | ✅ | Image to analyze |
| model_name | String | ❌ | Model override |

Example response:

```json
{
  "filename": "image.jpg",
  "model_name": "yolov8n.pt",
  "detections": [
    {
      "label": "person",
      "confidence": 0.91,
      "bbox": [120, 80, 240, 300]
    }
  ],
  "inference_time_ms": 47.3
}
```

---

## Local Development

### Requirements

- Python 3.11+
- Poetry
- Docker (optional)

Install dependencies:

```bash
poetry install
```

Run the application:

```bash
poetry run uvicorn durden.main:app --reload
```

The API will be available at:

```
http://localhost:8000
```

---

## Docker

Build the image:

```bash
docker build -t durden .
```

Run the container:

```bash
docker run -p 8000:8000 durden
```

---

## Testing

Run the test suite:

```bash
poetry run pytest
```

Run linting:

```bash
poetry run ruff check .
```

---

## CI/CD

GitHub Actions automatically:

- Runs linting
- Executes the test suite
- Builds the Docker image
- Publishes the image to GitHub Container Registry (GHCR)
- Deploys the latest revision to Google Cloud Run

---

## Deployment

The application is deployed as a Docker container on **Google Cloud Run**, providing:

- Automatic scaling
- Scale-to-zero when idle
- Managed container execution
- Revision-based deployments

---

## Tech Stack

- Python 3.11
- FastAPI
- Ultralytics YOLO
- PyTorch
- Poetry
- Docker
- GitHub Actions
- GitHub Container Registry
- Google Cloud Run