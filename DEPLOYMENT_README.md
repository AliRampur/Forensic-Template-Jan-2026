# 🚀 TraceFlow GCP Cloud SQL & Cloud Run Deployment

Complete automation scripts to deploy TraceFlow with PostgreSQL on Google Cloud SQL and Django app on Google Cloud Run.

## 📋 What's Included

### Deployment Scripts
- **`deploy-cloudsql.ps1`** - Windows PowerShell deployment script
- **`deploy-cloudsql.sh`** - Linux/macOS Bash deployment script
- **`cloud-run-entrypoint.sh`** - Cloud Run startup script

### Configuration Files
- **`.env.cloudsql`** - Database credentials (auto-generated)
- **`Dockerfile.cloudrun`** - Production-ready Docker image
- **`.gcloudignore`** - Cloud Build ignore patterns

### Documentation
- **`QUICKSTART.md`** - 5-minute quick start guide ⭐ **START HERE**
- **`DEPLOYMENT_GUIDE.md`** - Comprehensive step-by-step guide
- **`DEPLOYMENT_SUMMARY.md`** - Overview and reference

## ⚡ Quick Start (5 minutes)

### 1. Prerequisites
```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud config set project traceflow-2026
```

### 2. Deploy Cloud SQL
**Windows PowerShell:**
```powershell
.\deploy-cloudsql.ps1
```

**macOS/Linux:**
```bash
chmod +x deploy-cloudsql.sh
./deploy-cloudsql.sh
```

### 3. Deploy to Cloud Run
```bash
# Use Cloud Run optimized Dockerfile
cp Dockerfile Dockerfile.bak
cp Dockerfile.cloudrun Dockerfile

# Build and deploy
gcloud builds submit --tag gcr.io/traceflow-2026/traceflow-app

gcloud run deploy traceflow-app \
    --image gcr.io/traceflow-2026/traceflow-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --env-vars-file .env.cloudsql \
    --memory 512Mi
```

### 4. Get Your URL
```bash
gcloud run services describe traceflow-app --region us-central1 --format='value(status.url)'
```

**Done!** Your app is live! 🎉

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **QUICKSTART.md** | 5-min setup, common commands, quick reference |
| **DEPLOYMENT_GUIDE.md** | Complete walkthrough, all options, troubleshooting |
| **DEPLOYMENT_SUMMARY.md** | Overview, file reference, feature summary |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Google Cloud Run                   │
│      TraceFlow Django Application            │
│   (Auto-scaling, HTTPS, 0-N instances)      │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│        Google Cloud SQL                      │
│    PostgreSQL 15 Database Instance           │
│  (Backups, HA, IAM Authentication)          │
└─────────────────────────────────────────────┘
```

## 🔐 Security Features

✅ Non-root Docker user  
✅ SSL/TLS encryption (Cloud Run)  
✅ IAM authentication  
✅ Secure password generation  
✅ Environment variable management  
✅ Automated backups  
✅ No hardcoded credentials  

## 💰 Cost Estimate

| Component | Monthly Cost |
|-----------|--------------|
| Cloud SQL (db-f1-micro) | $15-20 |
| Cloud Run | $5-10 |
| Storage | $2-5 |
| **Total** | **~$25-35** |

*Costs scale with usage; Free tier may apply*

## 📊 Features

### Cloud SQL
- ✅ PostgreSQL 15
- ✅ Automated daily backups
- ✅ High availability option
- ✅ Automatic patching
- ✅ Cloud SQL Auth

### Cloud Run
- ✅ Auto-scaling (0 to N instances)
- ✅ Automatic HTTPS/SSL
- ✅ Pay per request
- ✅ No infrastructure management
- ✅ Cloud Logging integration

### Django
- ✅ Migrations run automatically
- ✅ Static files collected
- ✅ Gunicorn optimized (4 workers × 2 threads)
- ✅ Health checks ready
- ✅ Monitoring ready

## 🛠️ What the Scripts Do

### `deploy-cloudsql.ps1` / `deploy-cloudsql.sh`
1. Creates Cloud SQL PostgreSQL instance
2. Creates database and user
3. Generates secure passwords
4. Configures IAM permissions
5. Outputs `.env.cloudsql` file
6. Provides next steps

### `cloud-run-entrypoint.sh`
1. Collects Django static files
2. Runs database migrations
3. Starts Gunicorn server
4. Handles graceful shutdown

## 📖 File Structure

```
TraceFlow/
├── deploy-cloudsql.ps1          # Windows deployment
├── deploy-cloudsql.sh            # Unix deployment
├── cloud-run-entrypoint.sh       # Cloud Run startup
├── Dockerfile                    # Local development
├── Dockerfile.cloudrun           # Cloud Run production
├── .env.cloudsql                 # Database config (generated)
├── .gcloudignore                 # Cloud Build ignore
├── QUICKSTART.md                 # ⭐ START HERE
├── DEPLOYMENT_GUIDE.md           # Full documentation
└── DEPLOYMENT_SUMMARY.md         # Overview
```

## 🚦 Deployment Status

After running the script, you'll have:

| Component | Status |
|-----------|--------|
| Cloud SQL Instance | ✅ Running |
| Database | ✅ Created |
| Database User | ✅ Created |
| Credentials | ✅ Saved (.env.cloudsql) |
| IAM Setup | ✅ Configured |
| Ready for Cloud Run | ✅ Yes |

## 🐛 Troubleshooting

**Can't run PowerShell script?**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**gcloud not found?**
- Install from: https://cloud.google.com/sdk/docs/install
- Or add to PATH: `C:\Program Files\Google\Cloud SDK\bin`

**Permission denied on Bash script?**
```bash
chmod +x deploy-cloudsql.sh
chmod +x cloud-run-entrypoint.sh
```

**Database connection issues?**
```bash
# Start Cloud SQL Proxy
cloud_sql_proxy -instances=[CONNECTION_NAME]=tcp:5432

# Test connection
psql -h 127.0.0.1 -U traceflow_user -d postgres
```

See **DEPLOYMENT_GUIDE.md** for more troubleshooting.

## 📞 Support Resources

- [Google Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Django Deployment Guide](https://docs.djangoproject.com/en/4.2/howto/deployment/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## ✅ Deployment Checklist

- [ ] gcloud CLI installed and authenticated
- [ ] Project set to `traceflow-2026`
- [ ] APIs enabled (run script or see DEPLOYMENT_GUIDE.md)
- [ ] Ran Cloud SQL deployment script
- [ ] `.env.cloudsql` created successfully
- [ ] Database connection tested
- [ ] Django migrations run: `python manage.py migrate`
- [ ] Docker image built: `gcloud builds submit`
- [ ] Cloud Run deployment complete
- [ ] Service URL verified
- [ ] Application tested in browser

## 🎯 Next Steps

1. **Read QUICKSTART.md** for commands and tips
2. **Read DEPLOYMENT_GUIDE.md** for detailed instructions
3. **Run deployment scripts** - automation handles the rest
4. **Test locally** with Cloud SQL Proxy
5. **Deploy to Cloud Run** using provided commands
6. **Monitor** via Cloud Console
7. **Scale** as needed (increase memory, max instances)

## 📝 Environment Variables

The script automatically generates `.env.cloudsql` with:

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=traceflow_user
DB_PASSWORD=[auto-generated]
DB_HOST=[cloud-sql-ip]
DB_PORT=5432
INSTANCE_CONNECTION_NAME=[for-proxy]
DEBUG=False
ALLOWED_HOSTS=*
DJANGO_SECRET_KEY=[auto-generated]
```

## 🔄 Continuous Deployment

To update your deployment:

```bash
# Make code changes
git add .
git commit -m "Update changes"

# Rebuild and redeploy
gcloud builds submit --tag gcr.io/traceflow-2026/traceflow-app

gcloud run deploy traceflow-app \
    --image gcr.io/traceflow-2026/traceflow-app \
    --region us-central1
```

## 📊 Monitoring

```bash
# View logs
gcloud run logs read traceflow-app --limit 50

# Watch logs in real-time
gcloud run logs read traceflow-app --follow

# Get service metrics
gcloud run services describe traceflow-app --region us-central1

# Check database status
gcloud sql instances describe traceflow-postgres
```

---

## 🎓 Learn More

- Start with: **QUICKSTART.md** ⭐
- Detailed guide: **DEPLOYMENT_GUIDE.md** 📖
- Overview: **DEPLOYMENT_SUMMARY.md** 📋

**Questions?** Check the relevant documentation above.

**Ready to deploy?** Start with QUICKSTART.md!

---

*Last Updated: January 26, 2026*  
*Project: traceflow-2026*  
*Region: us-central1*
