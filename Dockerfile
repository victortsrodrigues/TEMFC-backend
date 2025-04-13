FROM python:3.11-slim-bullseye

WORKDIR /app

# Install system dependencies including build tools and Chrome dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    gcc \
    python3-dev \
    libpq-dev \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libxkbcommon0 \
    xdg-utils && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables for optimal performance
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=src.wsgi:app
ENV FLASK_ENV=production
ENV PORT=5000
ENV GUNICORN_WORKER_TIMEOUT=120
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE ${PORT}

# Command optimized for limited resources
CMD gunicorn --bind 0.0.0.0:${PORT} \
    --workers=1 \
    --threads=4 \
    --timeout=${GUNICORN_WORKER_TIMEOUT} \
    --log-level=info \
    src.wsgi:app