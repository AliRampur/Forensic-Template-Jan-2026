from django.contrib import admin
from .models import Account, Transaction, ReconciliationMatch


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_number', 'is_internal_book', 'transaction_count')
    list_filter = ('is_internal_book',)
    search_fields = ('name', 'account_number')
    
    def transaction_count(self, obj):
        return obj.transactions.count()
    transaction_count.short_description = 'Transactions'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'account', 'amount', 'description_preview', 'source_file', 'is_matched')
    list_filter = ('date', 'account', 'account__is_internal_book')
    search_fields = ('description', 'source_file', 'account__name')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('account', 'date', 'amount', 'description')
        }),
        ('Forensic Metadata', {
            'fields': ('source_file', 'created_at', 'updated_at')
        }),
    )
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'
    
    def is_matched(self, obj):
        if obj.account.is_internal_book:
            return obj.book_matches.exists()
        else:
            return obj.bank_matches.exists()
    is_matched.boolean = True
    is_matched.short_description = 'Matched'


@admin.register(ReconciliationMatch)
class ReconciliationMatchAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'bank_transaction_preview',
        'book_entry_preview',
        'match_type',
        'confidence_score',
        'created_at'
    )
    list_filter = ('match_type', 'created_at', 'confidence_score')
    search_fields = (
        'bank_transaction__description',
        'book_entry__description',
        'notes'
    )
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Match Details', {
            'fields': ('bank_transaction', 'book_entry', 'match_type', 'confidence_score')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    def bank_transaction_preview(self, obj):
        return f"{obj.bank_transaction.date} - ${obj.bank_transaction.amount}"
    bank_transaction_preview.short_description = 'Bank Transaction'
    
    def book_entry_preview(self, obj):
        if obj.book_entry:
            return f"{obj.book_entry.date} - ${obj.book_entry.amount}"
        return "No book entry"
    book_entry_preview.short_description = 'Book Entry'
