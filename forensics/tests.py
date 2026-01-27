"""
Tests for Forensics App
"""
from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta

from .models import Account, Transaction, ReconciliationMatch
from .reconciliation import run_auto_verification, get_unmatched_transactions


class AccountModelTest(TestCase):
    """Test Account model."""
    
    def test_account_creation(self):
        account = Account.objects.create(
            name="Test Bank Account",
            account_number="123456789",
            is_internal_book=False
        )
        self.assertEqual(account.name, "Test Bank Account")
        self.assertFalse(account.is_internal_book)
        self.assertEqual(str(account), "Test Bank Account (123456789)")


class TransactionModelTest(TestCase):
    """Test Transaction model."""
    
    def setUp(self):
        self.account = Account.objects.create(
            name="Test Account",
            account_number="123456",
            is_internal_book=False
        )
    
    def test_transaction_creation(self):
        transaction = Transaction.objects.create(
            account=self.account,
            date=date(2026, 1, 15),
            amount=Decimal("1000.00"),
            description="Test transaction",
            source_file="test.pdf"
        )
        self.assertEqual(transaction.amount, Decimal("1000.00"))
        self.assertEqual(transaction.account, self.account)
        self.assertTrue(transaction.is_bank_transaction)
        self.assertFalse(transaction.is_book_entry)


class ReconciliationMatchModelTest(TestCase):
    """Test ReconciliationMatch model."""
    
    def setUp(self):
        self.bank_account = Account.objects.create(
            name="Bank Account",
            account_number="BANK001",
            is_internal_book=False
        )
        self.book_account = Account.objects.create(
            name="Book Account",
            account_number="BOOK001",
            is_internal_book=True
        )
        self.bank_tx = Transaction.objects.create(
            account=self.bank_account,
            date=date(2026, 1, 15),
            amount=Decimal("500.00"),
            description="Payment from Customer",
            source_file="bank_statement.pdf"
        )
        self.book_tx = Transaction.objects.create(
            account=self.book_account,
            date=date(2026, 1, 14),
            amount=Decimal("500.00"),
            description="Customer Payment",
            source_file="general_ledger.xlsx"
        )
    
    def test_match_creation(self):
        match = ReconciliationMatch.objects.create(
            bank_transaction=self.bank_tx,
            book_entry=self.book_tx,
            match_type='EXACT',
            confidence_score=1.0
        )
        self.assertEqual(match.match_type, 'EXACT')
        self.assertEqual(match.confidence_score, 1.0)


class ReconciliationEngineTest(TestCase):
    """Test reconciliation engine functions."""
    
    def setUp(self):
        self.bank_account = Account.objects.create(
            name="Bank Account",
            account_number="BANK001",
            is_internal_book=False
        )
        self.book_account = Account.objects.create(
            name="Book Account",
            account_number="BOOK001",
            is_internal_book=True
        )
    
    def test_auto_verification(self):
        # Create matching transactions
        Transaction.objects.create(
            account=self.bank_account,
            date=date(2026, 1, 15),
            amount=Decimal("500.00"),
            description="Payment",
            source_file="bank.pdf"
        )
        Transaction.objects.create(
            account=self.book_account,
            date=date(2026, 1, 15),
            amount=Decimal("500.00"),
            description="Payment",
            source_file="book.xlsx"
        )
        
        result = run_auto_verification(self.bank_account.id, self.book_account.id)
        self.assertEqual(result['matches_created'], 1)
        self.assertEqual(ReconciliationMatch.objects.count(), 1)


class ViewsTest(TestCase):
    """Test views."""
    
    def setUp(self):
        self.client = Client()
    
    def test_home_view(self):
        response = self.client.get(reverse('forensics:home'))
        self.assertEqual(response.status_code, 200)
    
    def test_sankey_view(self):
        response = self.client.get(reverse('forensics:sankey'))
        self.assertEqual(response.status_code, 200)
