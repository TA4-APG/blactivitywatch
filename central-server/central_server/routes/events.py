"""
/api/0/buckets/{bucket_id}/events – event CRUD.
"""
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Bucket, Event

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────

class EventIn(BaseModel):
    timestamp: datetime
    duration: float
    data: dict


class EventOut(BaseModel):
    id: int
    timestamp: datetime
    duration: float
    data: dict

    model_config = {"from_attributes": True}


def _to_out(event: Event) -> EventOut:
    return EventOut(
        id=event.id,
        timestamp=event.timestamp,
        duration=event.duration,
        data=json.loads(event.data),
    )


def _bucket_or_404(bucket_id: str, db: Session) -> Bucket:
    bucket = db.get(Bucket, bucket_id)
    if bucket is None:
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_id}' not found")
    return bucket


# ── Routes ────────────────────────────────────────────────────────

@router.get("/api/0/buckets/{bucket_id}/events", response_model=List[EventOut])
def get_events(
    bucket_id: str,
    limit: Optional[int] = Query(default=100, ge=1, le=10000),
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db),
):
    _bucket_or_404(bucket_id, db)
    q = db.query(Event).filter(Event.bucket_id == bucket_id)
    if start:
        q = q.filter(Event.timestamp >= start)
    if end:
        q = q.filter(Event.timestamp <= end)
    q = q.order_by(Event.timestamp.desc()).limit(limit)
    return [_to_out(e) for e in q.all()]


@router.post("/api/0/buckets/{bucket_id}/events", response_model=List[EventOut])
def create_events(
    bucket_id: str,
    events: List[EventIn],
    db: Session = Depends(get_db),
):
    _bucket_or_404(bucket_id, db)
    created: list[Event] = []
    for ev in events:
        row = Event(
            bucket_id=bucket_id,
            timestamp=ev.timestamp,
            duration=ev.duration,
            data=json.dumps(ev.data),
        )
        db.add(row)
        created.append(row)
    db.commit()
    for row in created:
        db.refresh(row)
    return [_to_out(e) for e in created]


@router.get("/api/0/buckets/{bucket_id}/events/count")
def get_event_count(bucket_id: str, db: Session = Depends(get_db)):
    _bucket_or_404(bucket_id, db)
    count = db.query(Event).filter(Event.bucket_id == bucket_id).count()
    return count


@router.delete("/api/0/buckets/{bucket_id}/events/{event_id}", status_code=200)
def delete_event(bucket_id: str, event_id: int, db: Session = Depends(get_db)):
    _bucket_or_404(bucket_id, db)
    event = db.get(Event, event_id)
    if event is None or event.bucket_id != bucket_id:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
    return {}


@router.get("/api/0/buckets/{bucket_id}/heartbeat")
def heartbeat(
    bucket_id: str,
    pulsetime: float = Query(...),
    db: Session = Depends(get_db),
):
    """
    Minimal heartbeat endpoint – in a full implementation this would merge
    consecutive events with the same data that fall within `pulsetime` seconds.
    For the central server, we acknowledge the call without merging.
    """
    _bucket_or_404(bucket_id, db)
    return {}
