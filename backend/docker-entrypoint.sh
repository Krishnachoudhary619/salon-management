#!/bin/sh
set -eu

echo "Running database migrations..."
alembic upgrade head

echo "Starting API server..."
GRACEFUL_SHUTDOWN_SECONDS="${GRACEFUL_SHUTDOWN_SECONDS:-30}"

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --timeout-graceful-shutdown "${GRACEFUL_SHUTDOWN_SECONDS}"
