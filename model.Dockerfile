# --- Build Stage ---
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Final Production Runtime Stage ---
FROM python:3.11-slim AS runner

WORKDIR /app

# 1. Install curl so the container's internal healthcheck works
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local

# 2. Copy the actual inference app code into the root of /app
COPY inference_app.py /app/

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/app/model/spam_classifier.pkl
ENV VECTORIZER_PATH=/app/model/vectorizer.pkl
ENV MODEL_VERSION=v1.0.0

EXPOSE 8000

# Container-level health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 3. Corrected module path since inference_app.py is in the app root
CMD ["uvicorn", "inference_app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]