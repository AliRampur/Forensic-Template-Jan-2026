# TraceFlow - Forensic Accounting System

A Django-based forensic accounting application for bank reconciliation and financial transaction verification.

## Features

- **Dual-Side Evidence Storage**: Separates bank statements (Truth 1) from general ledger entries (Truth 2)
- **Automated Reconciliation Engine**: Matches transactions using exact, fuzzy date, and description matching algorithms
- **Courtroom-Ready Visualizations**: Sankey diagrams with Plotly to trace money flows
- **Forensic Trail**: Maintains complete audit trail with source file tracking and confidence scores
- **Unified Architecture**: Single cohesive Django app for better maintainability

## Project Structure

```
TraceFlow - Forensic Accounting/
├── forensics/              # Main Django app (unified)
│   ├── models.py          # Database models (Account, Transaction, ReconciliationMatch)
│   ├── views.py           # All views (dashboard, Sankey, lists)
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin interface configuration
│   ├── reconciliation.py  # Verification engine logic
│   ├── tests.py           # Comprehensive test suite
│   ├── management/        # Custom management commands
│   │   └── commands/
│   │       └── generate_fake_data.py
│   └── templates/         # HTML templates
│       └── forensics/
│           ├── base.html
│           ├── dashboard.html
│           └── sankey.html
├── traceflow/             # Django project configuration
├── manage.py
├── requirements.txt
└── Dockerfile
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL database
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "TraceFlow - Forensic Accounting"
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Set up environment variables:
Create a `.env` file with:
```
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

6. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

7. Create a superuser:
```bash
python manage.py createsuperuser
```

8. Run the development server:
```bash
python manage.py runserver
```

9. Access the application:
- Dashboard: http://localhost:8000/
- Admin interface: http://localhost:8000/admin/
- Sankey visualization: http://localhost:8000/sankey/
- Accounts: http://localhost:8000/accounts/
- Transactions: http://localhost:8000/transactions/
- Matches: http://localhost:8000/matches/

## Key Models

### Account
Represents bank accounts or general ledger accounts with differentiation between internal books and external bank statements.

### Transaction
Individual transaction entries from either bank statements or general ledger, including forensic metadata like source file tracking.

### ReconciliationMatch
Links bank transactions to book entries with match type (exact, fuzzy date, manual) and confidence scores.

## Reconciliation Algorithm

The verification engine uses:
1. **Exact Match**: Same amount + same date
2. **Date Slippage Match**: Same amount + bank date within 1-5 days of book date (accounts for check clearing delays)
3. **Description Fuzzy Match**: Levenshtein distance for matching similar descriptions

## Docker Deployment

Build and run with Docker:
```bash
docker build -t traceflow .
docker run -p 8000:8000 -e PORT=8000 traceflow
```

## Testing

Run tests:
```bash
python manage.py test
```

## License

[Specify your license]

## Contributing

[Specify contribution guidelines]
