# Cloud Build Deployment Script for TraceFlow (PowerShell)
# Uses Google Cloud Build to build and deploy to Cloud Run

$ErrorActionPreference = "Stop"

$PROJECT_ID = "agorapolis"
$SERVICE_NAME = "traceflow-service"
$REGION = "us-central1"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "TraceFlow Cloud Build & Cloud Run Deployment" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project ID: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Service: $SERVICE_NAME" -ForegroundColor Yellow
Write-Host "Region: $REGION" -ForegroundColor Yellow
Write-Host ""

try {
    # Submit build to Cloud Build
    Write-Host "[1/2] Submitting build to Cloud Build..." -ForegroundColor Green
    Write-Host ""
    
    gcloud builds submit `
      --config=cloudbuild.yaml `
      --project=$PROJECT_ID
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Build submitted successfully to Cloud Build" -ForegroundColor Green
    } else {
        throw "Cloud Build submission failed"
    }
    Write-Host ""

    # Verify deployment
    Write-Host "[2/2] Verifying Cloud Run deployment..." -ForegroundColor Green
    Write-Host ""
    
    Start-Sleep -Seconds 10
    
    gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
    
    Write-Host ""
    Write-Host "Deployment verification complete!" -ForegroundColor Green
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Deployment Status" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Service URL:" -ForegroundColor Yellow
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"

Write-Host ""
Write-Host "Build History:" -ForegroundColor Yellow
gcloud builds list --project=$PROJECT_ID --limit=5

Write-Host ""
Write-Host "To view detailed build logs:" -ForegroundColor Cyan
Write-Host "  gcloud builds log BUILD_ID --project=$PROJECT_ID" -ForegroundColor Gray
