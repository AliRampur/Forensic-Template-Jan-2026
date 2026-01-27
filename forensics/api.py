"""
Django Ninja API for TraceFlow Forensic Accounting

Provides RESTful API endpoints for:
- Accounts management
- Transactions
- Reconciliation matches
- Statistics and analytics
"""
from ninja import NinjaAPI, Schema
from typing import List, Optional
from datetime import date
from decimal import Decimal

from forensics.models import Account, Transaction, ReconciliationMatch
from forensics.reconciliation import (
    run_auto_verification,
    get_unmatched_transactions,
    calculate_reconciliation_summary
)

api = NinjaAPI(
    title="TraceFlow Forensic Accounting API",
    version="1.0.0",
    description="API for forensic accounting and transaction reconciliation"
)


# Schemas
class AccountSchema(Schema):
    id: int
    name: str
    account_number: str
    is_internal_book: bool
    
    @staticmethod
    def resolve_transaction_count(obj):
        return obj.transactions.count()


class AccountCreateSchema(Schema):
    name: str
    account_number: str
    is_internal_book: bool = False


class TransactionSchema(Schema):
    id: int
    account_id: int
    account_name: str
    date: date
    amount: float
    description: str
    source_file: str
    is_bank_transaction: bool
    is_book_entry: bool
    
    @staticmethod
    def resolve_account_name(obj):
        return obj.account.name


class TransactionCreateSchema(Schema):
    account_id: int
    date: date
    amount: float
    description: str
    source_file: str


class ReconciliationMatchSchema(Schema):
    id: int
    bank_transaction_id: int
    book_entry_id: Optional[int]
    match_type: str
    confidence_score: float
    notes: str
    created_at: str
    
    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat()


class ReconciliationStatsSchema(Schema):
    total_transactions: int
    matched: int
    unmatched: int
    match_rate_percent: float


class ReconciliationRunSchema(Schema):
    bank_account_id: int
    book_account_id: int


class ReconciliationResultSchema(Schema):
    matches_created: int
    bank_transactions: int
    book_transactions: int
    match_rate: float
    message: Optional[str] = None


# Account Endpoints
@api.get("/accounts", response=List[AccountSchema], tags=["Accounts"])
def list_accounts(request, is_internal_book: Optional[bool] = None):
    """List all accounts with optional filtering."""
    accounts = Account.objects.all()
    if is_internal_book is not None:
        accounts = accounts.filter(is_internal_book=is_internal_book)
    return accounts


@api.get("/accounts/{account_id}", response=AccountSchema, tags=["Accounts"])
def get_account(request, account_id: int):
    """Get a specific account by ID."""
    return Account.objects.get(id=account_id)


@api.post("/accounts", response=AccountSchema, tags=["Accounts"])
def create_account(request, payload: AccountCreateSchema):
    """Create a new account."""
    account = Account.objects.create(**payload.dict())
    return account


@api.delete("/accounts/{account_id}", tags=["Accounts"])
def delete_account(request, account_id: int):
    """Delete an account."""
    account = Account.objects.get(id=account_id)
    account.delete()
    return {"success": True}


# Transaction Endpoints
@api.get("/transactions", response=List[TransactionSchema], tags=["Transactions"])
def list_transactions(
    request,
    account_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100
):
    """List transactions with optional filtering."""
    transactions = Transaction.objects.select_related('account').all()
    
    if account_id:
        transactions = transactions.filter(account_id=account_id)
    if start_date:
        transactions = transactions.filter(date__gte=start_date)
    if end_date:
        transactions = transactions.filter(date__lte=end_date)
    
    return transactions[:limit]


@api.get("/transactions/{transaction_id}", response=TransactionSchema, tags=["Transactions"])
def get_transaction(request, transaction_id: int):
    """Get a specific transaction by ID."""
    return Transaction.objects.select_related('account').get(id=transaction_id)


@api.post("/transactions", response=TransactionSchema, tags=["Transactions"])
def create_transaction(request, payload: TransactionCreateSchema):
    """Create a new transaction."""
    transaction = Transaction.objects.create(**payload.dict())
    return transaction


# Reconciliation Endpoints
@api.get("/reconciliation/matches", response=List[ReconciliationMatchSchema], tags=["Reconciliation"])
def list_matches(request, match_type: Optional[str] = None, limit: int = 100):
    """List reconciliation matches."""
    matches = ReconciliationMatch.objects.select_related(
        'bank_transaction',
        'book_entry'
    ).all()
    
    if match_type:
        matches = matches.filter(match_type=match_type)
    
    return matches[:limit]


@api.get("/reconciliation/stats", response=ReconciliationStatsSchema, tags=["Reconciliation"])
def get_reconciliation_stats(request, account_id: Optional[int] = None):
    """Get reconciliation statistics."""
    stats = calculate_reconciliation_summary(account_id)
    return stats


@api.post("/reconciliation/run", response=ReconciliationResultSchema, tags=["Reconciliation"])
def run_reconciliation(request, payload: ReconciliationRunSchema):
    """Run automated reconciliation between bank and book accounts."""
    result = run_auto_verification(
        payload.bank_account_id,
        payload.book_account_id
    )
    return result


@api.get("/reconciliation/unmatched/{account_id}", response=List[TransactionSchema], tags=["Reconciliation"])
def get_unmatched(request, account_id: int, is_bank: bool = True):
    """Get unmatched transactions for an account."""
    transactions = get_unmatched_transactions(account_id, is_bank)
    return transactions


# Dashboard/Stats Endpoints
@api.get("/stats/summary", tags=["Statistics"])
def get_summary_stats(request):
    """Get overall system statistics."""
    return {
        'total_accounts': Account.objects.count(),
        'total_transactions': Transaction.objects.count(),
        'total_matches': ReconciliationMatch.objects.count(),
        'bank_accounts': Account.objects.filter(is_internal_book=False).count(),
        'book_accounts': Account.objects.filter(is_internal_book=True).count(),
    }


@api.get("/stats/accounts/{account_id}", tags=["Statistics"])
def get_account_stats(request, account_id: int):
    """Get statistics for a specific account."""
    account = Account.objects.get(id=account_id)
    transactions = account.transactions.all()
    
    total_inflow = sum(t.amount for t in transactions if t.amount > 0)
    total_outflow = sum(t.amount for t in transactions if t.amount < 0)
    
    return {
        'account_id': account_id,
        'account_name': account.name,
        'transaction_count': transactions.count(),
        'total_inflow': float(total_inflow),
        'total_outflow': float(total_outflow),
        'net_balance': float(total_inflow + total_outflow),
    }
