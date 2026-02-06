"""
Management command to link builder invoice PDFs to inventory units
based on the builder_pdf_filename field match.
"""
from django.core.management.base import BaseCommand
from forensics.inventory_models import InventoryUnit, Document
from forensics.gcs_utils import list_builder_invoices
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Link builder invoice PDFs from GCS to inventory units by filename'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be linked without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Get all builder invoices from GCS
        invoices = list_builder_invoices()
        self.stdout.write(f"Found {len(invoices)} builder invoices in GCS")
        
        if not invoices:
            self.stdout.write(self.style.WARNING("No invoices found in GCS"))
            return
        
        # Get all inventory units that have a builder_pdf_filename
        units_with_pdfs = InventoryUnit.objects.filter(
            builder_pdf_filename__isnull=False
        ).exclude(builder_pdf_filename='')
        
        self.stdout.write(f"Found {units_with_pdfs.count()} inventory units with builder_pdf_filename")
        
        linked_count = 0
        not_found_count = 0
        
        for unit in units_with_pdfs:
            pdf_filename = unit.builder_pdf_filename.strip()
            
            # Find matching invoice in GCS
            matching_invoice = None
            for invoice in invoices:
                if invoice['name'] == pdf_filename or invoice['name'].lower() == pdf_filename.lower():
                    matching_invoice = invoice
                    break
            
            if matching_invoice:
                # Check if document already exists
                doc, created = Document.objects.update_or_create(
                    inventory_unit=unit,
                    document_type='BUILDER_INVOICE',
                    title=pdf_filename,
                    defaults={
                        'property': unit.property,
                        'description': f'Builder invoice for {unit.property_unit}',
                        'gcs_path': matching_invoice['gcs_path'],
                        'file_url': matching_invoice['url'],
                        'file_size_bytes': matching_invoice['size_bytes'],
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Linked {pdf_filename} to {unit.property_unit}")
                    )
                    linked_count += 1
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Updated {pdf_filename} for {unit.property_unit}")
                    )
                    linked_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f"✗ Not found in GCS: {pdf_filename} ({unit.property_unit})")
                )
                not_found_count += 1
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes made"))
        
        self.stdout.write(self.style.SUCCESS(f"\nSummary:"))
        self.stdout.write(f"  Linked: {linked_count}")
        self.stdout.write(f"  Not found in GCS: {not_found_count}")
