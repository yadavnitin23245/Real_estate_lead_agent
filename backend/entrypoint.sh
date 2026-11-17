#!/bin/sh
set -e

# Create DB if missing, apply migrations, and (optionally) seed - all code-first.
if [ "${SEED_ON_STARTUP:-true}" = "true" ]; then
  python manage.py setup
else
  python manage.py setup --no-seed
fi

echo "==> Starting API"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app
