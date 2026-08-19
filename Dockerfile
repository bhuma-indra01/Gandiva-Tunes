# Production Dockerfile for Gandiva Tunes Discord Music Bot
# Optimized for Railway.app with FFmpeg audio support
# Credits: Syko Reddy

FROM python:3.11-slim

# Prevent Python from writing .pyc files & unbuffer stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (FFmpeg for audio processing, libopus for Discord voice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libopus0 \
    libopus-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code into container
COPY . .

# Launch Gandiva Tunes
CMD ["python", "main.py"]
