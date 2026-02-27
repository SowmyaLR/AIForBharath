# ════════════════════════════════════════════════════════════════
#  VaidyaSaarathi - Server Dockerfile
#  Multi-stage build: Python 3.12 + system audio libs
# ════════════════════════════════════════════════════════════════
FROM python:3.12-slim

# System dependencies for librosa / soundfile / audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python deps first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directory for audio files
RUN mkdir -p /app/storage/audio && chmod 700 /app/storage/audio

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Entrypoint
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
