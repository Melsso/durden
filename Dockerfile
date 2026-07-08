FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry==2.3.4

RUN poetry config virtualenvs.create false

RUN pip install --no-cache-dir \
    torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

RUN poetry install --only main --no-interaction --no-ansi --no-root --no-cache

COPY ./src .

CMD ["uvicorn", "durden.main:app", "--host", "0.0.0.0", "--port", "8000"]