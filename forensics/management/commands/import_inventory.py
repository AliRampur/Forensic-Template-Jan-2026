"""
Import LHS Inventory data from CSV files into PostgreSQL.
"""
import pandas as pd
import os
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from forensics.inventory_models import Property, InventoryUnit, Commission


class Command(BaseCommand):
    help = 'Import LHS Inventory detail CSV files into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing inventory data before import'
        )

    def handle(self, *args, **options):
        clear_existing = options['clear']
        
        if clear_existing:
            self.stdout.write(self.style.WARNING('Clearing existing inventory data...'))
            Commission.objects.all().delete()
            InventoryUnit.objects.all().delete()
            Property.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared'))
        
        # Define data directory
        data_dir = os.path.join('forensics', 'data')
        
        # Property mapping
        property_map = {
            'Gold Canyon': {'short': 'GCRV', 'base': 'GC'},
            'Other': {'short': 'OTHER', 'base': 'OTH'},
            'PEM': {'short': 'PEM', 'base': 'PEM'},
            'Springs': {'short': 'SPR', 'base': 'SPR'},
            'Sunrise': {'short': 'SR', 'base': 'SR'},
        }
        
        # CSV files to import
        csv_files = [
            'LHS_Inventory detail_01.07.2026.xlsx - Gold Canyon.csv',
            'LHS_Inventory detail_01.07.2026.xlsx - Other.csv',
            'LHS_Inventory detail_01.07.2026.xlsx - PEM.csv',
            'LHS_Inventory detail_01.07.2026.xlsx - Springs.csv',
            'LHS_Inventory detail_01.07.2026.xlsx - Sunrise.csv',
        ]
        
        total_units = 0
        total_commissions = 0
        
        for csv_file in csv_files:
            file_path = os.path.join(data_dir, csv_file)
            
            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.WARNING(f'File not found: {csv_file}')
                )
                continue
            
            # Extract property name from filename
            property_name = csv_file.split(' - ')[-1].replace('.csv', '')
            
            self.stdout.write(f'\nProcessing {property_name}...')
            
            # Import data for this property
            units_count, commissions_count = self.import_property_data(
                file_path,
                property_name,
                property_map.get(property_name, {})
            )
            
            total_units += units_count
            total_commissions += commissions_count
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'  [OK] {units_count} units, {commissions_count} commissions'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n[SUCCESS] Import complete: {total_units} total units, '
                f'{total_commissions} total commissions'
            )
        )

    @transaction.atomic
    def import_property_data(self, file_path, property_name, property_info):
        """Import data from a single CSV file."""
        
        # Read CSV, skipping header rows (data starts at row 8)
        df = pd.read_csv(file_path, skiprows=8)
        
        # Drop completely empty rows
        df = df.dropna(how='all')
        
        # Get or create Property
        prop, created = Property.objects.get_or_create(
            full_name=property_name,
            defaults={
                'short_name': property_info.get('short', property_name[:10]),
                'base_property': property_info.get('base', property_name[:3].upper())
            }
        )
        
        units_count = 0
        commissions_count = 0
        
        for idx, row in df.iterrows():
            # Skip if no unit number
            if pd.isna(row.get('Unit / Lot')) or str(row.get('Unit / Lot')).strip() == '':
                continue
            
            # Create InventoryUnit
            unit = self.create_unit(row, prop, os.path.basename(file_path))
            
            if unit:
                units_count += 1
                
                # Parse and create commissions
                comm_count = self.create_commissions(row, unit)
                commissions_count += comm_count
        
        return units_count, commissions_count

    def create_unit(self, row, property_obj, source_file):
        """Create an InventoryUnit from a CSV row."""
        
        try:
            unit = InventoryUnit.objects.create(
                # Identification
                unit_number=self.clean_string(row.get('Unit / Lot')),
                property=property_obj,
                property_unit=self.clean_string(row.get('Property_Unit')),
                base_unit=self.clean_string(row.get('Base_unit')),
                
                # Status
                current_lhs_property=self.parse_boolean(
                    row.get('Current LHS Property or Sold by LHS')
                ),
                is_lhs_rental=self.parse_boolean(row.get('LHS Rental')),
                is_rental_listed=self.parse_boolean(row.get('Rental List')),
                
                # Financial
                bank_gl_balance=self.parse_decimal(
                    row.get('Total Bank GL Balance (Per Unit BS Report)')
                ),
                sale_amount_pre_tax=self.parse_decimal(
                    row.get(' Sale Amount (pre-tax) ')
                ),
                sale_deposited_to=self.clean_string(
                    row.get(' Sale Deposited To: ')
                ),
                total_sale_price=self.parse_decimal(
                    row.get('Total Sale Price per PEM Sales Contract')
                ),
                
                # Rental
                gl_rental_income=self.parse_decimal(
                    row.get(' GL Rental Income (Credits to M-Lots, Daily Guest Fees, etc.) ')
                ),
                gl_unearned_rent=self.parse_decimal(
                    row.get(' GL - Credits to Unearned Rent/Prepaid) ')
                ),
                gl_rental_deposits=self.parse_decimal(
                    row.get(' GL Rental Deposits (Deposit to cash accounts) ')
                ),
                market_rental=self.parse_decimal(row.get('Market Rental')),
                current_occupant=self.clean_string(row.get('Current Occupant')),
                address=self.clean_string(row.get('Address')),
                
                # MCO
                mco_owner_matches=self.parse_boolean(
                    row.get('MCO Owner Matches Property Name?')
                ),
                mco_owner=self.clean_string(row.get('MCO - Owner')),
                mco_date_ref=self.clean_string(
                    row.get('MCO Date and Inv Ref')
                ),
                duplicate_mco=self.parse_boolean(row.get('Duplicate MCO (2nd version)')),
                mco_lot_mismatch=self.parse_boolean(
                    row.get('Lot/Unit on Cavco/Champion/etc. does not match')
                ),
                
                # Builder
                builder_invoice_amount=self.parse_decimal(
                    row.get(' Builder Invoice Amount ')
                ),
                serial_number=self.clean_string(row.get(' Serial Number ')),
                builder_invoice_date=self.parse_date(
                    row.get(' Builder Invoice Date ')
                ),
                builder_ship_date=self.parse_date(row.get(' Builder Ship Date ')),
                bill_to=self.clean_string(row.get(' Bill To ')),
                builder=self.clean_string(row.get(' Builder ')),
                
                # Commissions
                has_commissions=self.parse_boolean(row.get('Has_Commissions')),
                
                # Observations
                observations=self.clean_string(row.get('Observations')),
                cavco_champion_total=self.parse_decimal(
                    row.get('Cavco/Champion/CMH total')
                ),
                
                # Evidence Flags
                mco_not_match=self.parse_boolean(
                    row.get('1) MCO does not match')
                ),
                mco_indicates_home_sale_entity=self.parse_boolean(
                    row.get('2) MCO indicates Home Sale Entity as Owner')
                ),
                commission_but_no_sale=self.parse_boolean(
                    row.get('3) Commission recorded but no sale identified')
                ),
                no_mco_available=self.parse_boolean(
                    row.get('4) No MCO available')
                ),
                
                # Metadata
                source_file=source_file
            )
            
            return unit
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error creating unit {row.get("Unit / Lot")}: {str(e)}'
                )
            )
            return None

    def create_commissions(self, row, unit):
        """Parse and create commission records from a CSV row."""
        
        commissions_count = 0
        
        # Get the commission amount from the billed column
        comm_col = 'Billed to "Commissions" GL (e.g. SBR, Ernesto). Would not include "Bonus" GL or other'
        comm_amount = self.parse_decimal(row.get(comm_col))
        
        if comm_amount and comm_amount > 0:
            try:
                # Parse recipient from memo or default
                memo_val = self.clean_string(row.get('Memo / Invoice Number'))
                recipient_val = 'Unknown'
                
                # Try to extract recipient from column or memo
                if 'SBR' in memo_val.upper():
                    recipient_val = 'SBR'
                elif 'ERNESTO' in memo_val.upper():
                    recipient_val = 'Ernesto'
                
                Commission.objects.create(
                    unit=unit,
                    amount=comm_amount,
                    recipient=recipient_val,
                    memo=memo_val,
                    percentage_of_sales=self.parse_decimal(
                        row.get('% of Sales Price')
                    ),
                    status='SUPPORTED' if row.get('Supported / Unsupported / Insufficient') == 'Supported' else 'UNSUPPORTED',
                    comments=self.clean_string(row.get('Comments'))
                )
                commissions_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Could not create commission for {unit.property_unit}: {e}'
                    )
                )
        
        return commissions_count

    # Utility methods for parsing
    def clean_string(self, value):
        """Clean and return string value."""
        if pd.isna(value):
            return ''
        return str(value).strip()

    def parse_decimal(self, value):
        """Parse decimal value from various formats."""
        if pd.isna(value) or value == '':
            return None
        
        try:
            # Remove $ and commas
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').strip()
                if value == '' or value == '-':
                    return None
            
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    def parse_boolean(self, value):
        """Parse boolean value."""
        if pd.isna(value):
            return False  # Default to False instead of None
        
        if isinstance(value, bool):
            return value
        
        str_value = str(value).strip().upper()
        
        if str_value in ['TRUE', 'YES', 'Y', '1', 'X']:
            return True
        elif str_value in ['FALSE', 'NO', 'N', '0', '']:
            return False
        
        return False  # Default to False for unknown values

    def parse_date(self, value):
        """Parse date value."""
        if pd.isna(value) or value == '':
            return None
        
        try:
            # Try pandas date parser
            date_val = pd.to_datetime(value)
            return date_val.date()
        except:
            return None
