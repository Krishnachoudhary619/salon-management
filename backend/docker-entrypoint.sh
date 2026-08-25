#!/bin/sh
set -eu

echo "Running database migrations..."
alembic upgrade head

if [ "${RUN_SEED:-false}" = "true" ]; then
    echo "Seeding database..."
    python -m app.database.seed
fi

echo "Starting API server..."
PORT="${PORT:-8000}"
GRACEFUL_SHUTDOWN_SECONDS="${GRACEFUL_SHUTDOWN_SECONDS:-30}"

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --timeout-graceful-shutdown "${GRACEFUL_SHUTDOWN_SECONDS}"
