"""
Database Models for Forensic Accounting System

The core difference between a standard ledger and a forensic tool is the separation 
of evidence. You do not just store a "transaction"; you store the Bank Side (Truth 1) 
and the Book Side (Truth 2) and then link them.

Integration with django-ledger:
- django-ledger provides formal double-entry bookkeeping
- TraceFlow provides forensic evidence tracking and reconciliation
- Use ledger_integration.py to bridge the two systems
"""
from django.db import models


class Account(models.Model):
    """Represents a bank account or general ledger account."""
    name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=100)
    is_internal_book = models.BooleanField(
        default=False,
        help_text="True = General Ledger, False = Bank Statement"
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
    
    def __str__(self):
        return f"{self.name} ({self.account_number})"


class Transaction(models.Model):
    """
    Represents a single line item from a Bank Statement OR a General Ledger.
    Each transaction is evidence from either external (bank) or internal (books) sources.
    """
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Negative for outflow, positive for inflow"
    )
    description = models.TextField()
    
    # Metadata for forensic trail
    source_file = models.CharField(
        max_length=255,
        help_text="e.g., 'Chase_Dec_2023.pdf' or 'GL_2023.xlsx'"
    )
    
    # Optional: Link to django-ledger journal entry for formal accounting
    ledger_journal_entry_uuid = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID of linked django-ledger JournalEntryModel"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['date', 'amount']),
            models.Index(fields=['account', 'date']),
        ]
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
    
    def __str__(self):
        return f"{self.date} - {self.description[:50]} (${self.amount})"
    
    @property
    def is_bank_transaction(self):
        """Returns True if this is a bank transaction (external evidence)."""
        return not self.account.is_internal_book
    
    @property
    def is_book_entry(self):
        """Returns True if this is a book entry (internal evidence)."""
        return self.account.is_internal_book


class ReconciliationMatch(models.Model):
    """
    The 'Verification' Link between bank and book transactions.
    If a transaction is in this table, it has been verified against independent evidence.
    """
    MATCH_TYPE_CHOICES = [
        ('EXACT', 'Exact Match'),
        ('FUZZY_DATE', 'Date Slippage'),
        ('FUZZY_DESCRIPTION', 'Description Match'),
        ('MANUAL', 'Manually Verified')
    ]
    
    bank_transaction = models.ForeignKey(
        Transaction,
        related_name='bank_matches',
        on_delete=models.CASCADE,
        help_text="External evidence from bank statement"
    )
    book_entry = models.ForeignKey(
        Transaction,
        related_name='book_matches',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Internal evidence from general ledger"
    )
    
    match_type = models.CharField(max_length=50, choices=MATCH_TYPE_CHOICES)
    confidence_score = models.FloatField(
        default=1.0,
        help_text="0.0 to 1.0, where 1.0 is absolute certainty"
    )
    notes = models.TextField(blank=True, help_text="Additional verification notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Reconciliation Match'
        verbose_name_plural = 'Reconciliation Matches'
    
    def __str__(self):
        return f"Match: {self.bank_transaction.id} ↔ {self.book_entry.id if self.book_entry else 'None'} ({self.match_type})"
