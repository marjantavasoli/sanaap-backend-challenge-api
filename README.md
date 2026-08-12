# Sanaap Document Management API

A secure document management service built with Django REST Framework.
Documents are stored in MinIO and uploaded directly by clients, access is
controlled with JWT + role-based permissions, uploads are finalized
asynchronously, and clients are notified over WebSocket in real time. The
full stack runs under Docker Compose behind Nginx.

## Features

- JWT authentication (access / refresh)
- Role-based access control: **admin**, **editor**, **viewer**
- Direct-to-MinIO uploads via presigned URLs (files never pass through Django)
- Secure downloads with short-lived **presigned URLs**
- Filtering, ordering, and pagination on the documents API
- Immutable **audit logging** of document access and changes
- **Background processing** of uploads (Celery) triggered by MinIO events
- **Real-time notifications** over WebSocket (Django Channels)
- Interactive API docs (Swagger UI) via OpenAPI 3
- Fully dockerized behind Nginx: Django (ASGI), PostgreSQL, Redis, MinIO

## Tech stack

- Python 3.12 / Django 5 / Django REST Framework
- SimpleJWT · django-filter · drf-spectacular
- django-storages + boto3 (MinIO / S3)
- Celery (Redis broker) · Django Channels + channels-redis
- Gunicorn + Uvicorn workers (ASGI) · Nginx
- PostgreSQL · Redis · MinIO
- Docker & Docker Compose

## Running with Docker (recommended)

### Prerequisites

- Docker and Docker Compose

### Steps

```bash
# 1. Create your env file and set the secrets
cp .env.example .env
#    -> set a strong SECRET_KEY and MINIO_WEBHOOK_KEY

# 2. Build and start the stack
docker compose up --build
```

On startup, one-off services run and exit: `migrate` applies database
migrations, and `minio-init` provisions the MinIO bucket and registers the
upload event notification. The long-running services (`web`, `worker`,
`nginx`, `db`, `redis`, `minio`) start once their dependencies are ready.

Once up (everything is served through Nginx on port 80):

- API root: http://localhost/api/
- Swagger UI: http://localhost/api/docs/
- OpenAPI schema: http://localhost/api/schema/
- Health check: http://localhost/api/health/
- Django admin: http://localhost/admin/
- MinIO console: http://localhost:9001

### Create the first admin user

```bash
docker compose exec web python manage.py createsuperuser
```

Superusers are assigned the `admin` role automatically.

### Data persistence

PostgreSQL and MinIO persist to named Docker volumes (`postgres_data`,
`minio_data`), which survive `docker compose down` and rebuilds. To wipe
them: `docker compose down -v`.

### Services

| Service       | Image           | Port(s)     | Purpose                             |
|---------------|-----------------|-------------|-------------------------------------|
| nginx         | nginx:alpine    | 80          | Reverse proxy + static files        |
| web           | (built locally) | (internal)  | Django API (Gunicorn/Uvicorn, ASGI) |
| worker        | (built locally) | —           | Celery worker (upload processing)   |
| migrate       | (built locally) | —           | Runs migrations, then exits         |
| minio-init    | minio/mc        | —           | Creates the bucket + registers the upload event, then exits |
| db            | postgres:16     | 5432        | Database                            |
| redis         | redis:7         | 6379        | Cache, Celery broker, channel layer |
| minio         | minio/minio     | 9000, 9001  | Object storage                      |

### Serving architecture

```
client → Nginx (:80) → Gunicorn/Uvicorn (web:8000, ASGI) → Django
```

- **Gunicorn with Uvicorn workers** runs Django over ASGI (`config.asgi`),
  serving both HTTP and WebSocket traffic from one server.
- **Nginx** is the only publicly exposed service. It reverse-proxies to the
  app, serves `/static/` directly from a shared volume, and has a dedicated
  `/ws/` block for WebSocket upgrades.
- Static files are gathered at image build (`collectstatic`) into a volume
  shared with Nginx.


## Running locally without Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # leave DATABASE_URL unset -> SQLite fallback
python manage.py migrate
python manage.py runserver
```

### Roles

Every user has one role, managed by an admin in the Django admin:

| Role     | Documents access                     |
|----------|--------------------------------------|
| `admin`  | Full access + user/role management   |
| `editor` | Create and update (no delete)        |
| `viewer` | Read only                            |

## Documents API

All endpoints require a valid JWT (`Authorization: Bearer <access>`).

| Method    | Endpoint               | Min. role | Action                    |
|-----------|------------------------|-----------|---------------------------|
| GET       | `/api/documents/`      | viewer    | List documents            |
| GET       | `/api/documents/{id}/` | viewer    | Retrieve a document       |
| POST      | `/api/documents/`      | editor    | Create a document (upload) |
| PUT/PATCH | `/api/documents/{id}/` | editor    | Update a document         |
| DELETE    | `/api/documents/{id}/` | admin     | Delete a document         |


### Uploading a document (direct-to-MinIO)

Uploads go straight to MinIO; the file never passes through Django.

```text
1. POST /api/documents/  { "title": "report.pdf" }
   -> 201 { "id": 12, "status": "pending", "upload_url": "http://minio:9000/..." }

2. PUT the file bytes to the returned upload_url (client -> MinIO).

3. MinIO emits an ObjectCreated event to an authenticated webhook, which
   enqueues a Celery task. The task reads the object's metadata and flips
   the document to "ready".
```

Example:

```bash
# 1. Create the pending document
curl -X POST http://localhost/api/documents/ \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "report.pdf"}'
# -> { "id": 12, "status": "pending", "upload_url": "http://minio:9000/..." }

# 2. Upload the bytes straight to MinIO
curl -X PUT --upload-file /path/to/report.pdf "<upload_url>"
```

### Filtering, ordering & pagination

```bash
# Filter by title (case-insensitive, partial match)
GET /api/documents/?title=report

# Filter by creation date range
GET /api/documents/?created_after=2025-01-01&created_before=2025-12-31

# Order by a field (prefix with "-" for descending)
GET /api/documents/?ordering=title

# Paginate (10 per page)
GET /api/documents/?page=2
```

## Background processing

A MinIO **bucket notification** calls an authenticated webhook
(`/api/documents/hooks/minio/`, secured by a shared key) when an object is
created. The webhook enqueues a **Celery** task (broker: Redis) that reads
the stored object's metadata and marks the document `ready`.


## Real-time notifications (WebSocket)

The API pushes document lifecycle events over a WebSocket, backed by Django
Channels with a Redis channel layer, so clients can react live instead of
polling.

**Endpoint:** `ws://localhost/ws/documents/?token=<access-token>`

Authentication uses the same JWT as the REST API, passed as a `token` query
parameter (browsers can't set headers on WebSocket connections). Connections
without a valid token are rejected.

Events (broadcast to all connected users, since documents are a shared
collection):

| Event     | When                                            |
|-----------|-------------------------------------------------|
| `created` | a document is created (pending)                 |
| `updated` | a document is updated                           |
| `ready`   | background processing finishes; file available  |
| `deleted` | a document is deleted                           |

Message shape:

```json
{
  "event": "ready",
  "document": { "id": 12, "title": "report.pdf", "status": "ready" }
}
```

The `ready` event is emitted by the Celery worker when a direct upload
finishes processing — a client that created a pending document can wait on
the socket instead of polling.

## Audit logging

Every document action — create, update, delete, list, and retrieve — is
recorded to an immutable audit log capturing the actor, the action, and the
document (id + title). All writes go through a single audit **service**
(`documents/services.py`) and are best-effort: if a log write fails, the
original request still succeeds.

Admins can query the trail:

```bash
GET /api/audit-logs/                     # all entries (admin only)
GET /api/audit-logs/?actor=<user-id>
GET /api/audit-logs/?action=delete
GET /api/audit-logs/?document_id=<id>
```

Delete entries deliberately retain the document's id and title, so the
history remains meaningful after a document is removed. The log is also
viewable (read-only) in the Django admin.

## Running the tests

```bash
pytest
```

The suite runs fully offline — no MinIO, Redis, or Celery worker required
(in-memory fallbacks are used for the cache, channel layer, and task
execution).

## Project structure

```
.
├── config/          # Settings, URLs, ASGI (HTTP + WebSocket), Celery app
├── accounts/        # Custom user model, roles, JWT endpoints
├── common/          # Shared permissions, health check, WebSocket JWT auth
├── documents/       # Document model, storage, API, tasks, webhook,
│                    #   audit + notification services, consumer, routing
├── tests/           # Test suite, mirrors the app layout
├── nginx/           # Nginx reverse-proxy config
├── docker-compose.yml
├── Dockerfile
└── manage.py
```

## Environment variables

See `.env.example` for the full list. Key ones:

| Variable             | Purpose                                             |
|----------------------|-----------------------------------------------------|
| `SECRET_KEY`         | Django secret key                                   |
| `DEBUG`              | Debug mode (set `False` in production)              |
| `ALLOWED_HOSTS`      | Comma-separated allowed hosts                        |
| `POSTGRES_*`         | Database name / user / password                      |
| `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` | MinIO credentials              |
| `MINIO_BUCKET`       | Bucket name for documents                            |
| `MINIO_WEBHOOK_KEY`  | Shared secret MinIO sends with upload webhooks       |
| `DOCUMENT_URL_EXPIRY`| Presigned URL lifetime in seconds (default 300)      |
| `GUNICORN_WORKERS`   | Number of Gunicorn workers (default 3)               |