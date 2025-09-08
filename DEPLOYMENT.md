# Keilamenu - Azure Deployment Guide

This repository contains the infrastructure and deployment scripts for the Keilamenu application, a lunch menu scraper that fetches and displays restaurant menus.

## Architecture

The application is deployed on Azure using the following components:
- **Azure App Service (S1 SKU)**: Hosts the Flask application
- **Application Gateway**: Manages traffic and provides load balancing
- **Virtual Network**: Provides network isolation and security
- **Public IP**: Enables internet access through the Application Gateway

## Prerequisites

1. **Azure CLI**: Install from [Azure CLI installation guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Azure Subscription**: Active Azure subscription with appropriate permissions
3. **Bicep CLI**: Install from [Bicep installation guide](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/install)

## Quick Start

### 1. Login to Azure
```bash
az login
```

### 2. Deploy Infrastructure
```bash
./deploy-infrastructure.sh
```

This script will:
- Create a resource group named `keilamenu-rg`
- Deploy the Bicep template with all required resources
- Configure networking and security settings

### 3. Deploy Application
```bash
./deploy-app.sh
```

This script will:
- Deploy the Flask application using `az webapp up`
- Configure the runtime environment
- Set up the startup script

## Application Access

After deployment, the application will be available at:
- **Direct App Service URL**: https://keilamenuu.azurewebsites.net
- **Application Gateway URL**: http://[gateway-public-ip]

## Infrastructure Components

### App Service Configuration
- **Runtime**: Python 3.9
- **SKU**: S1 (Standard tier)
- **Features**: Always On, HTTPS Only
- **Startup Command**: `startup.sh`

### Application Gateway Configuration
- **SKU**: Standard_v2
- **Autoscaling**: 1-3 instances
- **Backend**: keilamenuu.azurewebsites.net
- **Health Probe**: HTTP health check

### Networking
- **Virtual Network**: 10.0.0.0/16
- **App Service Subnet**: 10.0.1.0/24 (with delegation)
- **Application Gateway Subnet**: 10.0.2.0/24

## Environment Variables

The application uses the following environment variables:
- `PORT`: Application port (default: 5000)

## Monitoring and Troubleshooting

### Check Application Logs
```bash
az webapp log tail --name keilamenu --resource-group keilamenu-rg
```

### Check Resource Status
```bash
az resource list --resource-group keilamenu-rg --output table
```

### Test Application Gateway
```bash
# Get the public IP
az network public-ip show --resource-group keilamenu-rg --name keilamenu-pip --query ipAddress

# Test connectivity
curl -I http://[public-ip]
```

## Cleanup

To remove all resources:
```bash
az group delete --name keilamenu-rg --yes --no-wait
```

## Files Structure

```
.
├── app.py                          # Main Flask application
├── requirements-minimal.txt        # Production dependencies
├── startup.sh                      # App Service startup script
├── deploy-infrastructure.sh        # Infrastructure deployment script
├── deploy-app.sh                   # Application deployment script
├── infrastructure/
│   ├── main.bicep                  # Bicep template for Azure resources
│   └── main.parameters.json        # Parameters for Bicep template
├── static/                         # Static web assets
├── templates/                      # Flask templates
└── DEPLOYMENT.md                   # This file
```

## Customization

### Changing App Name
To use a different app name, update the `appName` parameter in `infrastructure/main.parameters.json` and the `APP_NAME` variable in the deployment scripts.

### Scaling
To change the App Service plan size, modify the `skuName` and `skuTier` parameters in `infrastructure/main.parameters.json`.

### Location
To deploy to a different Azure region, update the `location` parameter in `infrastructure/main.parameters.json` and the `LOCATION` variable in the deployment scripts.

## Support

For issues and questions:
1. Check Azure App Service logs
2. Verify resource deployment status
3. Test network connectivity
4. Review Application Gateway health probes