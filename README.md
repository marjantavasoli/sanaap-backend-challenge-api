# Sanaap Document Management API

A secure document management service built with Django REST Framework.
Documents are stored in MinIO, access is controlled with role-based
permissions, and the full stack runs under Docker Compose.

## Tech stack

- Python / Django 5 / Django REST Framework
- JWT authentication (djangorestframework-simplejwt)
- PostgreSQL (database)
- Redis (cache)
- MinIO (object storage)
- Docker & Docker Compose

## Requirements

- Python 3.12+
- Docker & Docker Compose (for the full stack)

## Local setup
## Running with Docker (recommended)

The full stack — Django, PostgreSQL, Redis, and MinIO — runs under Docker
Compose.

### Prerequisites

- Docker and Docker Compose

### Steps

```bash
# 1. Create your env file and edit the secrets
cp .env.example .env
#    -> set a strong SECRET_KEY

# 2. Build and start the stack
docker compose up --build
```

On startup, a dedicated `migrate` service applies database migrations and
exits; the `web` service starts only after migrations finish. Once the
stack is up:

- API: http://localhost:8000/api/
- Health check: http://localhost:8000/api/health/
- MinIO console: http://localhost:9001 (log in with the MinIO credentials)

### Data persistence

PostgreSQL and MinIO store their data in named Docker volumes
(`postgres_data`, `minio_data`). This data survives `docker compose down`
and image rebuilds. To wipe it, run `docker compose down -v`.

### Create the first admin user

```bash
docker compose exec web python manage.py createsuperuser
```

Superusers are assigned the `admin` role automatically.

### Services

| Service  | Image           | Port(s)      | Purpose                     |
|----------|-----------------|--------------|-----------------------------|
| web      | (built locally) | 8000         | Django API                  |
| migrate  | (built locally) | —            | Runs migrations, then exits |
| db       | postgres:16     | 5432         | Database                    |
| redis    | redis:7         | 6379         | Cache                       |
| minio    | minio/minio     | 9000, 9001   | Object storage              |

> The `web` service runs Django's development server. A production-grade
> app server (Gunicorn) and reverse proxy (Nginx) are added in a later
> branch.

## Running locally without Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          
python manage.py migrate
python manage.py runserver
```

The API is then available at http://localhost:8000/api/.
A health check is exposed at http://localhost:8000/api/health/.

## Running the tests

```bash
pytest
```
## Authentication

The API uses JWT (via `djangorestframework-simplejwt`).

```bash
# Obtain a token pair
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "<user>", "password": "<pass>"}'

# Use the access token on protected endpoints
curl http://localhost:8000/api/... \
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

Create the first admin with `python manage.py createsuperuser`
