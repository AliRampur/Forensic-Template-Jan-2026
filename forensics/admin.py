from django.contrib import admin
from .inventory_models import Property, InventoryUnit, Commission


# Inventory Admin
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'short_name', 'base_property', 'unit_count')
    search_fields = ('full_name', 'short_name', 'base_property')
    
    def unit_count(self, obj):
        return obj.units.count()
    unit_count.short_description = 'Units'


@admin.register(InventoryUnit)
class InventoryUnitAdmin(admin.ModelAdmin):
    list_display = (
        'property_unit',
        'property',
        'unit_number',
        'current_lhs_property',
        'is_lhs_rental',
        'bank_gl_balance',
        'current_occupant',
        'has_commissions'
    )
    list_filter = (
        'property',
        'current_lhs_property',
        'is_lhs_rental',
        'has_commissions',
        'mco_owner_matches',
        'commission_but_no_sale'
    )
    search_fields = (
        'unit_number',
        'property_unit',
        'current_occupant',
        'serial_number',
        'observations'
    )
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Unit Identification', {
            'fields': ('unit_number', 'property', 'property_unit', 'base_unit')
        }),
        ('Status', {
            'fields': ('current_lhs_property', 'is_lhs_rental', 'is_rental_listed')
        }),
        ('Financial Data', {
            'fields': (
                'bank_gl_balance',
                'sale_amount_pre_tax',
                'sale_deposited_to',
                'total_sale_price',
            )
        }),
        ('Rental Information', {
            'fields': (
                'gl_rental_income',
                'gl_unearned_rent',
                'gl_rental_deposits',
                'market_rental',
                'current_occupant',
                'address'
            )
        }),
        ('MCO Data', {
            'fields': (
                'mco_owner_matches',
                'mco_owner',
                'mco_date_ref',
                'duplicate_mco',
                'mco_lot_mismatch'
            )
        }),
        ('Builder/Invoice', {
            'fields': (
                'builder_invoice_amount',
                'serial_number',
                'builder_invoice_date',
                'builder_ship_date',
                'bill_to',
                'builder'
            )
        }),
        ('Commissions & Flags', {
            'fields': (
                'has_commissions',
                'mco_not_match',
                'mco_indicates_home_sale_entity',
                'commission_but_no_sale',
                'no_mco_available'
            )
        }),
        ('Observations', {
            'fields': ('observations', 'cavco_champion_total')
        }),
        ('Metadata', {
            'fields': ('source_file', 'created_at', 'updated_at')
        }),
    )


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = (
        'unit',
        'recipient',
        'amount',
        'percentage_of_sales',
        'status',
        'created_at'
    )
    list_filter = ('status', 'recipient', 'unit__property')
    search_fields = ('unit__property_unit', 'recipient', 'memo', 'comments')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Commission Details', {
            'fields': ('unit', 'amount', 'recipient', 'percentage_of_sales')
        }),
        ('Documentation', {
            'fields': ('status', 'memo', 'comments')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )

