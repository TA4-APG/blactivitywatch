"""
API-key authentication middleware.

When AW_API_KEY is set, every request to /api/* must carry:

    Authorization: <api_key>

Requests without or with a wrong key receive HTTP 401.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.API_KEY:
            # Auth disabled – allow everything
            return await call_next(request)

        # Only protect the /api/* namespace
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        authorization = request.headers.get("Authorization", "")
        if authorization != settings.API_KEY:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "message": "Invalid or missing API key"},
            )
        return await call_next(request)
