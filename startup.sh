#!/bin/bash
# Minimal startup script for Azure App Service
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PORT="${PORT:-8000}"

echo "Starting Gunicorn from ${SCRIPT_DIR} on port ${PORT}"
exec gunicorn --bind "0.0.0.0:${PORT}" --timeout 600 --workers 1 app:app