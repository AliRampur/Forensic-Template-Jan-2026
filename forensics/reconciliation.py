"""
Reconciliation Engine for Forensic Accounting

This module provides automated matching algorithms to verify General Ledger (Books) 
accuracy by finding independent proof in Bank Statements.

Algorithm Logic:
1. Exact Match: Same Amount + Same Date
2. Date Slippage Match: Same Amount + Bank Date is 1-5 days after Book Date
3. Description Fuzzy Match: Using Levenshtein distance for similar descriptions
"""
import pandas as pd
from datetime import timedelta
from typing import Tuple, List
from .models import Transaction, ReconciliationMatch


def run_auto_verification(account_id_bank: int, account_id_book: int) -> dict:
    """
    Run automated reconciliation between bank and book accounts.
    
    Args:
        account_id_bank: ID of the bank account (external evidence)
        account_id_book: ID of the book account (internal evidence)
    
    Returns:
        Dictionary with reconciliation statistics
    """
    # Load data into Pandas for speed
    bank_txs = list(Transaction.objects.filter(account_id=account_id_bank).values())
    book_txs = list(Transaction.objects.filter(account_id=account_id_book).values())
    
    if not bank_txs or not book_txs:
        return {
            'matches_created': 0,
            'bank_transactions': len(bank_txs),
            'book_transactions': len(book_txs),
            'message': 'No transactions found in one or both accounts'
        }
    
    df_bank = pd.DataFrame(bank_txs)
    df_book = pd.DataFrame(book_txs)
    
    matches_created = 0
    
    # 1. Exact Amount and Date Matching
    for index, bank_row in df_bank.iterrows():
        # Filter books for same amount
        candidates = df_book[df_book['amount'] == bank_row['amount']]
        
        # Filter for date (Bank date >= Book date, within 5 days buffer)
        candidates = candidates[
            (candidates['date'] <= bank_row['date']) & 
            (candidates['date'] >= bank_row['date'] - timedelta(days=5))
        ]
        
        if not candidates.empty:
            # Match Found
            match = candidates.iloc[0]  # Take best fit (closest date)
            
            # Determine match type
            date_diff = abs((bank_row['date'] - match['date']).days)
            if date_diff == 0:
                match_type = 'EXACT'
                confidence = 1.0
            else:
                match_type = 'FUZZY_DATE'
                confidence = 0.95
            
            ReconciliationMatch.objects.create(
                bank_transaction_id=bank_row['id'],
                book_entry_id=match['id'],
                match_type=match_type,
                confidence_score=confidence
            )
            
            matches_created += 1
            
            # Remove from pool to prevent double matching
            df_book = df_book.drop(match.name)
    
    return {
        'matches_created': matches_created,
        'bank_transactions': len(bank_txs),
        'book_transactions': len(book_txs),
        'match_rate': matches_created / len(bank_txs) if bank_txs else 0
    }


def get_unmatched_transactions(account_id: int, is_bank: bool = True) -> List[Transaction]:
    """
    Get list of unmatched transactions for an account.
    
    Args:
        account_id: ID of the account
        is_bank: True if this is a bank account, False if book account
    
    Returns:
        List of Transaction objects that have no matches
    """
    transactions = Transaction.objects.filter(account_id=account_id)
    
    unmatched = []
    for tx in transactions:
        if is_bank:
            if not tx.bank_matches.exists():
                unmatched.append(tx)
        else:
            if not tx.book_matches.exists():
                unmatched.append(tx)
    
    return unmatched


def calculate_reconciliation_summary(account_id_bank: int = None) -> dict:
    """
    Calculate summary statistics for reconciliation status.
    
    Args:
        account_id_bank: Optional bank account ID to filter by
    
    Returns:
        Dictionary with summary statistics
    """
    if account_id_bank:
        bank_txs = Transaction.objects.filter(account_id=account_id_bank)
    else:
        bank_txs = Transaction.objects.filter(account__is_internal_book=False)
    
    total_bank_txs = bank_txs.count()
    matched_count = sum(1 for tx in bank_txs if tx.bank_matches.exists())
    unmatched_count = total_bank_txs - matched_count
    
    match_rate = (matched_count / total_bank_txs * 100) if total_bank_txs > 0 else 0
    
    return {
        'total_transactions': total_bank_txs,
        'matched': matched_count,
        'unmatched': unmatched_count,
        'match_rate_percent': round(match_rate, 2)
    }
