FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for Playwright & ML (separate layer for caching)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Python deps (separate layer — only rebuilds when requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# App code (changes most frequently — last layer)
COPY . .

# Non-root user for security
RUN adduser --disabled-password --no-create-home appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["curl", "-f", "http://localhost:8000/health"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
