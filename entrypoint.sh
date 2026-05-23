#!/bin/bash
# entrypoint.sh - Ensure required directories exist, then start Gunicorn

set -e

# Create the database directory if it doesn't exist (in case the volume mount is empty)
mkdir -p /app/backend/database

# Start Gunicorn with production settings
exec gunicorn -w 4 -b 0.0.0.0:5000 app:app
