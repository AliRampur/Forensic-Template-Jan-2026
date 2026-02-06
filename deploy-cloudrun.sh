#!/bin/bash
# Cloud Run Deployment Script for TraceFlow
# Builds and deploys the application to Google Cloud Run

set -e  # Exit on error

PROJECT_ID="agorapolis"
SERVICE_NAME="traceflow-service"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/traceflow"

echo "============================================"
echo "TraceFlow Cloud Run Deployment"
echo "============================================"
echo ""
echo "Project ID: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Image: $IMAGE_NAME"
echo ""

# Step 1: Build the Docker image
echo "[1/3] Building Docker image..."
docker build -f Dockerfile.cloudrun -t "$IMAGE_NAME:latest" .
echo "✓ Docker image built successfully"
echo ""

# Step 2: Push to Container Registry
echo "[2/3] Pushing image to Google Container Registry..."
docker push "$IMAGE_NAME:latest"
echo "✓ Image pushed to GCR"
echo ""

# Step 3: Deploy to Cloud Run
echo "[3/3] Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image "$IMAGE_NAME:latest" \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "INSTANCE_CONNECTION_NAME=agorapolis:us-central1:traceflow-db,DB_NAME=postgres,DB_USER=traceflow_user,DB_PASSWORD=5iwoxkMo,DEBUG=False,DJANGO_SECRET_KEY=django-insecure-prod-key-change-this,GCP_PROJECT_ID=agorapolis,GCP_BUCKET_NAME=traceflow" \
  --add-cloudsql-instances "agorapolis:us-central1:traceflow-db" \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 0 \
  --timeout 3600

echo "✓ Deployment complete!"
echo ""
echo "============================================"
echo "Deployment Summary"
echo "============================================"
gcloud run services describe $SERVICE_NAME --region $REGION --format="table(status.url)"
