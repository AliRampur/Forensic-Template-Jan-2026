# Cloud Run Deployment Script for TraceFlow (PowerShell)
# Builds and deploys the application to Google Cloud Run

$ErrorActionPreference = "Stop"

$PROJECT_ID = "agorapolis"
$SERVICE_NAME = "traceflow-service"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/traceflow"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "TraceFlow Cloud Run Deployment" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project ID: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Service: $SERVICE_NAME" -ForegroundColor Yellow
Write-Host "Region: $REGION" -ForegroundColor Yellow
Write-Host "Image: $IMAGE_NAME" -ForegroundColor Yellow
Write-Host ""

try {
    # Step 1: Build the Docker image
    Write-Host "[1/3] Building Docker image..." -ForegroundColor Green
    docker build -f Dockerfile.cloudrun -t "$IMAGE_NAME`:latest" .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker image built successfully" -ForegroundColor Green
    } else {
        throw "Docker build failed"
    }
    Write-Host ""

    # Step 2: Push to Container Registry
    Write-Host "[2/3] Pushing image to Google Container Registry..." -ForegroundColor Green
    docker push "$IMAGE_NAME`:latest"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Image pushed to GCR" -ForegroundColor Green
    } else {
        throw "Docker push failed"
    }
    Write-Host ""

    # Step 3: Deploy to Cloud Run
    Write-Host "[3/3] Deploying to Cloud Run..." -ForegroundColor Green
    gcloud run deploy $SERVICE_NAME `
      --image "$IMAGE_NAME`:latest" `
      --platform managed `
      --region $REGION `
      --allow-unauthenticated `
      --set-env-vars "INSTANCE_CONNECTION_NAME=agorapolis:us-central1:traceflow-db,DB_NAME=postgres,DB_USER=traceflow_user,DB_PASSWORD=5iwoxkMo,DEBUG=False,DJANGO_SECRET_KEY=django-insecure-prod-key-change-this,GCP_PROJECT_ID=agorapolis,GCP_BUCKET_NAME=traceflow" `
      --add-cloudsql-instances "agorapolis:us-central1:traceflow-db" `
      --memory 1Gi `
      --cpu 1 `
      --max-instances 10 `
      --min-instances 0 `
      --timeout 3600

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Deployment complete!" -ForegroundColor Green
    } else {
        throw "Cloud Run deployment failed"
    }

} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
gcloud run services describe $SERVICE_NAME --region $REGION --format="table(status.url)"
Write-Host ""
Write-Host "Deployment URL:" -ForegroundColor Yellow
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
