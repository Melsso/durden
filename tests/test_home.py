from pathlib import Path

from durden.main import settings


def test_home(client, monkeypatch, tmp_path):
    html = tmp_path / "index.html"
    html.write_text("<h1>Hello</h1>")

    monkeypatch.setattr(settings, "static_dir", Path(tmp_path))

    response = client.get("/")

    assert response.status_code == 200
    assert "<h1>Hello</h1>" in response.text
