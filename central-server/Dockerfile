# syntax=docker/dockerfile:1
# ─────────────────────────────────────────────────────────────────
# Stage 1 – builder: install dependencies into a virtual-env
# ─────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install Poetry (pinned version for reproducibility)
ENV POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml ./
# Generate a lock file if one is not present (CI will always commit it)
RUN poetry lock --no-update 2>/dev/null || true
COPY poetry.lock* ./
RUN poetry install --only main --no-root

COPY central_server ./central_server
RUN poetry install --only main

# ─────────────────────────────────────────────────────────────────
# Stage 2 – runtime: minimal image with only the virtual-env
# ─────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="ActivityWatch Central Server"
LABEL org.opencontainers.image.description="Centralised AW server – 12-factor, Docker-ready"
LABEL org.opencontainers.image.source="https://github.com/TA4-APG/blactivitywatch"
LABEL org.opencontainers.image.licenses="MPL-2.0"

# Create a non-root user (security best practice)
RUN addgroup --system aw && adduser --system --ingroup aw aw

WORKDIR /app

# Copy only the virtual-env produced in the builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/central_server /app/central_server

# Ensure the virtual-env's Python is used
ENV PATH="/app/.venv/bin:$PATH"

# ── 12-factor defaults (overridden at runtime via env vars) ───────
ENV AW_HOST=0.0.0.0 \
    AW_PORT=5600 \
    DATABASE_URL=sqlite:///./aw-central.db \
    AW_API_KEY="" \
    AW_SERVER_NAME=aw-central-server \
    LOG_LEVEL=INFO

# Data directory – mount a volume here for persistent SQLite storage
RUN mkdir -p /data && chown aw:aw /data
WORKDIR /data

USER aw

EXPOSE 5600

# Graceful shutdown: uvicorn handles SIGTERM
CMD ["python", "-m", "central_server.main"]
