"""
Django management command to generate fake forensic accounting data.

Usage:
    python manage.py generate_fake_data --accounts 5 --transactions 100
"""
from django.core.management.base import BaseCommand
from faker import Faker
from decimal import Decimal
import random
from datetime import timedelta

from forensics.models import Account, Transaction, ReconciliationMatch


class Command(BaseCommand):
    help = 'Generate fake data for testing TraceFlow application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--accounts',
            type=int,
            default=5,
            help='Number of accounts to create (default: 5)'
        )
        parser.add_argument(
            '--transactions',
            type=int,
            default=100,
            help='Number of transactions per account (default: 100)'
        )
        parser.add_argument(
            '--match-rate',
            type=float,
            default=0.7,
            help='Percentage of transactions to auto-match (default: 0.7)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data'
        )

    def handle(self, *args, **options):
        fake = Faker()
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            ReconciliationMatch.objects.all().delete()
            Transaction.objects.all().delete()
            Account.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Data cleared!'))

        num_accounts = options['accounts']
        num_transactions = options['transactions']
        match_rate = options['match_rate']

        self.stdout.write(self.style.SUCCESS(f'Generating {num_accounts} accounts...'))

        # Create bank accounts (external)
        bank_accounts = []
        for i in range(num_accounts // 2 + 1):
            account = Account.objects.create(
                name=f"{fake.company()} Bank Account",
                account_number=fake.bban(),
                is_internal_book=False
            )
            bank_accounts.append(account)
            self.stdout.write(f'  Created bank account: {account.name}')

        # Create book accounts (internal GL)
        book_accounts = []
        categories = ['Operating Account', 'Revenue Account', 'Expense Account', 'Asset Account']
        for i in range(num_accounts // 2):
            account = Account.objects.create(
                name=f"{fake.company()} {random.choice(categories)}",
                account_number=f"GL-{fake.random_number(digits=6)}",
                is_internal_book=True
            )
            book_accounts.append(account)
            self.stdout.write(f'  Created book account: {account.name}')

        self.stdout.write(self.style.SUCCESS(f'\nGenerating {num_transactions} transactions per account...'))

        # Transaction types
        vendors = [fake.company() for _ in range(20)]
        
        # Create bank transactions
        bank_transactions = []
        for account in bank_accounts:
            for i in range(num_transactions):
                transaction_date = fake.date_between(start_date='-6m', end_date='today')
                amount = Decimal(str(round(random.uniform(-5000, 5000), 2)))
                
                if amount > 0:
                    description = f"Deposit from {random.choice(vendors)}"
                else:
                    description = f"Payment to {random.choice(vendors)}"
                
                transaction = Transaction.objects.create(
                    account=account,
                    date=transaction_date,
                    amount=amount,
                    description=description,
                    source_file=f"Bank_Statement_{fake.date(pattern='%Y_%m')}.pdf"
                )
                bank_transactions.append(transaction)
        
        self.stdout.write(f'  Created {len(bank_transactions)} bank transactions')

        # Create book transactions
        book_transactions = []
        for account in book_accounts:
            for i in range(num_transactions):
                transaction_date = fake.date_between(start_date='-6m', end_date='today')
                amount = Decimal(str(round(random.uniform(-5000, 5000), 2)))
                
                if amount > 0:
                    description = f"Revenue - {random.choice(vendors)}"
                else:
                    description = f"Expense - {random.choice(vendors)}"
                
                transaction = Transaction.objects.create(
                    account=account,
                    date=transaction_date,
                    amount=amount,
                    description=description,
                    source_file=f"General_Ledger_{fake.date(pattern='%Y_%m')}.xlsx"
                )
                book_transactions.append(transaction)
        
        self.stdout.write(f'  Created {len(book_transactions)} book transactions')

        # Create reconciliation matches
        self.stdout.write(self.style.SUCCESS(f'\nCreating reconciliation matches...'))
        
        matches_to_create = int(len(bank_transactions) * match_rate)
        matched_book_indices = set()
        matches_created = 0
        
        for i, bank_tx in enumerate(random.sample(bank_transactions, matches_to_create)):
            # Find a suitable book transaction to match
            available_book_txs = [
                (idx, tx) for idx, tx in enumerate(book_transactions)
                if idx not in matched_book_indices
                and abs(tx.amount - bank_tx.amount) < Decimal('0.01')
            ]
            
            if not available_book_txs:
                # Create a matching book transaction
                matching_amount = bank_tx.amount
                matching_date = bank_tx.date - timedelta(days=random.randint(0, 3))
                
                book_tx = Transaction.objects.create(
                    account=random.choice(book_accounts),
                    date=matching_date,
                    amount=matching_amount,
                    description=bank_tx.description.replace('Deposit from', 'Revenue -').replace('Payment to', 'Expense -'),
                    source_file=f"General_Ledger_{fake.date(pattern='%Y_%m')}.xlsx"
                )
                book_transactions.append(book_tx)
                available_book_txs = [(len(book_transactions) - 1, book_tx)]
            
            idx, book_tx = random.choice(available_book_txs)
            matched_book_indices.add(idx)
            
            # Determine match type based on date difference
            date_diff = abs((bank_tx.date - book_tx.date).days)
            if date_diff == 0:
                match_type = 'EXACT'
                confidence = 1.0
            elif date_diff <= 3:
                match_type = 'FUZZY_DATE'
                confidence = 0.95
            else:
                match_type = 'MANUAL'
                confidence = 0.85
            
            ReconciliationMatch.objects.create(
                bank_transaction=bank_tx,
                book_entry=book_tx,
                match_type=match_type,
                confidence_score=confidence
            )
            matches_created += 1
        
        self.stdout.write(f'  Created {matches_created} reconciliation matches')

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Data generation complete!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Bank Accounts: {len(bank_accounts)}')
        self.stdout.write(f'Book Accounts: {len(book_accounts)}')
        self.stdout.write(f'Bank Transactions: {len(bank_transactions)}')
        self.stdout.write(f'Book Transactions: {len(book_transactions)}')
        self.stdout.write(f'Reconciliation Matches: {matches_created}')
        self.stdout.write(f'Match Rate: {(matches_created/len(bank_transactions)*100):.1f}%')
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('\nYou can now view the data at:'))
        self.stdout.write('  Admin: http://127.0.0.1:8000/admin/')
        self.stdout.write('  Dashboard: http://127.0.0.1:8000/')
        self.stdout.write('  Sankey: http://127.0.0.1:8000/sankey/')
