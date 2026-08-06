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

```bash
# 1. Create and activate a virtualenv
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements-dev.txt

# 3. Create your local env file
cp .env.example .env

# 4. Apply migrations and start the dev server
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
