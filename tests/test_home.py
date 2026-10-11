from pathlib import Path

import pytest

from durden.main import settings


@pytest.mark.parametrize(
    ("url", "filename"),
    [("/", "index.html"), ("/about", "about.html"), ("/api-docs", "api_docs.html")],
)
def test_pages(client, monkeypatch, tmp_path, url, filename):
    (tmp_path / filename).write_text("<h1>Hello</h1>")

    monkeypatch.setattr(settings, "static_dir", Path(tmp_path))

    response = client.get(url)

    assert response.status_code == 200
    assert "<h1>Hello</h1>" in response.text


def test_real_static_pages_exist(client):
    for url in ("/", "/about", "/api-docs"):
        response = client.get(url)

        assert response.status_code == 200
        assert "DURDEN" in response.text
