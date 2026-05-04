# ActivityWatch Central Server

A centralised ActivityWatch server that collects activity data from multiple agents/machines and stores it in a single database. It is designed following the [12-factor app](https://12factor.net/) methodology and ships as a Docker container.

## Features

- **12-factor compliant** – all configuration via environment variables
- **ActivityWatch REST API** – compatible with `aw-client`; buckets and events work out of the box
- **API-key authentication** – set `AW_API_KEY` to protect every `/api/*` endpoint
- **SQLite (default) or PostgreSQL** – swap with `DATABASE_URL`
- **Docker-ready** – multi-stage, minimal image running as a non-root user
- **GitHub Actions CI** – Docker image built and pushed on every push to `master` / on version tags

## Quick start

### Docker Compose (recommended)

```bash
cp .env.example .env
# Edit .env: set AW_API_KEY to a random secret
docker compose up -d
```

The server is available at <http://localhost:5600>.

### Local development

```bash
pip install poetry
poetry install
poetry run aw-central-server
```

## Configuration

All settings are read from environment variables (12-factor §3):

| Variable | Default | Description |
|---|---|---|
| `AW_HOST` | `0.0.0.0` | Bind address |
| `AW_PORT` | `5600` | TCP port |
| `DATABASE_URL` | `sqlite:///./aw-central.db` | SQLAlchemy database URL |
| `AW_API_KEY` | *(empty)* | API key – leave empty to disable auth |
| `AW_SERVER_NAME` | `aw-central-server` | Reported hostname in `/api/0/info` |
| `LOG_LEVEL` | `INFO` | Python log level |

## Connecting aw-client agents

In each agent's `aw-client.toml` (usually `~/.config/activitywatch/aw-client.toml`):

```toml
[central-server]
url   = "http://<central-server-ip>:5600"
token = "<AW_API_KEY value>"
```

Or programmatically:

```python
from aw_client import ActivityWatchClient
client = ActivityWatchClient.from_central_server()
```

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/0/info` | Server metadata |
| `GET` | `/api/0/buckets` | List all buckets |
| `POST` | `/api/0/buckets/{id}` | Create/update a bucket |
| `GET` | `/api/0/buckets/{id}` | Get a bucket |
| `DELETE` | `/api/0/buckets/{id}` | Delete a bucket |
| `GET` | `/api/0/buckets/{id}/events` | Get events (supports `limit`, `start`, `end`) |
| `POST` | `/api/0/buckets/{id}/events` | Insert events |
| `GET` | `/api/0/buckets/{id}/events/count` | Event count |
| `DELETE` | `/api/0/buckets/{id}/events/{eid}` | Delete an event |

Interactive API docs are available at <http://localhost:5600/docs>.

## Running tests

```bash
cd central-server
poetry install
poetry run pytest tests/ -v
```

## Docker

### Build manually

```bash
docker build -t aw-central-server ./central-server
```

### Run

```bash
docker run -d \
  -p 5600:5600 \
  -e AW_API_KEY=mysecret \
  -v aw_data:/data \
  aw-central-server
```
