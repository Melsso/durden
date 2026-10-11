from durden.main import app


def test_health_loading(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "loading", "models_ready": False}


def test_health_ready(client):
    app.state.model_ready = True

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "models_ready": True}


def test_health_error(client):
    app.state.model_error = "boom"

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "error", "models_ready": False}


def test_ready_returns_503_until_models_loaded(client):
    assert client.get("/ready").status_code == 503

    app.state.model_ready = True

    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["models_ready"] is True
