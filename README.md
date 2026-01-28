# TraceFlow - Forensic Accounting System

> **Complete Documentation:** See [DOCUMENTATION.md](DOCUMENTATION.md) for the full guide with collapsible sections.

## Quick Links

- 🌐 **Production**: https://traceflow-502947376621.us-central1.run.app
- 📚 **GitHub**: https://github.com/AliRampur/Forensic-Template-Jan-2026
- 💾 **Database**: Cloud SQL PostgreSQL (35.188.121.201)
- 📊 **Data**: 4,295 inventory units, 179 commissions

## Features

- **Property Inventory Management**: Track 4,295+ units across 5 properties
- **Forensic Analysis Dashboard**: Identify MCO mismatches and unsupported commissions
- **Money Flow Visualization**: Sankey diagrams showing property sales → commissions
- **Commission Tracking**: Validate commission records with support status
- **Professional Resume**: Ali Rampurawala's forensic accounting expertise

## Quick Start

```bash
# Local Development
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Visit http://127.0.0.1:8000/

## Key Pages

- `/` - Dashboard with inventory stats
- `/sankey/` - Money flow visualization
- `/inventory/metrics/` - Forensic analysis dashboard
- `/inventory/units/` - Paginated inventory units
- `/inventory/commissions/` - Commission records
- `/resume/` - Ali Rampurawala's resume
- `/admin/` - Admin interface

## Tech Stack

- Django 4.2.27
- PostgreSQL 15 (Cloud SQL)
- Plotly for visualizations
- GCP Cloud Run deployment
- Python 3.11 (Cloud Run), 3.14 (local)

---

**For complete setup instructions, deployment guides, and troubleshooting, see [DOCUMENTATION.md](DOCUMENTATION.md)**
