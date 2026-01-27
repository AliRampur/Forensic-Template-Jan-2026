#!/bin/bash

# Cloud Run Entrypoint Script for TraceFlow
# This script runs on Cloud Run startup to prepare the application

set -e

echo "=== TraceFlow Cloud Run Initialization ==="

# Check required environment variables
if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ] || [ -z "$INSTANCE_CONNECTION_NAME" ]; then
    echo "Warning: Database environment variables not fully set"
    echo "  DB_USER: $DB_USER"
    echo "  DB_NAME: $DB_NAME"
    echo "  INSTANCE_CONNECTION_NAME: $INSTANCE_CONNECTION_NAME"
fi

echo "Starting Django application..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist (optional)
# echo "Creating default superuser..."
# python manage.py shell << END
# from django.contrib.auth import get_user_model
# User = get_user_model()
# if not User.objects.filter(username='admin').exists():
#     User.objects.create_superuser('admin', 'admin@traceflow.com', 'admin')
#     print("Superuser 'admin' created")
# else:
#     print("Superuser 'admin' already exists")
# END

echo "Starting Gunicorn server..."
echo "Listening on 0.0.0.0:8080"

# Start Gunicorn
exec gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 4 \
    --threads 2 \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --timeout 0 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    traceflow.wsgi:application
