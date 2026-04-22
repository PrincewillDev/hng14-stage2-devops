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
# Healthcheck verifies the worker process (PID 1) is still running.
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import sys; cmdline=open('/proc/1/cmdline','rb').read(); sys.exit(0 if b'worker.py' in cmdline else 1)"

CMD ["python", "worker.py"]
