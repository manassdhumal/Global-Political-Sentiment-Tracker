# FastAPI backend image for the Global Political Sentiment Tracker.
# Lean: RoBERTa/torch are excluded (sentiment falls back to VADER).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Install deps first for better layer caching.
COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

# App code only (no frontend, data, tests).
COPY api ./api
COPY src ./src
COPY config ./config
COPY scripts ./scripts

# The API reads GPST_CORS_ORIGINS (your frontend URL) + optional live-data
# credentials from the environment. It runs on synthetic data out of the box.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
