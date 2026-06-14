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

- Python 3.12, Django 6.0
- **Nginx**: Reverse proxy optimized for SSE and MCP.
- **Supervisor**: Process manager for Django (ASGI/Uvicorn), Celery Worker, and Celery Beat.
- **PostgreSQL 17** + [`pgvector`](https://github.com/pgvector/pgvector) (HNSW indexes for embeddings)
- **Redis**: Celery broker and SSE pub/sub.
- **Docker**: Containerized deployment using Docker Compose.

## Project Layout

```
.
├── nginx/               # Nginx configuration (SSE optimized)
├── supervisor/          # Supervisor configuration for web and celery
├── vintage_hunter/      # Django project (settings, urls, celery, auth views)
│   ├── catalog/         # Instruments, brands, categories, embeddings, semantic search
│   ├── auction/         # Auctions, lots, bidding, SSE views
│   ├── payments/        # Payment providers and purchase flows
│   ├── users/           # Auth, profiles, saved-search finders
│   ├── commons/         # Base model, SSE helpers, Redis, Azure storages
│   ├── templates/       # Shared templates
│   ├── locale/          # en / uk translations
│   ├── ai-models/       # Local embedding model weights (gitignored)
│   └── manage.py
├── Dockerfile           # Application container image
├── docker-compose.yaml  # Full stack orchestration
└── README.md
```

## Getting Started (Docker - Recommended)

The easiest way to run the entire stack (Database, Redis, Web, Celery, and Nginx) is using Docker Compose.

### 1. Build and start the containers

```bash
docker compose up --build
```

This will:
1. Start **PostgreSQL** (with pgvector) and **Redis**.
2. Build the **Web** image, which runs **Supervisor** to manage the Django ASGI server, Celery Worker, and Celery Beat.
3. Start **Nginx** as a reverse proxy on port `80`.

The application will be accessible at `http://localhost`.

## Automation (Ansible)

The `ansible/` directory contains playbooks to provision a clean Ubuntu VM and deploy the application.

### 1. Prerequisites
- Ansible installed on your local machine.
- A target VM with SSH access.
- Local environment variables set for secrets (or loaded from your local `.env`).

### 2. Configure Inventory & Secrets
Update `ansible/inventory/production.ini` with your server's IP and SSH user:
```ini
[webservers]
my_server ansible_host=1.2.3.4 ansible_user=ubuntu
```

The playbook pulls secrets from your **local shell**. You can export them or load them from your local `.env`:
```bash
# Load local .env into shell
export $(grep -v '^#' vintage_hunter/.env | xargs)
```

**Required Environment Variables:**
- `SECRET_KEY`: Django secret key.
- `APP_DOMAIN`: Your site domain (e.g., `vintage.example.com`).
- `AZURE_CLIENT_ID`: (Optional) Azure AD client ID.
- `AZURE_CLIENT_SECRET`: (Optional) Azure AD client secret.
- `AZURE_STORAGE_NAME`: (Optional) Azure Storage account name.

### 3. Run the Playbook
```bash
cd ansible
ansible-playbook -i inventory/production.ini site.yml
```

This will:
- Harden the OS (UFW, Fail2Ban).
- Install Docker and Docker Compose.
- Clone the repository and template the `.env` file using your local environment variables.
- Start infrastructure (DB/Redis) and run **database migrations**.
- **Download AI models** from Hugging Face directly to the remote host.
- Start the full application stack (`--profile all`).

### 4. Create a superuser
After the first successful deployment, run:
```bash
docker exec -it vintage-web python manage.py createsuperuser
```

## Local Development (Manual)

If you prefer to run the application components manually:

### 1. Start Database and Redis only

```bash
docker compose up -d db redis
```

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
REDIS_URL='redis://127.0.0.1:6379/0'
CELERY_BROKER_URL='redis://127.0.0.1:6379/0'

# Azure auth (for Azure AD sign-in)
AZURE_CLIENT_ID=...
AZURE_TENANT_ID=...
AZURE_AD_AUTHORITY=https://login.microsoftonline.com/<tenant>/
AZURE_CLIENT_SECRET=...

# Azure Storage (static + media)
AZURE_STORAGE_NAME=...

# Local embedding model paths
EMBEDDING_MODEL_PATH='./ai-models/all-mpnet-base-v2'
EMBEDDING_IMAGE_MODEL_PATH='./ai-models/clip-vit-base-patch32'
```

### 4. Run the components

```bash
# In terminal 1: Django server
cd vintage_hunter && python manage.py runserver

# In terminal 2: Celery Worker
cd vintage_hunter && celery -A vintage_hunter worker -l info

# In terminal 3: Celery Beat
cd vintage_hunter && celery -A vintage_hunter beat -l info
```

## MCP Server

`vintage_hunter/mcp_tools.py` exposes a FastMCP server named `vintage-hunter` with tools to list categories, search instruments, and fetch detailed instrument information.

## Internationalization

The project ships English and Ukrainian translations under `vintage_hunter/locale/`. When changing user-facing strings:

```bash
python manage.py makemessages -l uk
python manage.py compilemessages
```

## Development Notes

Agent and contributor guidelines live in [`AGENTS.md`](AGENTS.md).
