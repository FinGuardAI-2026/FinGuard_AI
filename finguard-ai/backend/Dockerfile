# ── Production Dockerfile for FinGuard AI Backend ─────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY backend/requirements.txt ./backend_reqs.txt
RUN pip install --no-cache-dir -r backend_reqs.txt

# Copy source code for both backend and ml_pipeline
COPY backend ./backend
COPY ml_pipeline ./ml_pipeline

# Set Python environment path
ENV PYTHONPATH=/app/backend:/app

WORKDIR /app/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
