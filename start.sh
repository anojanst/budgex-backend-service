#!/bin/sh
set -e

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Get PORT from environment (Railway sets this automatically)
# Default to 8000 if not set (for local development)
PORT=${PORT:-8000}
echo "Starting server on port $PORT"

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"

