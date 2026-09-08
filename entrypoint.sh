#!/bin/sh
set -e
 
echo "Waiting for dependent services (if any)..."
# If you switch to Postgres/Redis with healthchecks in compose, this section
# can stay empty since depends_on + service_healthy already gates startup.
 
echo "Making migrations..."
python manage.py makemigrations --noinput
 
echo "Applying migrations..."
python manage.py migrate --noinput
 
echo "Collecting static files..."
python manage.py collectstatic --noinput || true
 
echo "Starting: $@"
exec "$@"
 