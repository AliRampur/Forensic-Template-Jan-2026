"""
Inventory Models for LHS Forensic Analysis

These models track manufactured home inventory across multiple properties
including sales, rentals, commissions, and MCO (Manufacturer's Certificate of Origin) data.
"""
from django.db import models
from decimal import Decimal


class Property(models.Model):
    """Represents a property/park where units are located."""
    full_name = models.CharField(max_length=255, help_text="Full Property/Park Name")
    short_name = models.CharField(max_length=50, help_text="Property acronym (e.g., GCRV, PEM)")
    base_property = models.CharField(max_length=50, help_text="Base Property code (GC, PEM, SPR, SR)")
    
    class Meta:
        ordering = ['full_name']
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
    
    def __str__(self):
        return f"{self.full_name} ({self.short_name})"


class InventoryUnit(models.Model):
    """
    Represents a manufactured home unit in the LHS inventory system.
    Tracks ownership, sales, rentals, and forensic evidence.
    """
    # Unit Identification
    unit_number = models.CharField(max_length=50, help_text="Unit/Lot number")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='units')
    property_unit = models.CharField(
        max_length=100,
        unique=True,
        help_text="Property_Unit (unique ID)"
    )
    base_unit = models.CharField(
        max_length=100,
        help_text="Base Property and Unit # combination"
    )
    
    # Ownership & Status
    current_lhs_property = models.BooleanField(
        default=False,
        help_text="Currently owned by LHS or sold by LHS"
    )
    is_lhs_rental = models.BooleanField(
        default=False,
        help_text="LHS Rental unit"
    )
    is_rental_listed = models.BooleanField(
        default=False,
        help_text="Listed in Rental List"
    )
    
    # Financial Data
    bank_gl_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total Bank GL Balance (Per Unit BS Report)"
    )
    sale_amount_pre_tax = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Sale Amount (pre-tax)"
    )
    sale_deposited_to = models.CharField(
        max_length=255,
        blank=True,
        help_text="Account where sale was deposited"
    )
    total_sale_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total Sale Price per PEM Sales Contract"
    )
    
    # Rental Information
    gl_rental_income = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="GL Rental Income (Credits)"
    )
    gl_unearned_rent = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="GL - Credits to Unearned Rent/Prepaid"
    )
    gl_rental_deposits = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="GL Rental Deposits"
    )
    market_rental = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Market Rental Rate"
    )
    current_occupant = models.CharField(
        max_length=255,
        blank=True,
        help_text="Current Occupant name"
    )
    address = models.CharField(max_length=500, blank=True, help_text="Unit address")
    
    # MCO (Manufacturer's Certificate of Origin) Data
    mco_owner_matches = models.BooleanField(
        null=True,
        blank=True,
        help_text="MCO Owner Matches Property Name?"
    )
    mco_owner = models.CharField(
        max_length=255,
        blank=True,
        help_text="MCO - Owner name"
    )
    mco_date_ref = models.CharField(
        max_length=255,
        blank=True,
        help_text="MCO Date and Invoice Reference"
    )
    duplicate_mco = models.BooleanField(
        default=False,
        help_text="Duplicate MCO (2nd version exists)"
    )
    mco_lot_mismatch = models.BooleanField(
        default=False,
        help_text="Lot/Unit on invoice does not match"
    )
    
    # Builder/Invoice Information
    builder_invoice_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Builder Invoice Amount"
    )
    serial_number = models.CharField(max_length=100, blank=True, help_text="Unit Serial Number")
    builder_invoice_date = models.DateField(
        null=True,
        blank=True,
        help_text="Builder Invoice Date"
    )
    builder_ship_date = models.DateField(
        null=True,
        blank=True,
        help_text="Builder Ship Date"
    )
    bill_to = models.CharField(max_length=255, blank=True, help_text="Bill To party")
    builder = models.CharField(max_length=255, blank=True, help_text="Builder name")
    
    # Commissions
    has_commissions = models.BooleanField(
        default=False,
        help_text="Has recorded commissions"
    )
    
    # Observations & Flags
    observations = models.TextField(
        blank=True,
        help_text="Forensic observations and notes"
    )
    cavco_champion_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cavco/Champion/CMH total"
    )
    
    # Evidence Flags
    mco_not_match = models.BooleanField(default=False, help_text="MCO does not match")
    mco_indicates_home_sale_entity = models.BooleanField(
        default=False,
        help_text="MCO indicates Home Sale Entity as Owner"
    )
    commission_but_no_sale = models.BooleanField(
        default=False,
        help_text="Commission recorded but no sale identified"
    )
    no_mco_available = models.BooleanField(
        default=False,
        help_text="No MCO available"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source_file = models.CharField(
        max_length=255,
        help_text="Source CSV filename"
    )
    
    class Meta:
        ordering = ['property', 'unit_number']
        verbose_name = 'Inventory Unit'
        verbose_name_plural = 'Inventory Units'
        indexes = [
            models.Index(fields=['property', 'unit_number']),
            models.Index(fields=['property_unit']),
            models.Index(fields=['current_lhs_property']),
        ]
    
    def __str__(self):
        return f"{self.property_unit} - {self.current_occupant or 'Vacant'}"


class Commission(models.Model):
    """Tracks commission payments related to unit sales."""
    unit = models.ForeignKey(
        InventoryUnit,
        on_delete=models.CASCADE,
        related_name='commissions'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Commission amount"
    )
    recipient = models.CharField(
        max_length=255,
        help_text="Commission recipient (e.g., SBR, Ernesto)"
    )
    memo = models.TextField(blank=True, help_text="Memo / Invoice Number")
    status = models.CharField(
        max_length=50,
        choices=[
            ('SUPPORTED', 'Supported'),
            ('UNSUPPORTED', 'Unsupported'),
            ('INSUFFICIENT', 'Insufficient Evidence'),
        ],
        default='SUPPORTED'
    )
    comments = models.TextField(blank=True, help_text="Additional comments")
    percentage_of_sales = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="% of Sales Price"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-amount']
        verbose_name = 'Commission'
        verbose_name_plural = 'Commissions'
    
    def __str__(self):
        return f"{self.unit.property_unit} - {self.recipient}: ${self.amount}"


class Document(models.Model):
    """Tracks documents for forensic analysis (taxes, bank statements, invoices, etc.)."""
    
    DOC_TYPE_CHOICES = [
        ('TAX', 'Tax Return'),
        ('BANK', 'Bank Statement'),
        ('INVOICE', 'Invoice'),
    ]
    
    # Basic Info
    document_type = models.CharField(
        max_length=50,
        choices=DOC_TYPE_CHOICES,
        help_text="Type of document"
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True,
        help_text="Related property"
    )
    
    # Document Details
    title = models.CharField(max_length=255, help_text="Document title")
    description = models.TextField(blank=True, help_text="Document description")
    
    # Tax-specific fields
    tax_year = models.IntegerField(
        null=True,
        blank=True,
        help_text="Tax year (for tax documents)"
    )
    tax_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type of tax return (e.g., 1040, 1120, K-1)"
    )
    
    # Bank Statement-specific fields
    statement_year = models.IntegerField(
        null=True,
        blank=True,
        help_text="Year (for bank statements)"
    )
    statement_month = models.IntegerField(
        null=True,
        blank=True,
        choices=[(i, f"{i:02d}") for i in range(1, 13)],
        help_text="Month (1-12)"
    )
    bank_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Bank name"
    )
    account_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Bank account number (partially masked)"
    )
    
    # Invoice-specific fields
    invoice_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Invoice number"
    )
    vendor_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Vendor/Supplier name"
    )
    invoice_date = models.DateField(
        null=True,
        blank=True,
        help_text="Invoice date"
    )
    invoice_year = models.IntegerField(
        null=True,
        blank=True,
        help_text="Year (for filtering)"
    )
    
    # Document Storage
    file_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original file name"
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to document file"
    )
    file_size_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="File size in MB"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.CharField(
        max_length=255,
        blank=True,
        help_text="User who uploaded the document"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        indexes = [
            models.Index(fields=['document_type', 'property']),
            models.Index(fields=['tax_year']),
            models.Index(fields=['statement_year', 'statement_month']),
        ]
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.title}"
