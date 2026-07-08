FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry==2.3.4

RUN poetry config virtualenvs.create false

RUN pip install --no-cache-dir \
    torch \
    torchvision \
    --index-url https://download.pytorch.org/whl/cpu

RUN poetry install --only main --no-interaction --no-ansi --no-root

COPY ./src .

CMD ["uvicorn", "durden.main:app", "--host", "0.0.0.0", "--port", "8000"]