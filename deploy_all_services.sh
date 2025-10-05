#!/bin/bash

# Deploy All Services Script
# Deploys all Prime services to Google Cloud Run

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT:-"easy-etrade-strategy"}
REGION=${GCP_REGION:-"us-central1"}

echo "🚀 Deploying All Prime Services to Google Cloud Run..."
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"

# Set project
gcloud config set project ${PROJECT_ID}

# 1. Deploy Main Trading System
echo ""
echo "📊 Deploying Main Trading System..."
SERVICE_NAME="easy-etrade-strategy-main"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

gcloud builds submit --tag ${IMAGE_NAME} --file Dockerfile .

gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
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
    --set-env-vars "ETRADE_MODE=demo"

MAIN_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")
echo "✅ Main Trading System deployed: ${MAIN_URL}"

# 2. Deploy Scanner Service
echo ""
echo "🔍 Deploying Scanner Service..."
SERVICE_NAME="easy-etrade-strategy-scanner"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

gcloud builds submit --tag ${IMAGE_NAME} --file scanner.Dockerfile .

gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 3600 \
    --concurrency 10 \
    --max-instances 1 \
    --set-env-vars "LOG_LEVEL=INFO,PORT=8080,HOST=0.0.0.0" \
    --set-env-vars "GCP_PROJECT=${PROJECT_ID}" \
    --set-env-vars "ENVIRONMENT=production"

SCANNER_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")
echo "✅ Scanner Service deployed: ${SCANNER_URL}"

# 3. Deploy Unified Services Manager
echo ""
echo "🎯 Deploying Unified Services Manager..."
SERVICE_NAME="easy-etrade-strategy-services"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Create Dockerfile for services
cat > services.Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO
ENV PORT=8080
ENV HOST=0.0.0.0

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["python3", "services/unified_services_manager.py"]
EOF

gcloud builds submit --tag ${IMAGE_NAME} --file services.Dockerfile .

gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
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
    --set-env-vars "ENVIRONMENT=production"

SERVICES_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")
echo "✅ Unified Services Manager deployed: ${SERVICES_URL}"

# 4. Test all services
echo ""
echo "🔍 Testing all deployed services..."

# Test main system
echo "Testing Main Trading System..."
curl -f "${MAIN_URL}/health" && echo "✅ Main system healthy" || echo "⚠️ Main system health check failed"

# Test scanner
echo "Testing Scanner Service..."
curl -f "${SCANNER_URL}/health" && echo "✅ Scanner healthy" || echo "⚠️ Scanner health check failed"

# Test services manager
echo "Testing Services Manager..."
curl -f "${SERVICES_URL}/health" && echo "✅ Services manager healthy" || echo "⚠️ Services manager health check failed"

# Cleanup
rm -f services.Dockerfile

echo ""
echo "🎯 All services deployment completed!"
echo ""
echo "📋 Service URLs:"
echo "  Main Trading System: ${MAIN_URL}"
echo "  Scanner Service: ${SCANNER_URL}"
echo "  Services Manager: ${SERVICES_URL}"
echo ""
echo "🔍 Health Checks:"
echo "  Main: ${MAIN_URL}/health"
echo "  Scanner: ${SCANNER_URL}/health"
echo "  Services: ${SERVICES_URL}/health"
echo ""
echo "📊 Metrics:"
echo "  Main: ${MAIN_URL}/metrics"
echo "  Scanner: ${SCANNER_URL}/metrics"
echo "  Services: ${SERVICES_URL}/metrics"
