# ──────────────────────────────────────────────────────────────
# Stage 1: Builder – install dependencies
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY actuarial_engine/ ./actuarial_engine/
RUN pip install --upgrade pip && pip install --no-cache-dir hatchling && pip install --no-cache-dir .

# ──────────────────────────────────────────────────────────────
# Stage 2: Runtime – minimal image
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Non-root user untuk keamanan on-premise
RUN addgroup --system actuarial && adduser --system --ingroup actuarial actuser

# Copy installed packages dari builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY actuarial_engine/ ./actuarial_engine/
COPY data/ ./data/

USER actuser

EXPOSE 8000

# PORT env variable is injected by Render (default 8000)
ENV PORT=8000

# Jalankan dengan uvicorn production-grade
# Workers=2 untuk Render free tier (512MB RAM)
CMD uvicorn actuarial_engine.main:app --host 0.0.0.0 --port $PORT --workers 2
