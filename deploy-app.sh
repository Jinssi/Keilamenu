#!/bin/bash

# Application Deployment Script for Keilamenu
# This script deploys the Flask application to Azure App Service using az webapp up

set -e

# Configuration
APP_NAME="keilamenuu"
RESOURCE_GROUP="${APP_NAME}-rg"
LOCATION="Sweden Central"

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

# Check if resource group exists
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    echo_error "Resource group $RESOURCE_GROUP does not exist. Please run deploy-infrastructure.sh first."
    exit 1
fi

# Backup original requirements.txt
if [ -f "requirements.txt" ] && [ ! -f "requirements-original.txt" ]; then
    echo_info "Backing up original requirements.txt"
    cp requirements.txt requirements-original.txt
fi

# Use minimal requirements for deployment
echo_info "Using minimal requirements for deployment"
cp requirements-minimal.txt requirements.txt

# Make startup script executable
chmod +x startup.sh

# Deploy application using az webapp up
echo_info "Deploying application to Azure App Service..."
az webapp up \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --runtime "PYTHON:3.10" \
    --sku P0V3 \
    
# `az webapp up` does not accept --startup-file on all platforms/versions.
# Configure the startup file explicitly after deployment instead.
echo_info "Configuring startup file for the app..."
az webapp config set --resource-group "$RESOURCE_GROUP" --name "$APP_NAME" --startup-file "startup.sh"

# Restore original requirements.txt
if [ -f "requirements-original.txt" ]; then
    echo_info "Restoring original requirements.txt"
    mv requirements-original.txt requirements.txt
fi

# Get app URL
APP_URL="https://${APP_NAME}.azurewebsites.net"

echo_info "Application deployed successfully!"
echo_info "Application URL: $APP_URL"
echo_info "DNS configured at: https://keilamenuu.azurewebsites.net"

# Test the deployment
echo_info "Testing application endpoint..."
if curl -f -s "$APP_URL" > /dev/null; then
    echo_info "Application is responding successfully!"
else
    echo_warning "Application might still be starting up. Please wait a few minutes and try accessing: $APP_URL"
fi