#!/bin/bash

# Complete Deployment Script for Keilamenu
# This script deploys both infrastructure and application

set -e

# Configuration
APP_NAME="keilamenuu"
RESOURCE_GROUP="${APP_NAME}-rg"
LOCATION="Sweden Central"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo_header() {
    echo -e "${BLUE}==== $1 ====${NC}"
}

# Check dependencies
echo_header "Checking Dependencies"

if ! command -v az &> /dev/null; then
    echo_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

echo_info "Azure CLI found"

# Login check
echo_info "Checking Azure CLI login status..."
if ! az account show &> /dev/null; then
    echo_warning "Not logged in to Azure. Please login."
    az login
fi

# Deploy Infrastructure
echo_header "Deploying Infrastructure"

echo_info "Creating resource group: $RESOURCE_GROUP"
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output table

echo_info "Deploying Bicep template..."
az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file infrastructure/main.bicep \
    --parameters infrastructure/main.parameters.json \
    --output table

# Deploy Application
echo_header "Deploying Application"

# Backup and use minimal requirements
if [ -f "requirements.txt" ] && [ ! -f "requirements-original.txt" ]; then
    echo_info "Backing up original requirements.txt"
    cp requirements.txt requirements-original.txt
fi

echo_info "Using minimal requirements for deployment"
cp requirements-minimal.txt requirements.txt

# Deploy application
echo_info "Deploying Flask application..."
az webapp up \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --runtime "PYTHON:3.9" \
    --sku S1 \
    --startup-file "bash /home/site/wwwroot/startup.sh"

# Restore original requirements
if [ -f "requirements-original.txt" ]; then
    echo_info "Restoring original requirements.txt"
    mv requirements-original.txt requirements.txt
fi

# Get deployment information
echo_header "Deployment Complete"

WEB_APP_URL="https://${APP_NAME}.azurewebsites.net"
APP_GATEWAY_FQDN=$(az network public-ip show \
    --resource-group "$RESOURCE_GROUP" \
    --name "${APP_NAME}-pip" \
    --query dnsSettings.fqdn \
    --output tsv 2>/dev/null || echo "Not available yet")

echo_info "Deployment completed successfully!"
echo_info "Application Name: $APP_NAME"
echo_info "Resource Group: $RESOURCE_GROUP"
echo_info "Web App URL: $WEB_APP_URL"
echo_info "Application Gateway FQDN: $APP_GATEWAY_FQDN"

echo_header "Testing Application"
echo_info "Testing application endpoint..."
sleep 10  # Give the app a moment to start

if curl -f -s "$WEB_APP_URL" > /dev/null; then
    echo_info "✅ Application is responding successfully!"
else
    echo_warning "⚠️  Application might still be starting up. Please wait a few minutes and try accessing: $WEB_APP_URL"
fi

echo_header "Next Steps"
echo "1. Access your application at: $WEB_APP_URL"
echo "2. Monitor logs with: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo "3. Application Gateway will be available at: http://$APP_GATEWAY_FQDN (may take additional time to configure)"