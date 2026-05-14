# Vintage Hunter

A Django application for cataloging and auctioning vintage musical instruments. Vintage Hunter combines a traditional catalog with live auctions, semantic and visual similarity search backed by `pgvector`, and an MCP server that exposes the catalog to AI agents.

## Features

- **Catalog** of vintage instruments with brands, categories, conditions, specifications, and image galleries.
- **Semantic text search** over instrument descriptions using sentence-transformers embeddings (`all-mpnet-base-v2`).
- **Visual similarity search** using CLIP image embeddings (`clip-vit-base-patch32`).
- **Auctions**: scheduled auctions with registration, bidding intervals, reminders, lot timeouts, and live updates over Server-Sent Events.
- **Payments**: pluggable payment providers (a mock provider ships by default) with purchase reservations.
- **Users**: registration, sign-in, saved-search "finder" jobs that run periodically via Celery Beat.
- **Internationalization**: English and Ukrainian translations.
- **MCP server** (`vintage_hunter/mcp_tools.py`) exposing `list_categories`, `list_instruments`, and `get_instrument_details` to AI agents via FastMCP.

## Stack

- Python 3.x, Django 6.0
- PostgreSQL 17 + [`pgvector`](https://github.com/pgvector/pgvector) (HNSW indexes for embeddings)
- Redis (Celery broker and SSE pub/sub)
- Celery + Celery Beat
- Bootstrap 5.3.0, Bootstrap Icons, vanilla CSS/JS, Django templates
- Azure Blob Storage for static and media files (via `django-storages`)
- `sentence-transformers`, `transformers` (CLIP) for embeddings
- `fastmcp`, `sse-starlette` for MCP and SSE endpoints

## Project Layout

```
vintage_hunter/
├── vintage_hunter/      # Django project (settings, urls, celery, auth views)
├── catalog/             # Instruments, brands, categories, embeddings, semantic search
├── auction/             # Auctions, lots, bidding, SSE views
├── payments/            # Payment providers and purchase flows
├── users/               # Auth, profiles, saved-search finders
├── commons/             # Base model, SSE helpers, Redis, Azure storages
├── templates/           # Shared templates
├── locale/              # en / uk translations
├── ai-models/           # Local embedding model weights (gitignored)
├── mcp_tools.py         # FastMCP server exposing catalog tools
└── manage.py
```

## Getting Started

### 1. Start PostgreSQL and Redis

```bash
docker compose up -d
```

This starts `pgvector/pgvector:pg17` on `localhost:5432` and `redis:latest` on `localhost:6379`. Data is persisted to `./pgdata` and `./redis`.

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create `vintage_hunter/.env` with at least:

```env
SECRET_KEY='change-me'
DB_URL='postgres://myuser:mypassword@127.0.0.1:5432/vintagedb'

# Azure auth (for Azure AD sign-in)
AZURE_CLIENT_ID=...
AZURE_TENANT_ID=...
AZURE_AD_AUTHORITY=https://login.microsoftonline.com/<tenant>/
AZURE_CLIENT_SECRET=...

# Azure Storage (static + media)
AZURE_STORAGE_NAME=...

# Celery queues
CELERY_BROKER_QUEUE=django-celery
CELEREY_PERIODIC_BROKER_QUEUE=django-periodic-celery

# Local embedding model paths
EMBEDDING_MODEL_PATH='./ai-models/all-mpnet-base-v2'
EMBEDDING_IMAGE_MODEL_PATH='./ai-models/clip-vit-base-patch32'
```

Download the embedding models into `vintage_hunter/ai-models/` (the folder is gitignored).

### 4. Run migrations and start the dev server

```bash
cd vintage_hunter
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 5. Start Celery workers and Beat

In separate terminals, from `vintage_hunter/`:

```bash
celery -A vintage_hunter worker -l info -Q django-celery
celery -A vintage_hunter worker -l info -Q django-periodic-celery
celery -A vintage_hunter beat -l info
```

Beat schedules auction timeouts, scheduled-auction starts, reminders, and saved-search finder runs (see `vintage_hunter/settings.py`).

## MCP Server

`vintage_hunter/mcp_tools.py` exposes a FastMCP server named `vintage-hunter` with tools to list categories, search instruments (semantic when a `query` is provided, otherwise category-filtered with pagination), and fetch detailed instrument information including visually similar items.

## Internationalization

The project ships English and Ukrainian translations under `vintage_hunter/locale/`. When changing user-facing strings:

```bash
python manage.py makemessages -l uk
python manage.py compilemessages
```

## Development Notes

Agent and contributor guidelines — Django conventions, model conventions, frontend rules, and AI/search rules — live in [`AGENTS.md`](AGENTS.md).
