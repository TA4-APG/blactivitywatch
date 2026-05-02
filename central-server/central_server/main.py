"""
Central ActivityWatch server – application entry point.

12-factor compliance:
  - All configuration via environment variables (see config.py).
  - Logs written to stdout.
  - Stateless process; state lives in the attached database service.
  - Port exported via $AW_PORT (default 5600).
"""
import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import ApiKeyMiddleware
from .config import settings
from .database import create_tables
from .routes import buckets_router, events_router, info_router

# ── Logging to stdout (12-factor §11: treat logs as event streams) ──
logging.basicConfig(
    stream=sys.stdout,
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    logger.info(
        "ActivityWatch Central Server %s started – listening on %s:%s",
        settings.VERSION,
        settings.HOST,
        settings.PORT,
    )
    yield


# ── Application ──────────────────────────────────────────────────
app = FastAPI(
    title="ActivityWatch Central Server",
    version=settings.VERSION,
    description=(
        "Centralised ActivityWatch server that aggregates data from multiple "
        "agents/machines. Follows the 12-factor app methodology."
    ),
    lifespan=lifespan,
)

# CORS – allow all origins so that any agent can reach the server.
# Restrict in production via a reverse proxy if needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API-key authentication
app.add_middleware(ApiKeyMiddleware)

# ── Routes ────────────────────────────────────────────────────────
app.include_router(info_router)
app.include_router(buckets_router)
app.include_router(events_router)


@app.get("/")
def root():
    return {"status": "ok", "server": settings.SERVER_NAME, "version": settings.VERSION}


# ── CLI entry-point ───────────────────────────────────────────────
def main():
    uvicorn.run(
        "central_server.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
