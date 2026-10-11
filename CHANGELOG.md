# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-11

First tagged release.

### Added

- Object detection API built with FastAPI and Ultralytics YOLO: `POST /predict` returns labels, confidence scores, bounding boxes and inference time.
- Three selectable models: `yolov8n.pt` (default), `yolov8s.pt` and `yolov8m.pt`, chosen per request with the `model_name` query parameter.
- `conf` query parameter to set the minimum confidence of returned detections.
- `GET /health` (liveness), `GET /ready` (readiness, `503` until models are loaded) and `GET /status` (version, environment, start time, models, readiness, load error).
- Web UI (plain HTML/CSS/JS, no build step): drag-and-drop upload, model selector, confidence slider, boxes drawn on the image, detections table with per-object highlight, live system status and API docs pages.
- Background model loading at startup, with failures reported through `/health`, `/ready`, `/status` and the UI instead of leaving the app loading forever.
- `DURDEN_PRELOAD_MODELS` setting to finish loading models before the server accepts traffic (used on Cloud Run).
- Configuration through `DURDEN_`-prefixed environment variables or `.env`, with defaults for every setting and a `.env.example`.
- Test suite with coverage covering the API, detector service, image utilities, static pages and the real startup path, including load failures.
- Dockerfile with model weights baked into the image, running as a non-root user, with a `HEALTHCHECK` and `.dockerignore`.
- GitHub Actions pipeline: lint, format check, dependency check (`deptry`) and tests on every branch, pull request and tag.
- Tag-triggered release job (`v*.*.*` on `main`): build and push the image to Google Artifact Registry, deploy to Google Cloud Run through Workload Identity Federation, smoke test `/ready`, and publish a GitHub Release.
- MIT license, `.gitignore` and this changelog.

### Changed

- Inference runs in a worker thread and is serialised with a lock, so health and status endpoints stay responsive and the YOLO models are never called concurrently.
- The confidence slider now filters results client-side, and the table and the canvas show the same set of detections.
- The status panel polls less often once models are ready and pauses in background tabs.
- Navigation stays available on small screens (the sidebar becomes a top bar).
- The About and API docs pages and the README now match the real API.
- `ruff` moved to the development dependencies; `pytest-cov` added.

### Fixed

- The model selector had no effect: the frontend sent `model` while the API reads `model_name`.
- The selected model was reset to the first one on every status refresh.
- The Detect button was enabled with no file selected and re-enabled while a request was running.
- Invalid or non-image uploads caused a `500` error; they now return `400` with a clear message.
- The loading status had no styling.

### Security

- Uploads are limited to 10 MB and to JPEG, PNG and WEBP (checked by content, not file name), with a maximum decoded pixel count as protection against decompression bombs; oversized requests are rejected with `413`.
- Detection results and error messages are rendered with `textContent` instead of `innerHTML`.
- Internal exception details from failed model loading are logged on the server and not exposed in API responses.
- The container runs as a non-root user, and deployment uses short-lived federated credentials instead of stored keys.

[0.1.0]: https://github.com/OWNER/durden/releases/tag/v0.1.0