#!/bin/bash
#
# Deploy Easy ETrade Strategy Trading System
# ===========================================
# 
# This script deploys:
# 1. Main trading system to Cloud Run (Demo + Signal-Only mode)
# 2. Cloud Scheduler job for 7 AM watchlist building
#
# Author: Easy ETrade Strategy Team
# Date: October 1, 2025

set -e

PROJECT_ID="easy-etrade-strategy"
REGION="us-central1"
SERVICE_NAME="easy-etrade-strategy"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "🚀 Deploying Easy ETrade Strategy Trading System"
echo "=" * 70
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# ============================================================================
# Step 1: Build and Push Container Image
# ============================================================================
echo "📦 Step 1: Building container image..."
echo ""

gcloud builds submit --tag ${IMAGE_NAME} \
  --project=${PROJECT_ID} \
  --timeout=20m

echo ""
echo "✅ Container image built successfully"
echo ""

# ============================================================================
# Step 2: Deploy to Cloud Run (Demo + Signal-Only Mode)
# ============================================================================
echo "🚀 Step 2: Deploying to Cloud Run (Demo + Signal-Only mode)..."
echo ""

gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_NAME} \
  --region=${REGION} \
  --platform=managed \
  --memory=4Gi \
  --cpu=2 \
  --max-instances=10 \
  --min-instances=1 \
  --timeout=3600 \
  --concurrency=1 \
  --set-env-vars="SYSTEM_MODE=signal_only,ETRADE_MODE=demo,STRATEGY_MODE=standard,LOG_LEVEL=INFO,CLOUD_MODE=true" \
  --allow-unauthenticated \
  --project=${PROJECT_ID}

echo ""
echo "✅ Cloud Run deployment complete"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format="value(status.url)")

echo "🌐 Service URL: ${SERVICE_URL}"
echo ""

# ============================================================================
# Step 3: Create Cloud Scheduler Job for 7 AM Watchlist Building
# ============================================================================
echo "📅 Step 3: Setting up Cloud Scheduler for 7 AM watchlist building..."
echo ""

# Check if job already exists
JOB_EXISTS=$(gcloud scheduler jobs list \
  --location=${REGION} \
  --project=${PROJECT_ID} \
  --filter="name:build-daily-watchlist" \
  --format="value(name)" 2>/dev/null || echo "")

if [ -z "$JOB_EXISTS" ]; then
    echo "Creating new Cloud Scheduler job..."
    
    gcloud scheduler jobs create http build-daily-watchlist \
      --location=${REGION} \
      --schedule="0 7 * * 1-5" \
      --time-zone="America/New_York" \
      --uri="${SERVICE_URL}/api/build-watchlist" \
      --http-method=POST \
      --headers="Content-Type=application/json" \
      --message-body='{"force_rebuild": true}' \
      --project=${PROJECT_ID} \
      --description="Build fresh dynamic watchlist at 7 AM ET for trading day"
    
    echo "✅ Cloud Scheduler job created"
else
    echo "⚠️ Cloud Scheduler job already exists, updating..."
    
    gcloud scheduler jobs update http build-daily-watchlist \
      --location=${REGION} \
      --schedule="0 7 * * 1-5" \
      --time-zone="America/New_York" \
      --uri="${SERVICE_URL}/api/build-watchlist" \
      --project=${PROJECT_ID}
    
    echo "✅ Cloud Scheduler job updated"
fi

echo ""

# ============================================================================
# Step 4: Verify Deployment
# ============================================================================
echo "🔍 Step 4: Verifying deployment..."
echo ""

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "${SERVICE_URL}/health")
echo "Response: ${HEALTH_RESPONSE}"
echo ""

# Test build-watchlist endpoint
echo "Testing build-watchlist endpoint (triggering manual build)..."
BUILD_RESPONSE=$(curl -s -X POST "${SERVICE_URL}/api/build-watchlist" -H "Content-Type: application/json" -d '{}')
echo "Response: ${BUILD_RESPONSE}"
echo ""

# ============================================================================
# Deployment Summary
# ============================================================================
echo "=" * 70
echo "🎉 Deployment Complete!"
echo "=" * 70
echo ""
echo "✅ Main Trading System:"
echo "   URL: ${SERVICE_URL}"
echo "   Mode: Demo + Signal-Only"
echo "   ETrade: Sandbox tokens"
echo "   Purpose: Signal validation, NO trades executed"
echo ""
echo "✅ Cloud Scheduler:"
echo "   Job: build-daily-watchlist"
echo "   Schedule: 7:00 AM ET (weekdays)"
echo "   Purpose: Build fresh watchlist daily"
echo ""
echo "✅ Watchlist System:"
echo "   File: data/watchlist/dynamic_watchlist.csv"
echo "   Symbols: 118 (as of last build)"
echo "   Scan frequency: Every 2 minutes"
echo "   Auto-rebuild: If stale or missing"
echo ""
echo "📊 Expected Behavior:"
echo "   • 7:00 AM ET: Fresh watchlist built (118 symbols)"
echo "   • 9:30 AM ET: Trading system scans for signals"
echo "   • Every 2 min: Scan watchlist for Buy confirmations"
echo "   • When signal found: Telegram alert sent (NO trade)"
echo "   • 4:00 PM ET: End-of-Day summary sent"
echo ""
echo "📱 Monitor Telegram for signal alerts:"
echo "   • 🔰🔰🔰 = Ultra High Confidence (98%+)"
echo "   • 🔰🔰 = High Confidence (85-97%)"
echo "   • 🔰 = Medium Confidence (70-84%)"
echo "   • 📟 = Standard Confidence (60-69%)"
echo "   • 🟡 = Lower Confidence (<60%)"
echo ""
echo "🔗 Useful Commands:"
echo "   View logs: gcloud logging read \"resource.labels.service_name=${SERVICE_NAME}\" --limit=50 --project=${PROJECT_ID}"
echo "   Check status: curl ${SERVICE_URL}/status"
echo "   Force watchlist build: curl -X POST ${SERVICE_URL}/api/build-watchlist"
echo ""
echo "🎯 Next Steps:"
echo "   1. Monitor Telegram for signal alerts today"
echo "   2. Validate signal quality over 1 week"
echo "   3. When satisfied, switch to Live mode with Production tokens"
echo ""
echo "=" * 70

