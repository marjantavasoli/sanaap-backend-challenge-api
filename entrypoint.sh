#!/bin/sh
set -e


exec gunicorn config.asgi:application \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}"