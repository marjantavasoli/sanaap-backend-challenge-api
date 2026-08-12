# Sanaap Document Management API

A secure document management service built with Django REST Framework.
Documents are stored in MinIO, access is controlled with JWT + role-based
permissions, and the full stack runs under Docker Compose.

## Features

- JWT authentication (access / refresh)
- Role-based access control: **admin**, **editor**, **viewer**
- Secure document storage in MinIO with short-lived **presigned URLs**
- Filtering, ordering, and pagination on the documents API
- Interactive API docs (Swagger UI) via OpenAPI 3
- Fully dockerized: Django, PostgreSQL, Redis, MinIO

## Tech stack

- Python 3.12 / Django 5 / Django REST Framework
- SimpleJWT · django-filter · drf-spectacular
- django-storages + boto3 (MinIO / S3)
- PostgreSQL · Redis · MinIO
- Docker & Docker Compose

## Running with Docker (recommended)

### Prerequisites

- Docker and Docker Compose

### Steps

```bash
# 1. Create your env file and set the secrets
cp .env.example .env
#    -> set a strong SECRET_KEY

# 2. Build and start the stack
docker compose up --build
```

On startup a dedicated `migrate` service applies migrations and exits, a
`createbuckets` service provisions the MinIO bucket, and the `web` service
starts only after both finish.

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

| Service      | Image           | Port(s)     | Purpose                     |
|--------------|-----------------|-------------|-----------------------------|
| web          | (built locally) | (internal)  | Django API (Gunicorn/Uvicorn, ASGI) |
| nginx        | nginx:alpine    | 80          | Reverse proxy + static files        |
| migrate      | (built locally) | —           | Runs migrations, then exits |
| createbuckets| minio/mc        | —           | Creates the bucket, exits   |
| db           | postgres:16     | 5432        | Database                    |
| redis        | redis:7         | 6379        | Cache                       |
| minio        | minio/minio     | 9000, 9001  | Object storage              |

> The `web` service runs Django's development server. A production app
> server (Gunicorn) and reverse proxy (Nginx) are planned as a later branch.

### Serving architecture

```
client → Nginx (:80) → Gunicorn/Uvicorn (web:8000, ASGI) → Django
```

- **Gunicorn with Uvicorn workers** runs Django over ASGI (`config.asgi`),
  so the same server handles HTTP today and WebSockets (Channels branch)
  without changes.
- **Nginx** is the only publicly exposed service. It reverse-proxies to the
  app, serves `/static/` directly from a shared volume, and is already
  configured to proxy WebSocket upgrades.
- Static files are gathered at image build (`collectstatic`) into a volume
  shared with Nginx.

> HTTP only — TLS is out of scope for this challenge but would terminate at
> the Nginx layer.

## Running locally without Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # leave DATABASE_URL unset -> SQLite fallback
python manage.py migrate
python manage.py runserver
```

> Without MinIO configured, storage calls won't reach a backend — use the
> Docker stack for full document upload/download.

## Authentication

The API uses JWT (via `djangorestframework-simplejwt`).

```bash
# Obtain a token pair
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "<user>", "password": "<pass>"}'

# Use the access token on protected endpoints
curl http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer <access-token>"

# Refresh an expired access token
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh-token>"}'
```

### Roles

Every user has one role, managed by an admin in the Django admin:

| Role     | Documents access                     |
|----------|--------------------------------------|
| `admin`  | Full access + user/role management   |
| `editor` | Upload and update (no delete)        |
| `viewer` | Read only                            |

## Documents API

All endpoints require a valid JWT (`Authorization: Bearer <access>`).

| Method    | Endpoint               | Min. role | Action              |
|-----------|------------------------|-----------|---------------------|
| GET       | `/api/documents/`      | viewer    | List documents      |
| GET       | `/api/documents/{id}/` | viewer    | Retrieve a document |
| POST      | `/api/documents/`      | editor    | Upload a document   |
| PUT/PATCH | `/api/documents/{id}/` | editor    | Update a document   |
| DELETE    | `/api/documents/{id}/` | admin     | Delete a document   |

Uploads are `multipart/form-data` with `title` and `file` fields. Responses
never include the raw file path — only a short-lived presigned `download_url`.


## Audit logging

Every document action — create, update, delete, list, and retrieve — is
recorded to an immutable audit log capturing the actor, the action, and the
document (id + title). All writes go through a single audit **service**
(`documents/services.py`), and are best-effort: if a log write fails, the
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

Example upload:

```bash
curl -X POST http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer <access-token>" \
  -F "title=Q4 Report" \
  -F "file=@/path/to/report.pdf"
```

> **Dev note — presigned URL host.** Inside Docker, the app signs URLs
> against the `minio` hostname (e.g. `http://minio:9000/...`). To open such a
> link from your host browser, add `127.0.0.1 minio` to your `/etc/hosts`.

## Running the tests

```bash
pytest
```

The suite runs fully offline — no MinIO or Redis required (in-memory
fallbacks are used).

## Project structure

```
.
├── config/          # Settings, URLs, WSGI/ASGI
├── accounts/        # Custom user model, roles, JWT endpoints
├── common/          # Shared permissions, health check
├── documents/       # Document model, storage, API
├── tests/           # Test suite, mirrors the app layout
├── docker-compose.yml
├── Dockerfile
└── manage.py
```