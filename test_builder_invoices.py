#!/usr/bin/env python
"""
Test script to verify builder invoices are accessible from GCP Cloud Storage
Run this to check if your GCP credentials are working and invoices are present
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traceflow.settings')
django.setup()

from forensics.gcs_utils import list_builder_invoices, get_file_url

print("\n" + "="*60)
print("Builder Invoices GCP Connection Test")
print("="*60 + "\n")

# Check environment
print("📋 Configuration:")
print(f"  GCP Project: {os.environ.get('GCP_PROJECT_ID', 'traceflow')}")
print(f"  GCP Bucket: {os.environ.get('GCP_BUCKET_NAME', 'traceflow')}")
print(f"  GCP Auth: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'Using ADC')}")

# Test GCS connection
print("\n🔗 Testing GCS Connection...")
try:
    invoices = list_builder_invoices()
    print(f"✅ Connection successful!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("  1. Set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON")
    print("  2. Or run: gcloud auth application-default login")
    print("  3. Or ensure you're running on Cloud Run with proper service account")
    sys.exit(1)

# Display results
if invoices:
    print(f"\n📁 Found {len(invoices)} builder invoices:\n")
    
    total_size = 0
    for invoice in invoices:
        size_mb = invoice.get('size_mb', 0)
        total_size += size_mb
        print(f"  📄 {invoice['name']}")
        print(f"     Size: {size_mb:.2f} MB")
        print(f"     Path: {invoice['gcs_path']}")
        
        # Test signed URL generation
        if invoice.get('url'):
            print(f"     ✅ Download URL: Available (24h expiration)")
        else:
            print(f"     ⚠️  Download URL: Could not generate")
        print()
    
    print(f"💾 Total Size: {total_size:.2f} MB\n")
    print("✅ All systems operational!\n")
    
else:
    print("\n⚠️  No invoices found in gs://traceflow/builder_invoices/")
    print("This could mean:")
    print("  - The folder is empty")
    print("  - The path is incorrect")
    print("  - GCP credentials don't have read access")
    print()

print("="*60)
