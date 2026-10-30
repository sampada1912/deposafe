FROM python:3.11-slim

WORKDIR /app

# System dependencies for PyMuPDF and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for build layer caching
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application, schemas/config, and synthetic seed datasets
COPY backend /app/backend
COPY config /app/config
COPY data /app/data

# Create runtime directories for data and storage
RUN mkdir -p /app/storage /app/data_runtime

# Create non-root system user and transfer directory ownership
RUN useradd -m -u 1000 deposafe && \
    chown -R deposafe:deposafe /app

USER deposafe

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DATA_DIR=/app/data_runtime

EXPOSE 8000

# Bind to PORT env var provided by Render (default 8000) with 1 worker to conserve RAM (< 450 MB)
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
