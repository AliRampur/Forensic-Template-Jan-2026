# TraceFlow Cloud SQL & Cloud Run Deployment Guide

## Overview
This guide walks you through deploying TraceFlow with PostgreSQL on Google Cloud SQL and the Django app on Google Cloud Run.

## Prerequisites

### Required Tools
1. **Google Cloud SDK (gcloud)**
   - Windows: https://cloud.google.com/sdk/docs/install
   - macOS: `brew install --cask google-cloud-sdk`
   - Linux: https://cloud.google.com/sdk/docs/install

2. **Cloud SQL Proxy** (for local development)
   - https://cloud.google.com/sql/docs/postgres/quickstart-proxy

3. **Docker** (for Cloud Run)
   - https://www.docker.com/products/docker-desktop

4. **Git** (for version control)

5. **psql** (PostgreSQL client - optional, for testing)
   - Windows: https://www.postgresql.org/download/windows/
   - macOS: `brew install postgresql`
   - Linux: `sudo apt-get install postgresql-client`

### GCP Setup
1. Create a GCP project: https://console.cloud.google.com/welcome?project=traceflow-2026
2. Enable required APIs:
   ```bash
   gcloud services enable \
     sqladmin.googleapis.com \
     run.googleapis.com \
     compute.googleapis.com \
     container.googleapis.com
   ```

3. Set your project as default:
   ```bash
   gcloud config set project traceflow-2026
   ```

## Step 1: Deploy PostgreSQL to Cloud SQL

### Windows PowerShell
```powershell
# Run the deployment script
.\deploy-cloudsql.ps1 `
    -ProjectId "traceflow-2026" `
    -InstanceName "traceflow-postgres" `
    -Region "us-central1" `
    -Tier "db-f1-micro" `
    -DbName "postgres" `
    -DbUser "traceflow_user"
```

### macOS/Linux Bash
```bash
# Make the script executable
chmod +x deploy-cloudsql.sh

# Run the deployment script
./deploy-cloudsql.sh
```

### Manual Steps (if scripts fail)

1. **Create Cloud SQL Instance**
```bash
gcloud sql instances create traceflow-postgres \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --network=default \
    --availability-type=zonal \
    --database-flags=cloudsql_iam_authentication=on
```

2. **Create Database**
```bash
gcloud sql databases create postgres \
    --instance=traceflow-postgres
```

3. **Create Database User**
```bash
gcloud sql users create traceflow_user \
    --instance=traceflow-postgres \
    --password=[YOUR_SECURE_PASSWORD]
```

4. **Get Connection Details**
```bash
# Get connection name (for Cloud SQL Proxy)
gcloud sql instances describe traceflow-postgres \
    --format='value(connectionName)'

# Get IP address (for direct connections)
gcloud sql instances describe traceflow-postgres \
    --format='value(ipAddresses[0].ipAddress)'
```

## Step 2: Test Connection Locally

### Using Cloud SQL Proxy

1. **Download and install Cloud SQL Proxy**
   - Windows: Download from https://cloud.google.com/sql/docs/postgres/quickstart-proxy
   - macOS: `brew install cloud-sql-proxy`
   - Linux: Download binary

2. **Start the proxy in one terminal**
```bash
# Get your connection name from Step 1
cloud_sql_proxy -instances=[CONNECTION_NAME]=tcp:5432
```

3. **Test connection in another terminal**
```bash
# Using the .env.cloudsql file
source .env.cloudsql  # macOS/Linux

# Windows PowerShell
Get-Content .env.cloudsql | ForEach-Object { $_.Split('=')[0] | Set-Item "Env:\$($_.Split('=')[0])" "$($_.Split('=')[1])" }

# Connect to database
psql -h 127.0.0.1 -U traceflow_user -d postgres
```

4. **In psql, run some test queries**
```sql
-- Check version
SELECT version();

-- Check current database
SELECT current_database();

-- List tables
\dt
```

## Step 3: Configure Django for Cloud SQL

### Update settings.py

```python
import os
from pathlib import Path

# ... existing settings ...

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'postgres'),
        'USER': os.environ.get('DB_USER', 'traceflow_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# For Cloud SQL with Unix domain socket (Cloud Run)
if 'INSTANCE_CONNECTION_NAME' in os.environ:
    DATABASES['default']['HOST'] = f"/cloudsql/{os.environ['INSTANCE_CONNECTION_NAME']}"
```

### Install PostgreSQL Adapter

```bash
pip install psycopg2-binary
```

### Run Migrations

```bash
# With Cloud SQL Proxy running locally
source .env.cloudsql  # macOS/Linux
python manage.py migrate

# On Cloud Run, migrations run automatically via entrypoint
```

## Step 4: Prepare for Cloud Run Deployment

### Update settings.py for Production

```python
# Security settings
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = '/tmp/static'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = '/tmp/media'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

### Update Dockerfile for Cloud Run

```dockerfile
# Use official Python lightweight image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download and install Cloud SQL Proxy
RUN curl https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -o /cloud_sql_proxy && \
    chmod +x /cloud_sql_proxy

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Port
EXPOSE 8080

# Start application with Cloud SQL Proxy
CMD exec gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 4 \
    --threads 2 \
    --timeout 0 \
    --access-logfile - \
    --error-logfile - \
    traceflow.wsgi:application
```

### Add requirements

Ensure your requirements.txt includes:
```
Django>=4.2,<5.0
psycopg2-binary>=2.9
gunicorn>=21.2.0
pandas>=2.0.0
plotly>=5.18.0
python-Levenshtein>=0.21.0
Faker>=22.0.0
django-ninja>=1.1.0
```

## Step 5: Deploy to Cloud Run

### Option A: Using the automated script

```powershell
# Windows PowerShell
.\deploy-to-cloudrun.ps1
```

```bash
# macOS/Linux Bash
chmod +x deploy-to-cloudrun.sh
./deploy-to-cloudrun.sh
```

### Option B: Manual deployment

```bash
# 1. Build container image
gcloud builds submit --tag gcr.io/traceflow-2026/traceflow-app

# 2. Deploy to Cloud Run
gcloud run deploy traceflow-app \
    --image gcr.io/traceflow-2026/traceflow-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars DB_ENGINE=django.db.backends.postgresql \
    --set-env-vars INSTANCE_CONNECTION_NAME=[CONNECTION_NAME] \
    --set-env-vars DB_NAME=postgres \
    --set-env-vars DB_USER=traceflow_user \
    --set-env-vars DB_PASSWORD=[YOUR_PASSWORD] \
    --set-env-vars DJANGO_SECRET_KEY=[YOUR_SECRET_KEY] \
    --set-env-vars DEBUG=False \
    --set-env-vars ALLOWED_HOSTS=*.run.app,localhost \
    --memory 512Mi \
    --timeout 3600
```

## Step 6: Verify Deployment

### Check Cloud Run Service

```bash
# Get service details
gcloud run services describe traceflow-app --region us-central1

# Check logs
gcloud run logs read traceflow-app --region us-central1 --limit 50

# Monitor in real-time
gcloud run logs read traceflow-app --region us-central1 --follow
```

### Test the Application

1. Get the service URL:
```bash
gcloud run services describe traceflow-app \
    --region us-central1 \
    --format='value(status.url)'
```

2. Visit the URL in your browser or test with curl:
```bash
curl https://[SERVICE_URL]/
curl https://[SERVICE_URL]/api/accounts/
```

## Troubleshooting

### Cloud SQL Connection Issues

**Error: "Connection refused"**
- Ensure Cloud SQL instance is running
- Check firewall rules allow your IP
- Verify Cloud SQL Proxy is running locally

**Error: "IAM authentication failed"**
- Run: `gcloud projects add-iam-policy-binding traceflow-2026 --member=user:[YOUR_EMAIL] --role=roles/cloudsql.client`
- Re-authenticate: `gcloud auth login`

### Cloud Run Issues

**Error: "502 Bad Gateway"**
- Check logs: `gcloud run logs read traceflow-app --limit 100`
- Ensure migrations ran successfully
- Verify environment variables are set correctly

**Error: "Out of memory"**
- Increase memory: `--memory 1Gi`
- Optimize Django settings for production

### Database Connection

**Error: "No such table"**
- Migrations didn't run
- Run: `python manage.py migrate`
- Verify database user has proper permissions

## Next Steps

1. **Set up custom domain**: https://cloud.google.com/run/docs/mapping-custom-domains
2. **Enable Cloud CDN**: https://cloud.google.com/run/docs/quickstarts/build-and-deploy#cdn
3. **Set up monitoring**: https://cloud.google.com/run/docs/monitoring
4. **Enable authentication**: https://cloud.google.com/run/docs/authenticating/service-to-service
5. **Set up continuous deployment**: https://cloud.google.com/run/docs/continuous-deployment

## Cost Optimization

- **Cloud SQL**: Use shared core (db-f1-micro) for development, scale as needed
- **Cloud Run**: Pay per request, no charges for idle time
- **Storage**: Use Cloud Storage for media files instead of Cloud Run's ephemeral storage
- **Database backups**: Enable automated backups (included in pricing)

## Security Best Practices

1. **Never commit .env files** - Add to .gitignore
2. **Rotate passwords** regularly via Cloud SQL
3. **Use VPC** for private connections
4. **Enable SSL** for database connections
5. **Set up Cloud Armor** for DDoS protection
6. **Use secrets** in production (not environment variables)

## Resources

- [Google Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Django on Google Cloud](https://cloud.google.com/python/django)
- [PostgreSQL Best Practices](https://www.postgresql.org/docs/current/intro.html)

---

For questions or issues, contact the TraceFlow team.
