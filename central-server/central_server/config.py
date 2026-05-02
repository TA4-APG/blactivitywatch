"""
12-factor configuration: all settings come from environment variables.
"""
import os


class Config:
    # ── Server ────────────────────────────────────────────────────
    HOST: str = os.environ.get("AW_HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("AW_PORT", "5600"))

    # ── Database ──────────────────────────────────────────────────
    # Accepts any SQLAlchemy URL, e.g.:
    #   sqlite:///./aw-central.db  (default, for development)
    #   postgresql://user:pass@db:5432/aw
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL", "sqlite:///./aw-central.db"
    )

    # ── Authentication ────────────────────────────────────────────
    # A single shared API key that every agent must send in the
    # "Authorization" header. Leave empty to disable auth (dev only).
    API_KEY: str = os.environ.get("AW_API_KEY", "")

    # ── Application metadata ──────────────────────────────────────
    SERVER_NAME: str = os.environ.get("AW_SERVER_NAME", "aw-central-server")
    VERSION: str = os.environ.get("AW_VERSION", "0.1.0")

    # ── Log level ─────────────────────────────────────────────────
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()


settings = Config()
