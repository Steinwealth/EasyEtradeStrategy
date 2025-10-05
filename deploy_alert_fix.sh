#!/bin/bash

# Deploy Alert Format Fix
# Updates the deployed service with the new OAuth alert format

set -e

# Configuration
PROJECT_ID="easy-etrade-strategy"
REGION="us-central1"
SERVICE_NAME="easy-etrade-strategy-223967598315"

echo "🚀 Deploying OAuth Alert Format Fix..."
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"

# Set project
gcloud config set project ${PROJECT_ID}

echo ""
echo "📊 Building and deploying updated service..."

# Build and deploy the service
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME} .

gcloud run deploy ${SERVICE_NAME} \
    --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --concurrency 10 \
    --max-instances 1 \
    --set-env-vars "LOG_LEVEL=INFO,PORT=8080,HOST=0.0.0.0" \
    --set-env-vars "GCP_PROJECT=${PROJECT_ID}" \
    --set-env-vars "ENVIRONMENT=production" \
    --set-env-vars "SYSTEM_MODE=full_trading" \
    --set-env-vars "STRATEGY_MODE=standard" \
    --set-env-vars "ETRADE_MODE=demo" \
    --set-env-vars "ENABLE_MULTI_STRATEGY=true"

echo ""
echo "✅ Service deployed successfully!"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")
echo "📊 Service URL: ${SERVICE_URL}"

# Test the service
echo ""
echo "🔍 Testing the updated service..."

# Test health endpoint
echo "Testing health endpoint..."
curl -f "${SERVICE_URL}/health" && echo "✅ Health check passed" || echo "❌ Health check failed"

# Test the midnight alert endpoint
echo "Testing midnight alert endpoint..."
curl -X POST "${SERVICE_URL}/api/alerts/midnight-token-expiry" \
    -H "Content-Type: application/json" \
    -d '{}' && echo "✅ Midnight alert endpoint working" || echo "❌ Midnight alert endpoint failed"

echo ""
echo "🎯 Deployment complete!"
echo ""
echo "📋 Updated Service Details:"
echo "  URL: ${SERVICE_URL}"
echo "  Health: ${SERVICE_URL}/health"
echo "  Midnight Alert: ${SERVICE_URL}/api/alerts/midnight-token-expiry"
echo "  Market Open Alert: ${SERVICE_URL}/api/alerts/market-open"
echo ""
echo "🔍 Cloud Scheduler Jobs:"
echo "  Midnight Alert: oauth-midnight-alert (0 0 * * * - midnight ET)"
echo "  Market Open Alert: oauth-market-open-alert (30 8 * * 1-5 - 8:30 AM ET weekdays)"
echo ""
echo "✅ OAuth alerts will now use the new concise format!"
echo "✅ Next midnight alert will use the updated format!"
