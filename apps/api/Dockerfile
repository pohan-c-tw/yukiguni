FROM python:3.12-slim

# PYTHONDONTWRITEBYTECODE: 不要產生 .pyc bytecode 檔案
# PYTHONUNBUFFERED: 輸出 log 時不要緩衝
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# rm -rf /var/lib/apt/lists/*: 把安裝後的快取清掉
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY .python-version pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

EXPOSE 8000

CMD ["sh", "-c", "uv run --no-dev uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
