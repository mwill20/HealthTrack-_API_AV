# syntax=docker/dockerfile:1
# ──────────────────────────────────────────────────────────────────────────
# Multi-stage build for HealthTrack API.
#
#  Stage 1 (builder)  installs dependencies into an isolated virtualenv.
#  Stage 2 (runtime)  copies only that venv + app code into a slim image and
#                     runs as a non-root user.
#
# Why multi-stage: build-time tooling and caches never reach the final image,
# so the shipped image is smaller and has a smaller attack surface.
# ──────────────────────────────────────────────────────────────────────────

# ── Stage 1: builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# PYTHONDONTWRITEBYTECODE: don't emit .pyc files. PYTHONUNBUFFERED: stream logs
# straight to stdout (so container logs appear immediately, not after a flush).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Build deps into a self-contained venv we can copy wholesale into the runtime
# stage. Only runtime requirements are installed here — never the dev/test set.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy the prebuilt virtualenv from the builder — no pip, no build cache here.
COPY --from=builder /opt/venv /opt/venv

# Copy only what the service needs to run. Tests, docs, CI config, and the dev
# requirements file are excluded via .dockerignore.
COPY app ./app
COPY wsgi.py ./

# Create an unprivileged account and run as it. A container process running as
# root that escapes isolation runs as root on the host — least privilege closes
# that path. High UID avoids collision with host system accounts.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Documents the port the app listens on. Publish it at run time with -p.
EXPOSE 5000

# Container-internal liveness probe. Uses Python's stdlib (no curl install
# needed) to hit /health; a non-200 or exception marks the container unhealthy.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:5000/health', timeout=3).status == 200 else 1)"

# Production WSGI server. Secrets/config arrive as runtime environment
# variables (see compose env_file) — never baked into the image.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "wsgi:app"]
