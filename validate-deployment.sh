#!/bin/bash

# Pre-deployment validation script for Keilamenu

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

echo_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo "=== Keilamenu Deployment Validation ==="
echo

# Check required files
echo "Checking required files..."

required_files=(
    "app.py"
    "requirements-minimal.txt"
    "startup.sh"
    "infrastructure/main.bicep"
    "infrastructure/main.parameters.json"
    "deploy.sh"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo_info "Found: $file"
    else
        echo_error "Missing: $file"
        exit 1
    fi
done

# Check script permissions
echo
echo "Checking script permissions..."

scripts=("deploy.sh" "deploy-app.sh" "deploy-infrastructure.sh" "startup.sh")

for script in "${scripts[@]}"; do
    if [ -x "$script" ]; then
        echo_info "Executable: $script"
    else
        echo_warning "Not executable: $script (fixing...)"
        chmod +x "$script"
        echo_info "Fixed: $script"
    fi
done

# Test Flask application
echo
echo "Testing Flask application..."

if python -c "import app; print('Flask app imports successfully')" 2>/dev/null; then
    echo_info "Flask application imports successfully"
else
    echo_error "Flask application has import errors"
    exit 1
fi

# Validate Bicep template syntax (basic check)
echo
echo "Validating Bicep template..."

if grep -q "Microsoft.Web/sites" infrastructure/main.bicep; then
    echo_info "Bicep template contains App Service resource"
else
    echo_error "Bicep template missing App Service resource"
    exit 1
fi

if grep -q "Microsoft.Network/applicationGateways" infrastructure/main.bicep; then
    echo_info "Bicep template contains Application Gateway resource"
else
    echo_error "Bicep template missing Application Gateway resource"
    exit 1
fi

# Check app name configuration
echo
echo "Checking app name configuration..."

if grep -q '"keilamenu"' infrastructure/main.parameters.json; then
    echo_info "App name 'keilamenu' configured in parameters"
else
    echo_error "App name not properly configured"
    exit 1
fi

echo
echo_info "All validation checks passed!"
echo_info "Ready for deployment with: ./deploy.sh"