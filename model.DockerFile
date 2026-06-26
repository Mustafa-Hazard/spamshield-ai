# --- Build Stage ---
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install dependencies into a separate path to isolate dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Final Production Runtime Stage ---
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy only installed libraries from build context
COPY --from=builder /root/.local /root/.local
COPY ./model /app/model

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/app/model/spam_classifier.pkl
ENV VECTORIZER_PATH=/app/model/vectorizer.pkl
ENV MODEL_VERSION=v1.0.0

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "model.inference_app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]