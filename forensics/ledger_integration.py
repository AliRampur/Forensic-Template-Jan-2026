"""
Django Ledger Integration Bridge

This module provides integration between django-ledger's accounting system
and TraceFlow's forensic reconciliation features.

django-ledger provides:
- Double-entry bookkeeping
- Journal entries
- Chart of accounts
- Financial statements

TraceFlow adds:
- Bank statement import
- Forensic reconciliation
- Evidence tracking
- Verification workflows
"""
from django.db import models
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import date

# This will work once django-ledger migrations are run
try:
    from django_ledger.models import EntityModel, LedgerModel, JournalEntryModel
    DJANGO_LEDGER_AVAILABLE = True
except ImportError:
    DJANGO_LEDGER_AVAILABLE = False

from forensics.models import Account, Transaction, ReconciliationMatch


class LedgerBridge:
    """
    Bridge class to integrate TraceFlow forensics with django-ledger.
    
    This allows using django-ledger for formal accounting while
    maintaining forensic evidence tracking in TraceFlow.
    """
    
    @staticmethod
    def sync_transaction_to_ledger(transaction: Transaction, entity: 'EntityModel', ledger: 'LedgerModel'):
        """
        Sync a TraceFlow transaction to django-ledger as a journal entry.
        
        Args:
            transaction: TraceFlow Transaction object
            entity: django-ledger EntityModel
            ledger: django-ledger LedgerModel
        """
        if not DJANGO_LEDGER_AVAILABLE:
            raise ImportError("django-ledger is not available")
        
        # Create journal entry
        journal_entry = JournalEntryModel.objects.create(
            ledger=ledger,
            description=transaction.description,
            date=transaction.date,
        )
        
        # Add reference to original forensic transaction
        journal_entry.notes = f"Forensic Transaction ID: {transaction.id}, Source: {transaction.source_file}"
        journal_entry.save()
        
        return journal_entry
    
    @staticmethod
    def import_ledger_to_forensics(ledger: 'LedgerModel', account: Account):
        """
        Import django-ledger entries into TraceFlow forensics for reconciliation.
        
        Args:
            ledger: django-ledger LedgerModel
            account: TraceFlow Account to import into
        """
        if not DJANGO_LEDGER_AVAILABLE:
            raise ImportError("django-ledger is not available")
        
        transactions_created = 0
        
        for journal_entry in ledger.journal_entries.all():
            # Create TraceFlow transaction for forensic tracking
            Transaction.objects.create(
                account=account,
                date=journal_entry.date,
                amount=journal_entry.amount if hasattr(journal_entry, 'amount') else 0,
                description=journal_entry.description,
                source_file=f"Ledger: {ledger.name}"
            )
            transactions_created += 1
        
        return transactions_created
    
    @staticmethod
    def create_forensic_account_from_ledger_account(ledger_account, is_internal: bool = True):
        """
        Create a TraceFlow forensic account from a django-ledger account.
        
        Args:
            ledger_account: django-ledger AccountModel
            is_internal: Whether this is an internal book account
        
        Returns:
            TraceFlow Account object
        """
        account = Account.objects.create(
            name=ledger_account.name if hasattr(ledger_account, 'name') else str(ledger_account),
            account_number=ledger_account.code if hasattr(ledger_account, 'code') else 'N/A',
            is_internal_book=is_internal
        )
        return account


class ForensicLedgerMixin(models.Model):
    """
    Mixin to add forensic tracking to django-ledger models.
    
    Add this to your custom ledger models to enable forensic features.
    """
    forensic_verified = models.BooleanField(default=False)
    forensic_verification_date = models.DateTimeField(null=True, blank=True)
    forensic_confidence_score = models.FloatField(default=0.0)
    forensic_source_file = models.CharField(max_length=255, blank=True)
    forensic_notes = models.TextField(blank=True)
    
    class Meta:
        abstract = True


def get_ledger_integration_status() -> Dict:
    """
    Check the status of django-ledger integration.
    
    Returns:
        Dictionary with integration status information
    """
    return {
        'django_ledger_installed': DJANGO_LEDGER_AVAILABLE,
        'forensics_accounts': Account.objects.count(),
        'forensics_transactions': Transaction.objects.count(),
        'reconciliation_matches': ReconciliationMatch.objects.count(),
    }


def reconcile_ledger_with_bank_statements(
    ledger_account_id: int,
    bank_account_id: int
) -> Dict:
    """
    High-level function to reconcile django-ledger accounts with bank statements.
    
    Args:
        ledger_account_id: TraceFlow Account ID for ledger (book) transactions
        bank_account_id: TraceFlow Account ID for bank transactions
    
    Returns:
        Dictionary with reconciliation results
    """
    from forensics.reconciliation import run_auto_verification
    
    result = run_auto_verification(bank_account_id, ledger_account_id)
    
    return {
        'status': 'completed',
        'ledger_account_id': ledger_account_id,
        'bank_account_id': bank_account_id,
        'matches_found': result.get('matches_created', 0),
        'match_rate': result.get('match_rate', 0),
    }
