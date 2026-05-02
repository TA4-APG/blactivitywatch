"""
/api/0/buckets – bucket CRUD compatible with the ActivityWatch REST API.
"""
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Bucket

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────

class BucketCreate(BaseModel):
    client: str
    type: str
    hostname: str
    name: Optional[str] = None


class BucketOut(BaseModel):
    id: str
    name: Optional[str]
    type: str
    client: str
    hostname: str
    created: datetime

    model_config = {"from_attributes": True}


# ── Helpers ───────────────────────────────────────────────────────

def _bucket_or_404(bucket_id: str, db: Session) -> Bucket:
    bucket = db.get(Bucket, bucket_id)
    if bucket is None:
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_id}' not found")
    return bucket


# ── Routes ────────────────────────────────────────────────────────

@router.get("/api/0/buckets")
def list_buckets(db: Session = Depends(get_db)):
    buckets = db.query(Bucket).all()
    return {b.id: BucketOut.model_validate(b).model_dump() for b in buckets}


@router.get("/api/0/buckets/{bucket_id}", response_model=BucketOut)
def get_bucket(bucket_id: str, db: Session = Depends(get_db)):
    return _bucket_or_404(bucket_id, db)


@router.post("/api/0/buckets/{bucket_id}", status_code=200)
def create_or_update_bucket(
    bucket_id: str,
    payload: BucketCreate,
    db: Session = Depends(get_db),
):
    bucket = db.get(Bucket, bucket_id)
    if bucket is None:
        bucket = Bucket(
            id=bucket_id,
            name=payload.name,
            type=payload.type,
            client=payload.client,
            hostname=payload.hostname,
            created=datetime.now(timezone.utc),
        )
        db.add(bucket)
        db.commit()
        db.refresh(bucket)
    return BucketOut.model_validate(bucket)


@router.delete("/api/0/buckets/{bucket_id}", status_code=200)
def delete_bucket(bucket_id: str, db: Session = Depends(get_db)):
    bucket = _bucket_or_404(bucket_id, db)
    db.delete(bucket)
    db.commit()
    return {}
