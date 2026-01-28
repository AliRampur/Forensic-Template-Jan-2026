# TraceFlow - Forensic Accounting System
## Complete Documentation

> **Last Updated:** January 27, 2026  
> **Project:** traceflow-2026 (agorapolis)  
> **Region:** us-central1  
> **Database:** PostgreSQL 15 on Cloud SQL  
> **Framework:** Django 4.2.27  
> **Python:** 3.11 (Cloud Run), 3.14 (Local Dev)

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Deployment Guides](#deployment-guides)
- [Requirements & Dependencies](#requirements--dependencies)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

---

<details>
<summary><h2>📖 Overview</h2></summary>

### About TraceFlow

TraceFlow is a Django-based forensic accounting application designed for analyzing property inventory, commissions, and financial transactions with built-in forensic red flag detection.

### Key Features

- **Real Inventory Data Management**: Track 4,295+ property units across multiple locations
- **Forensic Analysis Dashboard**: Identify MCO mismatches, missing documentation, and unsupported commissions
- **Money Flow Visualization**: Sankey diagrams with Plotly to trace property sales through commission payments
- **Property Portfolio Tracking**: Manage inventory across 5 properties (Gold Canyon, PEM, Springs, Sunrise, Other)
- **Commission Analysis**: Track and validate commission records with support status (Supported, Unsupported, Insufficient Evidence)
- **Professional Resume Page**: Featuring Ali Rampurawala's expertise in forensic accounting
- **Cloud-Ready**: Deployed on GCP Cloud Run with Cloud SQL PostgreSQL

### Current Status

✅ **Deployed**: https://traceflow-502947376621.us-central1.run.app  
✅ **Database**: Cloud SQL PostgreSQL (agorapolis:us-central1:traceflow-db, IP: 35.188.121.201)  
✅ **GitHub**: https://github.com/AliRampur/Forensic-Template-Jan-2026  
✅ **Data**: 4,295 inventory units imported (Gold Canyon: 1,106, Other: 132, PEM: 1,897, Springs: 616, Sunrise: 544)  
✅ **Commissions**: 179 commission records tracked  

</details>

---

<details>
<summary><h2>🚀 Quick Start</h2></summary>

### 5-Minute Deployment

#### Prerequisites
```bash
# Install gcloud CLI
# Windows: https://cloud.google.com/sdk/docs/install
# macOS: brew install --cask google-cloud-sdk
# Linux: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud config set project agorapolis
```

#### Deploy Cloud SQL (PostgreSQL)

**Windows PowerShell:**
```powershell
.\deploy-cloudsql.ps1
```

**macOS/Linux:**
```bash
chmod +x deploy-cloudsql.sh
./deploy-cloudsql.sh
```

#### Deploy to Cloud Run

**After the script completes:**

1. **Rename Dockerfile for Cloud Run:**
```bash
cp Dockerfile Dockerfile.bak
cp Dockerfile.cloudrun Dockerfile
```

2. **Deploy:**
```bash
gcloud builds submit --tag gcr.io/agorapolis/traceflow-app

gcloud run deploy traceflow-app \
    --image gcr.io/agorapolis/traceflow-app \
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

### Common Tasks

#### Test Local Connection
```bash
# Terminal 1: Start Cloud SQL Proxy
source .env.cloudsql  # Load environment variables
cloud_sql_proxy -instances=$INSTANCE_CONNECTION_NAME=tcp:5432

# Terminal 2: Connect to database
psql -h 127.0.0.1 -U traceflow_user -d postgres
```

#### Run Migrations
```bash
# With proxy running
source .env.cloudsql
python manage.py migrate
```

#### View Cloud Run Logs
```bash
# Real-time logs
gcloud run logs read traceflow-app --region us-central1 --follow

# Last 100 lines
gcloud run logs read traceflow-app --region us-central1 --limit 100
```

#### Update Application
```bash
# Push new version
gcloud builds submit --tag gcr.io/agorapolis/traceflow-app

# Deploy new version
gcloud run deploy traceflow-app \
    --image gcr.io/agorapolis/traceflow-app \
    --platform managed \
    --region us-central1
```

#### Scale Cloud Run
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

#### Backup Database
```bash
# Create on-demand backup
gcloud sql backups create \
    --instance=traceflow-db

# List backups
gcloud sql backups list --instance=traceflow-db
```

</details>

---

<details>
<summary><h2>📁 Project Structure</h2></summary>

### Current Architecture

```
TraceFlow - Forensic Accounting/
├── forensics/              # Main Django app (unified)
│   ├── models.py          # Placeholder pointing to inventory_models.py
│   ├── inventory_models.py # Active models (Property, InventoryUnit, Commission)
│   ├── views.py           # All views (dashboard, Sankey, inventory lists)
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin interface configuration
│   ├── tests.py           # Comprehensive test suite
│   ├── templatetags/      # Custom template filters
│   │   ├── __init__.py
│   │   └── forensics_filters.py  # div, mul, percentage filters
│   ├── management/        # Custom management commands
│   │   └── commands/
│   │       └── import_inventory.py  # CSV data importer
│   ├── data/              # Source CSV files
│   │   └── LHS_Inventory detail_01.07.2026.xlsx - [Property].csv (5 files)
│   └── templates/         # HTML templates
│       └── forensics/
│           ├── base.html           # Base template with navigation
│           ├── dashboard.html      # Main dashboard with stats
│           ├── sankey.html         # Money flow visualization
│           ├── inventory_metrics.html  # Forensic analysis dashboard
│           ├── inventory_unit_list.html  # Paginated units list
│           ├── commission_list.html      # Paginated commissions list
│           └── resume.html         # Ali Rampurawala resume page
├── traceflow/             # Django project configuration
│   ├── settings.py        # PostgreSQL config, Cloud SQL detection
│   ├── urls.py            # Project URL routing
│   ├── wsgi.py
│   └── asgi.py
├── manage.py
├── requirements.txt
├── Dockerfile             # Local development
├── Dockerfile.cloudrun    # Cloud Run optimized
├── cloud-run-entrypoint.sh  # Cloud Run startup script
├── deploy-cloudsql.ps1    # Windows deployment automation
├── deploy-cloudsql.sh     # Unix deployment automation
├── .env                   # Local environment variables
├── .env.cloudsql          # Cloud SQL configuration (auto-generated)
└── .gcloudignore          # Cloud Build exclusions
```

### Key Models

#### Property
- `full_name`: Complete property name
- `short_name`: Abbreviated name for displays
- `base_property`: Base property identifier

#### InventoryUnit (54+ fields)
Core financial data:
- `unit_number`: Unit/lot identifier
- `property`: Foreign key to Property
- `bank_gl_balance`: Bank general ledger balance
- `sale_amount_pre_tax`: Sale amount before tax
- `rental_income`: Rental income amount

Forensic tracking:
- `current_lhs_property`: Boolean - Is this LHS owned?
- `is_lhs_rental`: Boolean - Is this an LHS rental?
- `mco_owner_matches`: Boolean - Does MCO owner match records?
- `mco_available`: Boolean - Is MCO documentation available?
- `home_sale_entity_mco`: Boolean - Does home sale entity match MCO?

#### Commission
- `unit`: Foreign key to InventoryUnit
- `amount`: Commission amount
- `recipient`: Commission recipient name
- `status`: SUPPORTED / UNSUPPORTED / INSUFFICIENT
- `percentage_of_sales`: Percentage of sale amount
- `memo`: Description
- `comments`: Additional notes

</details>

---

<details>
<summary><h2>⚙️ Setup Instructions</h2></summary>

### Local Development Setup

#### Prerequisites

- Python 3.11+
- PostgreSQL database (Cloud SQL or local)
- pip (Python package manager)
- Virtual environment tool

#### Installation Steps

1. **Clone the repository:**
```bash
git clone https://github.com/AliRampur/Forensic-Template-Jan-2026.git
cd "TraceFlow - Forensic Accounting"
```

2. **Create a virtual environment:**
```bash
python -m venv .venv
```

3. **Activate the virtual environment:**
- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Set up environment variables:**
Create a `.env` file with:
```
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=postgres
DB_USER=traceflow_user
DB_PASSWORD=your-password
DB_HOST=35.188.121.201
DB_PORT=5432
```

6. **Run migrations:**
```bash
python manage.py migrate
```

7. **Create a superuser:**
```bash
python manage.py createsuperuser
```

8. **Import inventory data (optional):**
```bash
python manage.py import_inventory
```

9. **Run the development server:**
```bash
python manage.py runserver
```

10. **Access the application:**
- Dashboard: http://127.0.0.1:8000/
- Admin interface: http://127.0.0.1:8000/admin/
- Sankey visualization: http://127.0.0.1:8000/sankey/
- Inventory Metrics: http://127.0.0.1:8000/inventory/metrics/
- Inventory Units: http://127.0.0.1:8000/inventory/units/
- Commissions: http://127.0.0.1:8000/inventory/commissions/
- Resume: http://127.0.0.1:8000/resume/

### Database Configuration

#### Cloud SQL Connection (Local Development)

**With Cloud SQL Proxy:**
```bash
# Terminal 1: Start proxy
cloud_sql_proxy -instances=agorapolis:us-central1:traceflow-db=tcp:5432

# Terminal 2: Configure .env
DB_HOST=127.0.0.1
DB_PORT=5432
```

**Direct Connection:**
```bash
DB_HOST=35.188.121.201
DB_PORT=5432
```

#### Cloud Run Connection

The app automatically detects Cloud Run environment and uses Unix socket:
```python
# In settings.py - automatic detection
if 'INSTANCE_CONNECTION_NAME' in os.environ:
    DATABASES['default']['HOST'] = f"/cloudsql/{os.environ['INSTANCE_CONNECTION_NAME']}"
```

</details>

---

<details>
<summary><h2>☁️ Deployment Guides</h2></summary>

### What Gets Created in GCP

1. **Cloud SQL Instance**: `traceflow-db`
   - PostgreSQL 15
   - db-f1-micro tier (0.6 GB RAM)
   - Automated backups
   - IAM authentication enabled

2. **Database**: `postgres`
   - Schema ready for Django migrations
   - User: `traceflow_user`

3. **Service Account**: For Cloud SQL authentication

4. **Firewall Rules**: Allow connections from Cloud Run and authorized IPs

5. **Cloud Run Service**: `traceflow-app`
   - Managed platform
   - Automatic HTTPS/SSL
   - Auto-scaling (0 to N instances)

### Configuration Files Generated

| File | Purpose |
|------|---------|
| `.env.cloudsql` | Database credentials and connection details |
| `cloud-run-entrypoint.sh` | Startup script for Cloud Run |
| `Dockerfile.cloudrun` | Optimized Docker image for Cloud Run |
| `.gcloudignore` | Files to exclude from Cloud Build |

### Deployment Flow

```
1. Run deployment script (PowerShell/Bash)
   ↓
2. Creates Cloud SQL instance (PostgreSQL 15)
   ↓
3. Generates database credentials
   ↓
4. Creates .env.cloudsql configuration
   ↓
5. Ready for Cloud Run deployment
   ↓
6. Build Docker image: gcloud builds submit
   ↓
7. Deploy to Cloud Run: gcloud run deploy
```

### Manual Cloud SQL Setup (Alternative)

If scripts fail, follow these manual steps:

1. **Create Cloud SQL Instance**
```bash
gcloud sql instances create traceflow-db \
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
    --instance=traceflow-db
```

3. **Create Database User**
```bash
gcloud sql users create traceflow_user \
    --instance=traceflow-db \
    --password=[YOUR_SECURE_PASSWORD]
```

4. **Authorize Your IP**
```bash
gcloud sql instances patch traceflow-db \
    --authorized-networks=[YOUR_IP_ADDRESS]
```

5. **Get Connection Details**
```bash
# Get connection name (for Cloud SQL Proxy)
gcloud sql instances describe traceflow-db \
    --format='value(connectionName)'

# Get IP address (for direct connections)
gcloud sql instances describe traceflow-db \
    --format='value(ipAddresses[0].ipAddress)'
```

### Manual Cloud Run Deployment

```bash
# 1. Build container image
gcloud builds submit --tag gcr.io/agorapolis/traceflow-app

# 2. Deploy to Cloud Run
gcloud run deploy traceflow-app \
    --image gcr.io/agorapolis/traceflow-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars DB_ENGINE=django.db.backends.postgresql \
    --set-env-vars INSTANCE_CONNECTION_NAME=agorapolis:us-central1:traceflow-db \
    --set-env-vars DB_NAME=postgres \
    --set-env-vars DB_USER=traceflow_user \
    --set-env-vars DB_PASSWORD=[YOUR_PASSWORD] \
    --set-env-vars DJANGO_SECRET_KEY=[YOUR_SECRET_KEY] \
    --set-env-vars DEBUG=False \
    --set-env-vars ALLOWED_HOSTS=*.run.app,localhost \
    --memory 512Mi \
    --timeout 3600
```

### Cost Breakdown (Monthly)

| Component | Small | Medium | Large |
|-----------|-------|--------|-------|
| Cloud SQL (db-f1-micro) | $15-20 | - | - |
| Cloud SQL (highmem-4) | - | $300-400 | - |
| Cloud Run | $5-15 | $20-50 | $50-100+ |
| Storage | $2-5 | $5-10 | $10-20 |
| **Total** | **$22-40** | **$325-460** | **$370-520** |

*Costs vary based on traffic, data stored, and query patterns. Free tier may apply.*

### Performance Tips

#### Cloud SQL
- **Development**: `db-f1-micro` (0.6 GB RAM)
- **Production**: `db-highmem-4` or larger
- Enable automated backups
- Monitor CPU/Memory in Cloud Console

#### Cloud Run
- **Memory**: 512 MB is fine for small deployments
- **Workers**: 4 workers × 2 threads (good balance)
- **Max instances**: Start at 10, scale based on load
- Use concurrency to handle more requests per instance

#### Database
- Add indexes on frequently queried columns
- Archive old data periodically
- Use connection pooling (PgBouncer)

### Security Checklist

- [x] Database password stored securely (not in code)
- [x] Django SECRET_KEY generated cryptographically
- [x] DEBUG set to False in production
- [x] ALLOWED_HOSTS configured correctly
- [x] Database user has minimal required permissions
- [x] Cloud SQL backup enabled
- [x] Cloud Run IAM roles configured
- [x] Non-root Docker user
- [ ] Secrets Manager for sensitive data (recommended upgrade)
- [ ] VPC for private database connections (optional)

</details>

---

<details>
<summary><h2>📦 Requirements & Dependencies</h2></summary>

### Python Dependencies

```
Django>=4.2,<5.0
psycopg2-binary>=2.9
pandas>=2.0.0
plotly>=5.18.0
gunicorn>=21.2.0
python-Levenshtein>=0.21.0
Faker>=22.0.0
django-ledger>=0.6.3
django-ninja>=1.1.0
```

### System Requirements

- **Python**: 3.11+ (3.14 supported for local dev)
- **PostgreSQL**: 15
- **RAM**: 512MB minimum (Cloud Run), 2GB+ recommended for local
- **Disk**: 1GB minimum for application files
- **Network**: Outbound internet access for Cloud SQL connection

### Optional Tools

- **Cloud SQL Proxy**: For local development with Cloud SQL
- **Docker**: For containerized deployment
- **Git**: For version control
- **psql**: PostgreSQL command-line client

### Django Apps

Installed apps:
- `django.contrib.admin`
- `django.contrib.auth`
- `django.contrib.contenttypes`
- `django.contrib.sessions`
- `django.contrib.messages`
- `django.contrib.staticfiles`
- `django.contrib.humanize` (for number formatting)
- `forensics` (main application)

</details>

---

<details>
<summary><h2>🔧 Troubleshooting</h2></summary>

### Common Issues

#### "Permission denied" when running scripts
```bash
# Make scripts executable
chmod +x deploy-cloudsql.sh
chmod +x cloud-run-entrypoint.sh
```

#### "502 Bad Gateway" on Cloud Run
```bash
# Check logs
gcloud run logs read traceflow-app --limit 100

# Common causes:
# 1. Migrations failed - check DB connection
# 2. Missing environment variables - verify .env.cloudsql
# 3. Port not set to 8080 - check Dockerfile
```

#### Database connection refused
```bash
# Verify instance is running
gcloud sql instances list

# Check instance details
gcloud sql instances describe traceflow-db

# Restart instance if needed
gcloud sql instances restart traceflow-db
```

#### Cloud Build failing
```bash
# Check build logs
gcloud builds log [BUILD_ID]

# Common causes:
# 1. Requirements.txt not found - ensure it's in project root
# 2. Python version mismatch - update Dockerfile
# 3. Missing environment files - ensure .gcloudignore is correct
```

#### Static files not loading (404 errors)
```bash
# Cause: DEBUG=False prevents Django from serving static files locally
# Solutions:
# 1. Set DEBUG=True in .env for local development
# 2. Use Cloud Run deployment (static files served via Whitenoise/collectstatic)
# 3. Configure web server (nginx/Apache) for production static file serving
```

#### Import errors with models
```bash
# Cause: Old Account/Transaction/ReconciliationMatch models removed
# Solution: These models have been replaced with inventory models
# - Use: Property, InventoryUnit, Commission
# - Location: forensics/inventory_models.py
```

#### Template filter errors
```bash
# Cause: Missing custom template filters
# Solution: Ensure forensics/templatetags/forensics_filters.py exists
# Required filters: div, mul, percentage
# Enable in template: {% load forensics_filters %}
```

#### CSV import failures
```bash
# Verify CSV files exist
ls forensics/data/

# Run import command
python manage.py import_inventory

# Common issues:
# 1. Wrong skiprows value - data starts at row 8, not row 5
# 2. Column name mismatch - check leading/trailing spaces
# 3. Boolean parsing errors - ensure parse_boolean returns False by default
```

### GCP-Specific Issues

#### gcloud command not found
```bash
# Windows: Add to PATH
# C:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin

# macOS/Linux: Source the path
source ~/google-cloud-sdk/path.bash.inc
```

#### Authentication Issues
```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project agorapolis

# Verify
gcloud config list
```

#### IAM Permission Errors
```bash
# Grant yourself Cloud SQL client role
gcloud projects add-iam-policy-binding agorapolis \
    --member=user:[YOUR_EMAIL] \
    --role=roles/cloudsql.client

# Grant Cloud Run admin role
gcloud projects add-iam-policy-binding agorapolis \
    --member=user:[YOUR_EMAIL] \
    --role=roles/run.admin
```

#### PowerShell Execution Policy Error
```powershell
# Allow running scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Database Issues

#### Migrations not applying
```bash
# Check migration status
python manage.py showmigrations

# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# If stuck, try fake migration
python manage.py migrate --fake [app_name] [migration_name]
```

#### Can't connect to Cloud SQL locally
```bash
# Ensure Cloud SQL Proxy is running
cloud_sql_proxy -instances=agorapolis:us-central1:traceflow-db=tcp:5432

# Test connection
psql -h 127.0.0.1 -U traceflow_user -d postgres

# Check firewall rules
gcloud sql instances describe traceflow-db --format='value(settings.ipConfiguration)'
```

#### Out of memory on Cloud Run
```bash
# Increase memory allocation
gcloud run deploy traceflow-app \
    --memory 1Gi \
    --region us-central1
```

</details>

---

<details>
<summary><h2>📚 Additional Resources</h2></summary>

### Official Documentation

- [Google Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Django Documentation](https://docs.djangoproject.com/en/4.2/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Plotly Python Documentation](https://plotly.com/python/)

### Project Resources

- **Production URL**: https://traceflow-502947376621.us-central1.run.app
- **GitHub Repository**: https://github.com/AliRampur/Forensic-Template-Jan-2026
- **Database IP**: 35.188.121.201:5432
- **Database Connection**: agorapolis:us-central1:traceflow-db

### Key Commands Reference

#### Django Management
```bash
python manage.py migrate              # Run migrations
python manage.py makemigrations       # Create migrations
python manage.py createsuperuser      # Create admin user
python manage.py collectstatic        # Collect static files
python manage.py import_inventory     # Import CSV data
python manage.py runserver            # Start dev server
```

#### GCP Cloud SQL
```bash
gcloud sql instances list             # List instances
gcloud sql instances describe NAME    # Instance details
gcloud sql databases list -i NAME     # List databases
gcloud sql backups list -i NAME       # List backups
gcloud sql backups create -i NAME     # Create backup
```

#### GCP Cloud Run
```bash
gcloud run services list              # List services
gcloud run services describe NAME     # Service details
gcloud run logs read NAME --follow    # Stream logs
gcloud run deploy NAME                # Deploy/update service
gcloud run revisions list             # List revisions
```

#### Docker
```bash
docker build -t traceflow .           # Build image
docker run -p 8000:8000 traceflow     # Run container
docker ps                             # List containers
docker logs CONTAINER_ID              # View logs
```

### Next Steps

1. **Custom Domain**: Map a custom domain to your Cloud Run service
2. **SSL Certificate**: Automatically issued by Cloud Run for custom domains
3. **Monitoring**: Set up Cloud Monitoring alerts for errors and performance
4. **Backup Schedule**: Configure automated backup schedule in Cloud SQL
5. **Load Testing**: Test with production traffic patterns
6. **CI/CD**: Set up automated deployment pipeline with GitHub Actions
7. **Secrets Management**: Migrate to Google Secret Manager for production
8. **VPC Peering**: Configure private VPC for enhanced security

### Support Contacts

- **Project Lead**: Ali Rampurawala
- **GitHub Issues**: https://github.com/AliRampur/Forensic-Template-Jan-2026/issues
- **GCP Support**: https://cloud.google.com/support

</details>

---

## Quick Reference Links

| Resource | Link |
|----------|------|
| **Production App** | https://traceflow-502947376621.us-central1.run.app |
| **GitHub Repo** | https://github.com/AliRampur/Forensic-Template-Jan-2026 |
| **Local Dev** | http://127.0.0.1:8000/ |
| **Admin Panel** | /admin/ |
| **Inventory Metrics** | /inventory/metrics/ |
| **Sankey Diagram** | /sankey/ |
| **Resume Page** | /resume/ |

---

## Deployment Checklist

- [x] gcloud CLI installed and authenticated
- [x] Project set to `agorapolis`
- [x] Cloud SQL instance created (`traceflow-db`)
- [x] Database and user configured
- [x] `.env.cloudsql` generated
- [x] Database connection tested
- [x] Django migrations completed
- [x] Inventory data imported (4,295 units)
- [x] Docker image built and pushed
- [x] Cloud Run deployment complete
- [x] Service URL verified and tested
- [x] GitHub repository updated
- [ ] Custom domain configured (optional)
- [ ] Monitoring alerts set up (optional)
- [ ] Backup schedule verified

---

**Ready to deploy?** Start with the Quick Start section above!

*For questions or issues, check the Troubleshooting section or create an issue on GitHub.*
