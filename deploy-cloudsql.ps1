<#
TraceFlow - Deploy PostgreSQL to GCP Cloud SQL (Windows PowerShell)
Minimal, robust script to set up Cloud SQL and generate .env.cloudsql
#>

param(
    [string]$ProjectId = "traceflow-2026",
    [string]$InstanceName = "traceflow-postgres",
    [string]$Region = "us-central1",
    [string]$Tier = "db-f1-micro",
    [string]$DbName = "postgres",
    [string]$DbUser = "traceflow_user"
)

function Info([string]$msg)   { Write-Host $msg -ForegroundColor Yellow }
function Ok([string]$msg)     { Write-Host $msg -ForegroundColor Green }
function Err([string]$msg)    { Write-Host $msg -ForegroundColor Red }

Info "=== TraceFlow - Cloud SQL PostgreSQL Deployment ==="

# Verify gcloud
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Err "gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"
    exit 1
}

Info "Setting project: $ProjectId"
gcloud config set project $ProjectId | Out-Null

# Check instance exists
Info "Checking Cloud SQL instance: $InstanceName"
$instanceList = gcloud sql instances list --filter="name=$InstanceName" --format="value(name)" 2>$null
$exists = $instanceList -ne $null -and $instanceList.Trim() -ne ""

if (-not $exists) {
    Info "Creating Cloud SQL instance..."
    gcloud sql instances create $InstanceName `
        --database-version=POSTGRES_15 `
        --tier=$Tier `
        --region=$Region `
        --availability-type=zonal `
        --backup-start-time=03:00 `
        --enable-bin-log `
        --database-flags=cloudsql_iam_authentication=on `
        --display-name "TraceFlow PostgreSQL Database" | Out-Null
    Ok "Instance created"
} else {
    Ok "Instance already exists"
}

# Get connection details
$instanceConnection = gcloud sql instances describe $InstanceName --format='value(connectionName)'
$instanceIp = gcloud sql instances describe $InstanceName --format='value(ipAddresses[0].ipAddress)'
Ok "Connection: $instanceConnection"
Ok "IP: $instanceIp"

# Create database
Info "Ensuring database: $DbName"
gcloud sql databases create $DbName --instance=$InstanceName 2>$null
if ($LASTEXITCODE -eq 0) { Ok "Database created" } else { Ok "Database exists" }

# Create / update user
Info "Ensuring user: $DbUser"
Add-Type -AssemblyName System.Security
$bytes = New-Object Byte[] 32
([System.Security.Cryptography.RNGCryptoServiceProvider]::new()).GetBytes($bytes)
$dbPassword = [Convert]::ToBase64String($bytes)

gcloud sql users create $DbUser --instance=$InstanceName --password=$dbPassword 2>$null
if ($LASTEXITCODE -eq 0) { Ok "User created" } else { Info "Updating user password"; gcloud sql users set-password $DbUser --instance=$InstanceName --password=$dbPassword; Ok "User password updated" }

# IAM role for current account
$currentUser = gcloud config get-value account
Info "Granting Cloud SQL Client to $currentUser"
gcloud projects add-iam-policy-binding $ProjectId --member="user:$currentUser" --role=roles/cloudsql.client 2>$null | Out-Null

# Write .env.cloudsql
Info "Writing .env.cloudsql"
$secretKey = [Guid]::NewGuid().ToString()
$envText = @'
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=traceflow_user
DB_PASSWORD=__DB_PASSWORD__
DB_HOST=__DB_HOST__
DB_PORT=5432
INSTANCE_CONNECTION_NAME=__INSTANCE_CONN__
DEBUG=False
ALLOWED_HOSTS=*
DJANGO_SECRET_KEY=__SECRET__
'@
$envText = $envText.Replace("__DB_PASSWORD__", $dbPassword).Replace("__DB_HOST__", $instanceIp).Replace("__INSTANCE_CONN__", $instanceConnection).Replace("__SECRET__", $secretKey)
Set-Content -Path ".env.cloudsql" -Value $envText -Encoding UTF8
Ok ".env.cloudsql created"

# Proxy doc
Info "Writing cloudsql-proxy-config.txt"
$proxyText = @'
# Cloud SQL Proxy
# cloud_sql_proxy -instances=__INSTANCE_CONN__=tcp:5432
# Connect: psycopg2://traceflow_user:<password>@127.0.0.1:5432/postgres
'@
$proxyText = $proxyText.Replace("__INSTANCE_CONN__", $instanceConnection)
Set-Content -Path "cloudsql-proxy-config.txt" -Value $proxyText -Encoding UTF8
Ok "cloudsql-proxy-config.txt created"

# Generate Cloud Run deploy script
Info "Writing deploy-to-cloudrun.ps1"
$deployPs = @'
param(
    [string]$ProjectId = "traceflow-2026",
    [string]$ServiceName = "traceflow-app",
    [string]$Region = "us-central1",
    [string]$ImageName = "traceflow-app"
)

Write-Host "Building Docker image..." -ForegroundColor Yellow
gcloud builds submit --tag gcr.io/$ProjectId/$ImageName

Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $ServiceName --image gcr.io/$ProjectId/$ImageName --platform managed --region $Region --allow-unauthenticated --env-vars-file .env.cloudsql --memory 512Mi --timeout 3600
'@
Set-Content -Path "deploy-to-cloudrun.ps1" -Value $deployPs -Encoding UTF8
Ok "deploy-to-cloudrun.ps1 created"

Ok "=== Cloud SQL Setup Complete ==="
Write-Host "Instance: $InstanceName" -ForegroundColor Yellow
Write-Host "Database: $DbName" -ForegroundColor Yellow
Write-Host "User: $DbUser" -ForegroundColor Yellow
Write-Host "Host: $instanceIp" -ForegroundColor Yellow
Write-Host "Connection: $instanceConnection" -ForegroundColor Yellow
