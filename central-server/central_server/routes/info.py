"""
/api/0/info – server metadata.
"""
from fastapi import APIRouter

from ..config import settings

router = APIRouter()


@router.get("/api/0/info")
def info():
    return {
        "hostname": settings.SERVER_NAME,
        "version": settings.VERSION,
        "testing": False,
        "device_id": settings.SERVER_NAME,
    }
