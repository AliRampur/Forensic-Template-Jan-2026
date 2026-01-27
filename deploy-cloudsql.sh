#!/bin/bash

# TraceFlow - Deploy PostgreSQL to GCP Cloud SQL
# This script sets up a PostgreSQL database on Google Cloud SQL

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="traceflow-2026"
INSTANCE_NAME="traceflow-postgres"
REGION="us-central1"
TIER="db-f1-micro"
DB_NAME="postgres"
DB_USER="traceflow_user"
NETWORK_NAME="default"

echo -e "${YELLOW}=====================================================${NC}"
echo -e "${YELLOW}TraceFlow - Cloud SQL PostgreSQL Deployment${NC}"
echo -e "${YELLOW}=====================================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed.${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set the project
echo -e "${YELLOW}Setting GCP project to ${PROJECT_ID}...${NC}"
gcloud config set project $PROJECT_ID

# Check if instance already exists
echo -e "${YELLOW}Checking if Cloud SQL instance exists...${NC}"
if gcloud sql instances describe $INSTANCE_NAME --quiet 2>/dev/null; then
    echo -e "${GREEN}✓ Instance ${INSTANCE_NAME} already exists${NC}"
else
    echo -e "${YELLOW}Creating Cloud SQL PostgreSQL instance...${NC}"
    gcloud sql instances create $INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=$TIER \
        --region=$REGION \
        --network=$NETWORK_NAME \
        --availability-type=zonal \
        --backup-start-time=03:00 \
        --enable-bin-log \
        --database-flags=cloudsql_iam_authentication=on \
        --display-name="TraceFlow PostgreSQL Database"
    
    echo -e "${GREEN}✓ Cloud SQL instance created successfully${NC}"
fi

echo ""
echo -e "${YELLOW}Configuring database and user...${NC}"

# Get the instance connection name
INSTANCE_CONNECTION=$(gcloud sql instances describe $INSTANCE_NAME --format='value(connectionName)')
echo -e "${GREEN}✓ Instance Connection Name: ${INSTANCE_CONNECTION}${NC}"

# Create database
echo -e "${YELLOW}Creating database ${DB_NAME}...${NC}"
gcloud sql databases create $DB_NAME \
    --instance=$INSTANCE_NAME \
    --quiet 2>/dev/null || echo -e "${GREEN}✓ Database ${DB_NAME} already exists${NC}"

# Generate secure password for database user
DB_PASSWORD=$(openssl rand -base64 32)

# Create database user
echo -e "${YELLOW}Creating database user ${DB_USER}...${NC}"
gcloud sql users create $DB_USER \
    --instance=$INSTANCE_NAME \
    --password=$DB_PASSWORD \
    --quiet 2>/dev/null || echo -e "${GREEN}✓ User ${DB_USER} already exists (updating password)${NC}"

# Update user password (if user already exists)
gcloud sql users set-password $DB_USER \
    --instance=$INSTANCE_NAME \
    --password=$DB_PASSWORD

echo ""
echo -e "${YELLOW}Configuring IAM authentication for Cloud SQL...${NC}"

# Get the current user's email for IAM authentication
CURRENT_USER=$(gcloud config get-value account)
echo -e "${GREEN}✓ Current user: ${CURRENT_USER}${NC}"

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member=user:$CURRENT_USER \
    --role=roles/cloudsql.client \
    --condition=None \
    --quiet 2>/dev/null || echo -e "${GREEN}✓ IAM role already assigned${NC}"

echo ""
echo -e "${YELLOW}Getting Cloud SQL instance details...${NC}"

# Get instance IP address
INSTANCE_IP=$(gcloud sql instances describe $INSTANCE_NAME --format='value(ipAddresses[0].ipAddress)')
echo -e "${GREEN}✓ Instance IP Address: ${INSTANCE_IP}${NC}"

echo ""
echo -e "${YELLOW}Creating .env file for Django...${NC}"

# Create .env file
cat > .env.cloudsql << EOF
# GCP Cloud SQL Configuration for Django
DB_ENGINE=django.db.backends.postgresql
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$INSTANCE_IP
DB_PORT=5432

# Connection via Cloud SQL Proxy (for local development)
# Use this format: /cloudsql/$INSTANCE_CONNECTION
INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION

# Django settings
DEBUG=False
ALLOWED_HOSTS=*
DJANGO_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
EOF

echo -e "${GREEN}✓ Created .env.cloudsql file${NC}"

echo ""
echo -e "${YELLOW}Creating connection string for Cloud SQL Proxy...${NC}"

cat > cloudsql-proxy-config.txt << EOF
# Cloud SQL Proxy Configuration
# For local development, use Cloud SQL Proxy to connect securely

# Installation:
# curl https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -o cloud_sql_proxy
# chmod +x cloud_sql_proxy

# Usage:
# ./cloud_sql_proxy -instances=$INSTANCE_CONNECTION_NAME=tcp:5432

# Then connect Django via:
# psycopg2://user:password@127.0.0.1:5432/database
EOF

echo -e "${GREEN}✓ Created cloudsql-proxy-config.txt${NC}"

echo ""
echo -e "${YELLOW}Creating Cloud Run deployment script...${NC}"

cat > deploy-to-cloudrun.sh << 'DEPLOY_SCRIPT'
#!/bin/bash

set -e

# Configuration
PROJECT_ID="traceflow-2026"
SERVICE_NAME="traceflow-app"
REGION="us-central1"
IMAGE_NAME="traceflow"

echo "Building and deploying to Cloud Run..."

# Build the Docker image
echo "Building Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars "DEBUG=False" \
    --memory 512Mi \
    --timeout 3600 \
    --env-vars-file .env.cloudsql

echo "Deployment complete!"
echo "Service URL: https://$SERVICE_NAME-$(openssl rand -hex 2).a.run.app"
DEPLOY_SCRIPT

chmod +x deploy-to-cloudrun.sh
echo -e "${GREEN}✓ Created deploy-to-cloudrun.sh${NC}"

echo ""
echo -e "${GREEN}=====================================================${NC}"
echo -e "${GREEN}Cloud SQL Setup Complete!${NC}"
echo -e "${GREEN}=====================================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Install Cloud SQL Proxy (for local development):"
echo "   curl https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -o cloud_sql_proxy"
echo "   chmod +x cloud_sql_proxy"
echo ""
echo "2. Connect locally using Cloud SQL Proxy:"
echo "   ./cloud_sql_proxy -instances=$INSTANCE_CONNECTION_NAME=tcp:5432 &"
echo ""
echo "3. Test the connection:"
echo "   psql -h 127.0.0.1 -U $DB_USER -d $DB_NAME"
echo ""
echo "4. Update your Django settings to use the .env.cloudsql:"
echo "   source .env.cloudsql"
echo ""
echo "5. Run migrations against Cloud SQL:"
echo "   python manage.py migrate"
echo ""
echo "6. Deploy to Cloud Run:"
echo "   ./deploy-to-cloudrun.sh"
echo ""
echo -e "${YELLOW}Database Credentials:${NC}"
echo "  Instance: $INSTANCE_NAME"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Host: $INSTANCE_IP"
echo "  Connection Name: $INSTANCE_CONNECTION"
echo ""
echo -e "${YELLOW}Important: Save your database password${NC}"
echo "  Password: $DB_PASSWORD"
echo ""
echo "This has been saved to .env.cloudsql"
echo ""
