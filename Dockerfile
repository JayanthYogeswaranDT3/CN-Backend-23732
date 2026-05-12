FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for building some python wheels and for health checks (curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user
RUN useradd -m appuser
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

USER appuser

EXPOSE 8000

# Uvicorn is enough for scaffold; add gunicorn/uvicorn workers later for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"
