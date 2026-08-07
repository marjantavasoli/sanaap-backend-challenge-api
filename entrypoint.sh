#!/bin/sh
set -e

echo "Starting development server..."
exec python manage.py runserver 0.0.0.0:8000