#!/bin/bash

# Azure Infrastructure Deployment Script for Keilamenu
# This script deploys the Azure infrastructure using Bicep templates

set -e

# Configuration
APP_NAME="keilamenu"
RESOURCE_GROUP="${APP_NAME}-rg"
LOCATION="Sweden South"
SUBSCRIPTION_ID=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Login check
echo_info "Checking Azure CLI login status..."
if ! az account show &> /dev/null; then
    echo_warning "Not logged in to Azure. Please login."
    az login
fi

# Set subscription if provided
if [ -n "$SUBSCRIPTION_ID" ]; then
    echo_info "Setting subscription to: $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
fi

# Create resource group
echo_info "Creating resource group: $RESOURCE_GROUP"
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output table

# Deploy infrastructure
echo_info "Deploying infrastructure using Bicep template..."
az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file infrastructure/main.bicep \
    --parameters infrastructure/main.parameters.json \
    --output table

# Get deployment outputs
echo_info "Getting deployment outputs..."
WEB_APP_NAME=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name main \
    --query 'properties.outputs.webAppName.value' \
    --output tsv)

WEB_APP_URL=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name main \
    --query 'properties.outputs.webAppUrl.value' \
    --output tsv)

APP_GATEWAY_FQDN=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name main \
    --query 'properties.outputs.applicationGatewayFQDN.value' \
    --output tsv)

echo_info "Deployment completed successfully!"
echo_info "Web App Name: $WEB_APP_NAME"
echo_info "Web App URL: $WEB_APP_URL"
echo_info "Application Gateway FQDN: $APP_GATEWAY_FQDN"

echo_info "Next steps:"
echo "1. Deploy your application code using: ./deploy-app.sh"
echo "2. Access your application at: http://$APP_GATEWAY_FQDN"