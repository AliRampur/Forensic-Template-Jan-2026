gcloud run deploy traceflow-service \
  --image gcr.io/PROJECT_ID/traceflow \
  --add-cloudsql-instances PROJECT_ID:REGION:traceflow-db \
  --set-env-vars "DB_NAME=...,DB_USER=...,DB_PASS=..." \
  --allow-unauthenticated