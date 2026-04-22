# ── Stage 1: build deps ───────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir pip==25.1.1 \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

COPY --from=builder /install /usr/local

# copy application source (no .env, no secrets)
COPY worker.py .

USER app

# Worker is a long-running queue consumer with no HTTP server.
# Healthcheck verifies Redis is reachable and the script is importable.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import redis, os; r = redis.Redis(host=os.getenv('REDIS_HOST','redis'), port=6379, password=os.getenv('REDIS_PASSWORD')); r.ping()"

CMD ["python", "worker.py"]
