#!/bin/bash
# Startup script for Azure App Service

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt"
    pip install --no-cache-dir -r requirements.txt
fi

# Start the application with gunicorn
echo "Starting application with gunicorn"
gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers=1 app:app