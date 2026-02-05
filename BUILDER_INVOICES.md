# Builder Invoices Integration - GCP Cloud Storage

## Overview
The Document Inventory page now displays builder invoices stored in your GCP Cloud Storage bucket (`traceflow/builder_invoices`), with automatic linking to associated inventory units.

## Features

### 1. **Real-time Builder Invoice Listing**
- Fetches all PDF files from the `gs://traceflow/builder_invoices/` folder
- Displays file size and metadata
- Generates signed URLs for secure downloading (24-hour expiration by default)

### 2. **Inventory Unit Association**
- Automatically links invoices to inventory units when filenames match
- Displays unit details (property, unit number) on the invoice card
- Falls back to filename display if no unit match is found

### 3. **New Document Type**
- Added `BUILDER_INVOICE` as a document type in the Document model
- Can be filtered on the Document Inventory page
- Stores GCP Cloud Storage path in the database for reference

## Usage

### Viewing Builder Invoices
1. Navigate to `/documents/` on the TraceFlow site
2. Select "Builder Invoice" from the Document Type dropdown
3. The page will fetch and display all builder invoices from GCP Cloud Storage
4. Click the "⬇️ Download" button to download a PDF with a signed URL

### Syncing Builder Invoices to Database
To sync all builder invoices from GCP and link them to inventory units:

```bash
python manage.py sync_builder_invoices
```

**Options:**
- `--bucket traceflow` - GCP bucket name (default: traceflow)
- `--folder builder_invoices` - Folder within bucket (default: builder_invoices)
- `--dry-run` - Preview changes without saving

**Example:**
```bash
python manage.py sync_builder_invoices --dry-run
```

This will show what documents would be created/updated without making changes.

## Database Schema

### Document Model Changes
Added fields to track builder invoices:

| Field | Type | Purpose |
|-------|------|---------|
| `inventory_unit` | ForeignKey | Links to specific InventoryUnit |
| `gcs_path` | CharField | Full GCS path (gs://bucket/path/file.pdf) |
| `document_type` | CharField | Now includes BUILDER_INVOICE choice |

### Related Model
- **InventoryUnit**: Now has a reverse relationship to documents via `documents` related_name

## GCP Cloud Storage Setup

### Prerequisites
1. **Google Cloud Storage Access**: Your application needs access to the `traceflow` bucket
2. **Authentication**: Uses Application Default Credentials (ADC)
   - On Cloud Run: Uses default service account
   - Local development: Set `GOOGLE_APPLICATION_CREDENTIALS` to service account JSON file
   - Alternative: Run `gcloud auth application-default login`

### Environment Variables (Optional)
```
GCP_PROJECT_ID=traceflow
GCP_BUCKET_NAME=traceflow
```

### Files in GCP
- **Location**: `gs://traceflow/builder_invoices/`
- **Format**: PDF files with optional builder invoice filenames
- **Naming**: Filenames can include unit numbers for automatic matching
- **Permissions**: Bucket should be readable by the TraceFlow service account

## API Reference

### list_builder_invoices()
Fetch builder invoices from GCP Cloud Storage.

```python
from forensics.gcs_utils import list_builder_invoices

invoices = list_builder_invoices(bucket_name='traceflow', folder='builder_invoices')
# Returns: [
#   {
#     'name': 'filename.pdf',
#     'size_bytes': 1024000,
#     'size_mb': 1.0,
#     'gcs_path': 'gs://traceflow/builder_invoices/filename.pdf',
#     'url': 'https://storage.googleapis.com/...'
#   }
# ]
```

### get_file_url()
Get a signed URL for a file in GCS.

```python
from forensics.gcs_utils import get_file_url

url = get_file_url('gs://traceflow/builder_invoices/my_file.pdf')
# Returns: signed URL valid for 24 hours
```

### Management Command
```python
from forensics.management.commands.sync_builder_invoices import Command

cmd = Command()
cmd.handle(bucket='traceflow', folder='builder_invoices', dry_run=True)
```

## Troubleshooting

### "No builder invoices found"
1. **Check GCP Credentials**: Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set or you're running on Cloud Run
2. **Check Bucket Access**: Verify the service account has `storage.objects.list` permission
3. **Check Path**: Verify files exist in `gs://traceflow/builder_invoices/`

### "Failed to initialize GCS client"
- Ensure `google-cloud-storage` is installed: `pip install google-cloud-storage`
- Check that authentication credentials are properly configured

### File size shows as 0
- The GCS API may not have calculated the size; refresh the page to retry

## Template Display

The Document Inventory template displays builder invoices with:
- **Icon**: 🏗️ (construction)
- **Badge**: "Builder Invoice" (purple gradient)
- **Unit Info**: Associated inventory unit (if found)
- **Download**: Direct link to GCS file with signed URL
- **Size**: File size in MB

## Future Enhancements
- [ ] Batch download invoices as ZIP
- [ ] Automatic OCR extraction of invoice data
- [ ] Match invoices by builder PDF filename field from CSV imports
- [ ] Invoice aging report (invoices older than 90 days)
- [ ] Cost analysis by builder/vendor
