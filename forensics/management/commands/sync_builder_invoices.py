"""
Management command to sync builder invoices from GCP Cloud Storage
"""
import os
import re
from decimal import Decimal
from typing import Optional
from django.core.management.base import BaseCommand
from forensics.inventory_models import Document, InventoryUnit
from forensics.gcs_utils import list_builder_invoices

class Command(BaseCommand):
    help = 'Sync builder invoices from GCP Cloud Storage with inventory units'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--bucket',
            type=str,
            default='traceflow',
            help='GCP bucket name (default: traceflow)'
        )
        parser.add_argument(
            '--folder',
            type=str,
            default='builder_invoices',
            help='Folder in bucket to sync (default: builder_invoices)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating'
        )
    
    def handle(self, *args, **options):
        bucket = options['bucket']
        folder = options['folder']
        dry_run = options['dry_run']
        
        self.stdout.write(f'Syncing builder invoices from gs://{bucket}/{folder}/')
        
        # Get all invoices from GCS
        invoices = list_builder_invoices(bucket_name=bucket, folder=folder)
        
        if not invoices:
            self.stdout.write(self.style.WARNING('No invoices found'))
            return
        
        self.stdout.write(f'Found {len(invoices)} invoices')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for invoice in invoices:
            file_name = invoice['name']
            gcs_path = invoice['gcs_path']
            size_mb = Decimal(str(invoice['size_mb']))
            
            # Try to find associated inventory unit by filename
            # Pattern: some units might have PDF filename in their data
            inventory_unit = self._find_inventory_unit_by_filename(file_name)
            
            # Check if document already exists
            existing = Document.objects.filter(
                document_type='BUILDER_INVOICE',
                file_name=file_name
            ).first()
            
            if existing:
                # Update existing
                existing.gcs_path = gcs_path
                existing.file_size_mb = size_mb
                existing.inventory_unit = inventory_unit
                if not dry_run:
                    existing.save()
                updated_count += 1
                status = "UPDATED"
            else:
                # Create new
                doc = Document(
                    document_type='BUILDER_INVOICE',
                    title=file_name.replace('.pdf', ''),
                    file_name=file_name,
                    gcs_path=gcs_path,
                    file_size_mb=size_mb,
                    inventory_unit=inventory_unit,
                    description=f'Builder invoice from GCP Cloud Storage'
                )
                if not dry_run:
                    doc.save()
                created_count += 1
                status = "CREATED"
            
            unit_info = f" -> {inventory_unit.property_unit}" if inventory_unit else ""
            self.stdout.write(f'  {status}: {file_name}{unit_info}')
            
        self.stdout.write(self.style.SUCCESS(
            f'\nSync complete: {created_count} created, {updated_count} updated'
        ))
    
    def _find_inventory_unit_by_filename(self, filename: str) -> Optional[InventoryUnit]:
        """
        Try to find an inventory unit that matches this filename.
        
        This is a heuristic - it looks for common patterns in filenames
        like unit numbers, property codes, etc.
        """
        # Remove extension
        name_without_ext = os.path.splitext(filename)[0]
        
        # Try exact match on builder_pdf_filename if that field exists
        try:
            # Some filenames might be exact matches to InventoryUnit builder data
            unit = InventoryUnit.objects.filter(
                builder_pdf_filename=filename
            ).first()
            if unit:
                return unit
        except:
            pass
        
        # Try to extract unit number patterns
        # Look for patterns like "25XXX" (lot numbers) or other numeric patterns
        numbers = re.findall(r'\d+', name_without_ext)
        
        if numbers:
            # Try matching by unit number
            unit_number = numbers[-1]  # Often the last number is the unit number
            unit = InventoryUnit.objects.filter(
                unit_number=unit_number
            ).first()
            if unit:
                return unit
        
        return None
