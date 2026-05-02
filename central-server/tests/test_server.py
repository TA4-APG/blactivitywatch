"""
Basic smoke tests for the central server.
Uses FastAPI's TestClient (synchronous) backed by an in-memory SQLite database.
"""
import os

# Must be set before importing application modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AW_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from central_server.database import get_db
from central_server.main import app
from central_server.models import Base

# ── Shared in-memory engine for tests ────────────────────────────
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def fresh_db():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


# ── /api/0/info ───────────────────────────────────────────────────

def test_info(client):
    r = client.get("/api/0/info")
    assert r.status_code == 200
    data = r.json()
    assert "version" in data
    assert "hostname" in data


# ── Buckets ───────────────────────────────────────────────────────

BUCKET_ID = "test-bucket_testhost"
BUCKET_PAYLOAD = {"client": "test-client", "type": "test", "hostname": "testhost"}


def test_create_and_get_bucket(client):
    r = client.post(f"/api/0/buckets/{BUCKET_ID}", json=BUCKET_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == BUCKET_ID
    assert data["hostname"] == "testhost"

    r = client.get(f"/api/0/buckets/{BUCKET_ID}")
    assert r.status_code == 200
    assert r.json()["id"] == BUCKET_ID


def test_list_buckets(client):
    client.post(f"/api/0/buckets/{BUCKET_ID}", json=BUCKET_PAYLOAD)
    r = client.get("/api/0/buckets")
    assert r.status_code == 200
    assert BUCKET_ID in r.json()


def test_delete_bucket(client):
    client.post(f"/api/0/buckets/{BUCKET_ID}", json=BUCKET_PAYLOAD)
    r = client.delete(f"/api/0/buckets/{BUCKET_ID}")
    assert r.status_code == 200
    r = client.get(f"/api/0/buckets/{BUCKET_ID}")
    assert r.status_code == 404


# ── Events ────────────────────────────────────────────────────────

EVENT = {"timestamp": "2024-01-01T00:00:00+00:00", "duration": 1.0, "data": {"app": "test"}}


def test_create_and_get_events(client):
    client.post(f"/api/0/buckets/{BUCKET_ID}", json=BUCKET_PAYLOAD)
    r = client.post(f"/api/0/buckets/{BUCKET_ID}/events", json=[EVENT])
    assert r.status_code == 200
    created = r.json()
    assert len(created) == 1
    assert created[0]["data"]["app"] == "test"

    r = client.get(f"/api/0/buckets/{BUCKET_ID}/events")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_event_count(client):
    client.post(f"/api/0/buckets/{BUCKET_ID}", json=BUCKET_PAYLOAD)
    client.post(f"/api/0/buckets/{BUCKET_ID}/events", json=[EVENT, EVENT])
    r = client.get(f"/api/0/buckets/{BUCKET_ID}/events/count")
    assert r.status_code == 200
    assert r.json() == 2


def test_delete_event(client):
    client.post(f"/api/0/buckets/{BUCKET_ID}", json=BUCKET_PAYLOAD)
    r = client.post(f"/api/0/buckets/{BUCKET_ID}/events", json=[EVENT])
    event_id = r.json()[0]["id"]
    r = client.delete(f"/api/0/buckets/{BUCKET_ID}/events/{event_id}")
    assert r.status_code == 200
    r = client.get(f"/api/0/buckets/{BUCKET_ID}/events")
    assert r.json() == []


# ── Auth ──────────────────────────────────────────────────────────

def test_auth_required():
    from central_server import config
    original_key = config.settings.API_KEY
    config.settings.API_KEY = "secret123"
    try:
        with TestClient(app) as c:
            r = c.get("/api/0/info")
            assert r.status_code == 401

            r = c.get("/api/0/info", headers={"Authorization": "secret123"})
            assert r.status_code == 200
    finally:
        config.settings.API_KEY = original_key

