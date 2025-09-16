#!/bin/bash
# === Google Cloud Deployment Script for Demo Mode ===
# Deploys the ETrade Strategy to Google Cloud Run with Demo Sandbox trading

set -e

echo "🚀 Starting Google Cloud Deployment for Demo Mode"
echo "=================================================="

# Configuration
PROJECT_ID="odin-187104"
REGION="us-west2"
SERVICE_NAME="etrade-strategy-demo"
IMAGE_NAME="gcr.io/${PROJECT_ID}/etrade-strategy:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if logged into gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "Not logged into gcloud. Please run 'gcloud auth login' first."
        exit 1
    fi
    
    # Check if project is set
    CURRENT_PROJECT=$(gcloud config get-value project)
    if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
        print_warning "Setting project to $PROJECT_ID"
        gcloud config set project $PROJECT_ID
    fi
    
    print_success "Prerequisites check passed"
}

# Build and push Docker image
build_and_push_image() {
    print_status "Building and pushing Docker image..."
    
    # Enable required APIs
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    
    # Build image using Cloud Build
    gcloud builds submit --tag $IMAGE_NAME .
    
    print_success "Docker image built and pushed successfully"
}

# Deploy to Cloud Run
deploy_to_cloud_run() {
    print_status "Deploying to Google Cloud Run..."
    
    # Create deployment configuration
    cat > cloudrun-demo.yaml << EOF
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: $SERVICE_NAME
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/execution-environment: gen2
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/execution-environment: gen2
    spec:
      containerConcurrency: 100
      timeoutSeconds: 300
      containers:
      - image: $IMAGE_NAME
        ports:
        - containerPort: 8080
        env:
        - name: DEPLOYMENT_MODE
          value: "demo"
        - name: AUTOMATION_ENABLED
          value: "true"
        - name: TELEGRAM_ENABLED
          value: "true"
        - name: ENABLE_ALERT_MANAGER
          value: "true"
        - name: ENABLE_PRIME_SYSTEM
          value: "true"
        - name: GCP_PROJECT_ID
          value: "$PROJECT_ID"
        - name: GCP_REGION
          value: "$REGION"
        - name: LOG_LEVEL
          value: "INFO"
        - name: PYTHONUNBUFFERED
          value: "1"
        - name: TZ
          value: "America/New_York"
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
          requests:
            cpu: "1"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 60
          timeoutSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 10
  traffic:
  - percent: 100
    latestRevision: true
EOF

    # Deploy to Cloud Run
    gcloud run services replace cloudrun-demo.yaml --region=$REGION
    
    print_success "Deployed to Google Cloud Run successfully"
}

# Configure environment variables
configure_environment() {
    print_status "Configuring environment variables..."
    
    # Set environment variables for the service
    gcloud run services update $SERVICE_NAME \
        --region=$REGION \
        --set-env-vars="DEPLOYMENT_MODE=demo" \
        --set-env-vars="AUTOMATION_ENABLED=true" \
        --set-env-vars="TELEGRAM_ENABLED=true" \
        --set-env-vars="ENABLE_ALERT_MANAGER=true" \
        --set-env-vars="ENABLE_PRIME_SYSTEM=true" \
        --set-env-vars="LOG_LEVEL=INFO" \
        --set-env-vars="PYTHONUNBUFFERED=1" \
        --set-env-vars="TZ=America/New_York"
    
    print_success "Environment variables configured"
}

# Test deployment
test_deployment() {
    print_status "Testing deployment..."
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    
    # Wait for service to be ready
    print_status "Waiting for service to be ready..."
    sleep 30
    
    # Test health endpoint
    if curl -f -s "$SERVICE_URL/health" > /dev/null; then
        print_success "Health check passed"
    else
        print_warning "Health check failed, but deployment may still be starting"
    fi
    
    # Test ready endpoint
    if curl -f -s "$SERVICE_URL/ready" > /dev/null; then
        print_success "Readiness check passed"
    else
        print_warning "Readiness check failed, but deployment may still be starting"
    fi
    
    print_success "Deployment testing completed"
    echo "Service URL: $SERVICE_URL"
}

# Display deployment information
display_info() {
    print_status "Deployment Information:"
    echo "=========================="
    echo "Project ID: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Service Name: $SERVICE_NAME"
    echo "Image: $IMAGE_NAME"
    echo "Deployment Mode: Demo (Sandbox)"
    echo "Automation: Enabled"
    echo "Telegram Alerts: Enabled"
    echo ""
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    echo "Service URL: $SERVICE_URL"
    echo ""
    
    print_success "Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Monitor the service logs: gcloud run logs tail $SERVICE_NAME --region=$REGION"
    echo "2. Check service status: gcloud run services describe $SERVICE_NAME --region=$REGION"
    echo "3. Update ETrade OAuth tokens when they expire"
    echo "4. Monitor Telegram alerts for trading signals"
}

# Main deployment function
main() {
    echo "🚀 Google Cloud Deployment for Demo Mode"
    echo "========================================="
    echo ""
    
    check_prerequisites
    build_and_push_image
    deploy_to_cloud_run
    configure_environment
    test_deployment
    display_info
    
    echo ""
    print_success "🎉 Demo deployment completed successfully!"
    print_warning "Remember to update ETrade OAuth tokens when they expire"
}

# Run main function
main "$@"
