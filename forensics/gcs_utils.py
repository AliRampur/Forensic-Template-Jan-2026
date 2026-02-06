"""
Google Cloud Storage utilities for TraceFlow
Handles fetching documents from GCP Cloud Storage buckets
"""
import os
import logging
from typing import List, Dict, Optional
from decimal import Decimal

try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

logger = logging.getLogger(__name__)

GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'traceflow')
GCP_BUCKET_NAME = os.environ.get('GCP_BUCKET_NAME', 'traceflow')


def get_gcs_client():
    """Get authenticated Google Cloud Storage client."""
    if not GCS_AVAILABLE:
        logger.warning("google-cloud-storage not installed")
        return None
    
    try:
        # Uses Application Default Credentials (ADC)
        # Works with:
        # - GCP Service Account credentials (GOOGLE_APPLICATION_CREDENTIALS env var)
        # - gcloud auth application-default login
        # - GCP Cloud Run/Compute Engine default service account
        return storage.Client(project=GCP_PROJECT_ID)
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        return None


def list_builder_invoices_simple(bucket_name: str = GCP_BUCKET_NAME, 
                                 folder: str = 'builder_Invoices') -> List[Dict]:
    """
    List builder invoice filenames from GCP Cloud Storage WITHOUT signing URLs.
    Fast operation - just returns filenames.
    
    Returns:
        List of dicts with keys: name, size_bytes, size_mb, gcs_path
    """
    client = get_gcs_client()
    if not client:
        logger.warning("GCS client unavailable, returning empty list")
        return []
    
    try:
        bucket = client.bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix=folder + '/'))
        
        invoices = []
        for blob in blobs:
            # Skip folder entries (blobs with empty size)
            if blob.name.endswith('/'):
                continue
            
            # Skip the folder prefix itself
            if blob.name == folder + '/':
                continue
            
            file_name = os.path.basename(blob.name)
            size_mb = Decimal(blob.size / (1024 * 1024)) if blob.size else Decimal(0)
            
            invoice = {
                'name': file_name,
                'size_bytes': blob.size or 0,
                'size_mb': float(size_mb),
                'gcs_path': f"gs://{bucket_name}/{blob.name}",
            }
            invoices.append(invoice)
        
        logger.info(f"Found {len(invoices)} builder invoices in GCS")
        return invoices
    
    except Exception as e:
        logger.error(f"Error listing builder invoices: {e}")
        return []


def list_builder_invoices(bucket_name: str = GCP_BUCKET_NAME, 
                          folder: str = 'builder_Invoices') -> List[Dict]:
    """
    List all builder invoice files from GCP Cloud Storage.
    
    Returns:
        List of dicts with keys: name, size_bytes, size_mb, gcs_path, url
    """
    client = get_gcs_client()
    if not client:
        logger.warning("GCS client unavailable, returning empty list")
        return []
    
    try:
        bucket = client.bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix=folder + '/'))
        
        invoices = []
        for blob in blobs:
            # Skip folder entries (blobs with empty size)
            if blob.name.endswith('/'):
                continue
            
            # Skip the folder prefix itself
            if blob.name == folder + '/':
                continue
            
            file_name = os.path.basename(blob.name)
            size_mb = Decimal(blob.size / (1024 * 1024)) if blob.size else Decimal(0)
            
            # Always generate signed URL for temporary authenticated access
            signed_url = generate_signed_url(blob, expiration_hours=72)  # 3 days validity
            
            invoice = {
                'name': file_name,
                'size_bytes': blob.size or 0,
                'size_mb': float(size_mb),
                'gcs_path': f"gs://{bucket_name}/{blob.name}",
                'url': signed_url,
            }
            invoices.append(invoice)
        
        logger.info(f"Found {len(invoices)} builder invoices in GCS")
        return invoices
    
    except Exception as e:
        logger.error(f"Error listing builder invoices: {e}")
        return []


def generate_signed_url(blob, expiration_hours: int = 24) -> str:
    """
    Generate a signed URL for a GCS blob with expiration using impersonated credentials.
    This works with Application Default Credentials without needing a service account key.
    
    Args:
        blob: google.cloud.storage.Blob object
        expiration_hours: How many hours the URL is valid
        
    Returns:
        Signed URL string
    """
    try:
        from datetime import timedelta
        from google.auth import impersonated_credentials
        from google.auth.transport import requests as google_requests
        import google.auth
        
        # Get the source credentials
        source_credentials, project = google.auth.default()
        
        # Use the default compute service account for signing
        target_service_account = "502947376621-compute@developer.gserviceaccount.com"
        
        # Check if we already have service account credentials with a signer
        if hasattr(source_credentials, 'signer') and hasattr(source_credentials, 'service_account_email'):
            # Already using service account credentials, use them directly
            signing_credentials = source_credentials
        else:
            # Impersonate the service account to get signing credentials
            # This calls the IAM API to sign on behalf of the service account
            target_scopes = ['https://www.googleapis.com/auth/devstorage.read_only']
            signing_credentials = impersonated_credentials.Credentials(
                source_credentials=source_credentials,
                target_principal=target_service_account,
                target_scopes=target_scopes,
                lifetime=3600  # Token lifetime in seconds
            )
        
        # Generate signed URL using the impersonated credentials
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=expiration_hours),
            method="GET",
            credentials=signing_credentials,
        )
        logger.info(f"Generated signed URL for {blob.name}")
        return url
        
    except Exception as e:
        logger.error(f"Failed to generate signed URL: {e}")
        # Fallback to public URL (won't work for private buckets but prevents errors)
        return blob.public_url


def get_file_url(gcs_path: str) -> str:
    """
    Get a signed URL for a file in GCS.
    
    Args:
        gcs_path: Path like 'gs://bucket/path/to/file'
        
    Returns:
        Signed URL or empty string if unavailable
    """
    if not gcs_path.startswith('gs://'):
        return ""
    
    client = get_gcs_client()
    if not client:
        return ""
    
    try:
        # Parse gs://bucket/path/to/file
        parts = gcs_path.replace('gs://', '').split('/', 1)
        bucket_name = parts[0]
        blob_path = parts[1] if len(parts) > 1 else ''
        
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        return generate_signed_url(blob)
    except Exception as e:
        logger.error(f"Error getting file URL for {gcs_path}: {e}")
        return ""
