#!/bin/bash
# UVA Sustainability Metrics API - Run Script

set -e

echo "Building Docker image..."
docker build -t uva-sustain-api:latest .

echo ""
echo "Starting container..."
docker run --rm -p 8080:8080 --env-file .env uva-sustain-api:latest

