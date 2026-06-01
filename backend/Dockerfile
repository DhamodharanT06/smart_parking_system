FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system deps required for OpenCV/FFmpeg and git-lfs
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       git-lfs \
       ffmpeg \
       libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and model
COPY . /app

ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV MODEL_PATH=/app/yolov8n.pt

EXPOSE ${PORT}

# Start the FastAPI app using the PORT provided by Spaces
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
