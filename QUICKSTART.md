# TraceFlow Cloud SQL & Cloud Run - Quick Start

## TL;DR - Deploy in 5 Minutes

### Prerequisites
```bash
# 1. Install gcloud CLI
# Windows: https://cloud.google.com/sdk/docs/install
# macOS: brew install --cask google-cloud-sdk
# Linux: https://cloud.google.com/sdk/docs/install

# 2. Authenticate
gcloud auth login
gcloud config set project traceflow-2026
```

### Deploy Cloud SQL (PostgreSQL)

**Windows PowerShell:**
```powershell
.\deploy-cloudsql.ps1
```

**macOS/Linux:**
```bash
chmod +x deploy-cloudsql.sh
./deploy-cloudsql.sh
```

### Deploy to Cloud Run

**After the script completes:**

1. **Rename Dockerfile for Cloud Run:**
```bash
cp Dockerfile Dockerfile.bak
cp Dockerfile.cloudrun Dockerfile
```

2. **Deploy:**
```bash
gcloud builds submit --tag gcr.io/traceflow-2026/traceflow-app

gcloud run deploy traceflow-app \
    --image gcr.io/traceflow-2026/traceflow-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --env-vars-file .env.cloudsql \
    --memory 512Mi
```

3. **Get your URL:**
```bash
gcloud run services describe traceflow-app --region us-central1 --format='value(status.url)'
```

**Done!** Your TraceFlow app is live at that URL.

---

## What The Scripts Do

### `deploy-cloudsql.ps1` / `deploy-cloudsql.sh`
- ✓ Creates PostgreSQL 15 Cloud SQL instance
- ✓ Creates database and user
- ✓ Generates secure passwords
- ✓ Sets up IAM permissions
- ✓ Creates `.env.cloudsql` with connection details
- ✓ Creates Cloud Run deployment script

### `cloud-run-entrypoint.sh`
- ✓ Runs Django migrations automatically
- ✓ Collects static files
- ✓ Starts Gunicorn with optimal settings for Cloud Run

---

## Configuration Files Created

| File | Purpose |
|------|---------|
| `.env.cloudsql` | Database credentials and connection details |
| `cloud-run-entrypoint.sh` | Startup script for Cloud Run |
| `Dockerfile.cloudrun` | Optimized Docker image for Cloud Run |
| `.gcloudignore` | Files to exclude from Cloud Build |

---

## Common Tasks

### Test Local Connection
```bash
# Terminal 1: Start Cloud SQL Proxy
source .env.cloudsql  # Load environment variables
cloud_sql_proxy -instances=$INSTANCE_CONNECTION_NAME=tcp:5432

# Terminal 2: Connect to database
psql -h 127.0.0.1 -U traceflow_user -d postgres
```

### Run Migrations
```bash
# With proxy running
source .env.cloudsql
python manage.py migrate
```

### View Cloud Run Logs
```bash
# Real-time logs
gcloud run logs read traceflow-app --region us-central1 --follow

# Last 100 lines
gcloud run logs read traceflow-app --region us-central1 --limit 100
```

### Update Application
```bash
# Push new version
gcloud builds submit --tag gcr.io/traceflow-2026/traceflow-app

# Deploy new version
gcloud run deploy traceflow-app \
    --image gcr.io/traceflow-2026/traceflow-app \
    --platform managed \
    --region us-central1
```

### Scale Cloud Run
```bash
# Increase memory for better performance
gcloud run deploy traceflow-app \
    --memory 1Gi \
    --region us-central1

# Set max instances
gcloud run services update traceflow-app \
    --max-instances 100 \
    --region us-central1
```

### Backup Database
```bash
# Create on-demand backup
gcloud sql backups create \
    --instance=traceflow-postgres

# List backups
gcloud sql backups list --instance=traceflow-postgres
```

---

## Troubleshooting

### "Permission denied" when running scripts
```bash
# Make scripts executable
chmod +x deploy-cloudsql.sh
chmod +x cloud-run-entrypoint.sh
```

### "502 Bad Gateway" on Cloud Run
```bash
# Check logs
gcloud run logs read traceflow-app --limit 100

# Common causes:
# 1. Migrations failed - check DB connection
# 2. Missing environment variables - verify .env.cloudsql
# 3. Port not set to 8080 - check Dockerfile
```

### Database connection refused
```bash
# Verify instance is running
gcloud sql instances list

# Check instance details
gcloud sql instances describe traceflow-postgres

# Restart instance if needed
gcloud sql instances restart traceflow-postgres
```

### Cloud Build failing
```bash
# Check build logs
gcloud builds log [BUILD_ID]

# Common causes:
# 1. Requirements.txt not found - ensure it's in project root
# 2. Python version mismatch - update Dockerfile
# 3. Missing environment files - ensure .gcloudignore is correct
```

---

## Performance Tips

### Cloud SQL
- **Development**: `db-f1-micro` (0.6 GB RAM)
- **Production**: `db-highmem-4` or larger
- Enable automated backups
- Monitor CPU/Memory in Cloud Console

### Cloud Run
- **Memory**: 512 MB is fine for small deployments
- **Workers**: 4 workers × 2 threads (good balance)
- **Max instances**: Start at 10, scale based on load
- Use concurrency to handle more requests per instance

### Database
- Add indexes on frequently queried columns
- Archive old reconciliation data periodically
- Use connection pooling (PgBouncer)

---

## Cost Estimates (USD/month)

| Component | Small | Medium | Large |
|-----------|-------|--------|-------|
| Cloud SQL (db-f1-micro) | $15-20 | - | - |
| Cloud SQL (highmem-4) | - | $300-400 | - |
| Cloud Run | $5-15 | $20-50 | $50-100+ |
| Storage | $2-5 | $5-10 | $10-20 |
| **Total** | **$22-40** | **$325-460** | **$60-120+** |

*Costs vary based on traffic, data stored, and query patterns.*

---

## Next Steps

1. **Custom Domain**: https://cloud.google.com/run/docs/mapping-custom-domains
2. **SSL Certificate**: Automatically issued by Cloud Run
3. **Monitoring**: Set up Cloud Monitoring alerts
4. **Backup Schedule**: https://cloud.google.com/sql/docs/postgres/backup-recovery
5. **Load Testing**: Test with production traffic patterns

---

## Security Checklist

- [ ] Database password stored securely (not in code)
- [ ] Django SECRET_KEY rotated
- [ ] DEBUG set to False in production
- [ ] ALLOWED_HOSTS configured correctly
- [ ] Database user has minimal required permissions
- [ ] Cloud SQL backup enabled
- [ ] Cloud Run IAM roles configured
- [ ] Secrets Manager used for sensitive data
- [ ] VPC for private database connections (optional)

---

## Support & Documentation

- [Google Cloud SQL Docs](https://cloud.google.com/sql/docs)
- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [Django Deployment Guide](https://docs.djangoproject.com/en/4.2/howto/deployment/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

**Project**: traceflow-2026  
**Region**: us-central1  
**Database**: PostgreSQL 15  
**Framework**: Django 4.2  
**Python**: 3.11
