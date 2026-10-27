# Dockerfile — Iris Prediction Service
# Base image: python:3.10-slim for a small, production-ready image.
# Best practices:
#   - Non-root user for security
#   - .dockerignore keeps the build context small
#   - Two-stage dependency install (cache-friendly)
#   - Gunicorn as WSGI server (not Flask dev server)

FROM python:3.10-slim

# ── Metadata ──────────────────────────────────────────────────────────────────
LABEL maintainer="Raviraj Amol Patil"
LABEL description="Iris Species Prediction Service — MLOps ISE-2 Demo"
LABEL version="1.0"

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Create non-root user ──────────────────────────────────────────────────────
RUN groupadd --gid 1001 appgroup \
 && useradd  --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies FIRST (layer-caching optimisation) ────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application code ─────────────────────────────────────────────────────
COPY train.py .
COPY app/ ./app/

# ── Train model at build time (bakes model.pkl into the image) ────────────────
RUN python train.py

# ── Switch to non-root user ───────────────────────────────────────────────────
RUN chown -R appuser:appgroup /app
USER appuser

# ── Expose port ───────────────────────────────────────────────────────────────
EXPOSE 5000

# ── Health check (Docker Engine built-in) ─────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# ── Start with Gunicorn ───────────────────────────────────────────────────────
# - 2 workers (CPU-bound ML is fine with 2 on small machines)
# - bind to all interfaces on port 5000
# - The WSGI callable is app.app:app  (package.module:flask_instance)
CMD ["gunicorn", \
     "--workers", "2", \
     "--bind", "0.0.0.0:5000", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app.app:app"]
