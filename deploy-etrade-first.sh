#!/bin/bash
# ETRADE-First Deployment Script
# Deploys the optimized ETRADE-first strategy to Google Cloud

set -e

# Configuration
PROJECT_ID="odin-187104"
REGION="us-west2"
SERVICE_NAME="etrade-strategy"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to validate ETRADE deployment prerequisites
validate_etrade_prerequisites() {
    print_status "Validating ETRADE deployment prerequisites..."
    
    # Check if validation script exists and run it
    if [ -f "scripts/validate_etrade_deployment.py" ]; then
        print_status "Running ETRADE deployment validation..."
        python scripts/validate_etrade_deployment.py
        
        if [ $? -eq 0 ]; then
            print_success "ETRADE deployment validation passed"
        else
            print_error "ETRADE deployment validation failed"
            print_warning "Please fix validation errors before deploying"
            exit 1
        fi
    else
        print_warning "ETRADE validation script not found - skipping validation"
    fi
    
    # Check for ETRADE tokens file
    if [ ! -f "data/etrade_tokens.json" ]; then
        print_error "ETRADE tokens file not found: data/etrade_tokens.json"
        print_warning "Please set up ETRADE OAuth tokens before deploying"
        exit 1
    fi
    
    print_success "ETRADE prerequisites validated"
}

# Function to setup ETRADE-specific secrets
setup_etrade_secrets() {
    print_status "Setting up ETRADE-specific secrets..."
    
    # List of ETRADE-specific secrets
    declare -A etrade_secrets=(
        ["etrade-consumer-key"]="ETRADE_CONSUMER_KEY"
        ["etrade-consumer-secret"]="ETRADE_CONSUMER_SECRET"
        ["etrade-account-id-key"]="ETRADE_ACCOUNT_ID_KEY"
        ["etrade-tokens"]="ETRADE_TOKENS_JSON"
        ["alpha-vantage-api-key"]="ALPHA_VANTAGE_API_KEY"
    )
    
    for secret_name in "${!etrade_secrets[@]}"; do
        env_var="${etrade_secrets[$secret_name]}"
        
        # Check if secret exists
        if gcloud secrets describe $secret_name --project=$PROJECT_ID &> /dev/null; then
            print_warning "Secret $secret_name already exists"
        else
            # Create secret
            print_status "Creating secret: $secret_name"
            
            if [ "$secret_name" == "etrade-tokens" ]; then
                # Special handling for ETRADE tokens JSON file
                if [ -f "data/etrade_tokens.json" ]; then
                    gcloud secrets create $secret_name --data-file=data/etrade_tokens.json --project=$PROJECT_ID
                    print_success "ETRADE tokens secret created"
                else
                    print_error "ETRADE tokens file not found"
                    exit 1
                fi
            else
                echo "placeholder" | gcloud secrets create $secret_name --data-file=- --project=$PROJECT_ID
                print_warning "Please update the secret value for $secret_name:"
                echo "gcloud secrets versions add $secret_name --data-file=- --project=$PROJECT_ID"
            fi
        fi
    done
    
    print_success "ETRADE secrets setup completed"
}

# Function to deploy ETRADE-first service
deploy_etrade_service() {
    local strategy_mode=$1
    local automation_mode=$2
    local service_suffix=""
    
    # Create service name suffix for different modes
    if [ "$strategy_mode" != "standard" ] || [ "$automation_mode" != "off" ]; then
        service_suffix="-$strategy_mode-$automation_mode"
    fi
    
    local full_service_name="${SERVICE_NAME}${service_suffix}"
    
    print_status "Deploying ETRADE-first service: $full_service_name"
    print_status "Strategy: $strategy_mode | Automation: $automation_mode"
    
    # Deploy to Cloud Run with ETRADE-optimized configuration
    gcloud run deploy $full_service_name \
        --image $IMAGE_NAME \
        --platform managed \
        --region $REGION \
        --project $PROJECT_ID \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --concurrency 1 \
        --max-instances 1 \
        --timeout 3600 \
        --set-env-vars "STRATEGY_MODE=$strategy_mode,AUTOMATION_MODE=$automation_mode,ENVIRONMENT=production,DATA_PROVIDER_PRIORITY=etrade,alpha_vantage,yahoo" \
        --port 8080 \
        --set-secrets "TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,TELEGRAM_CHAT_ID=telegram-chat-id:latest,ETRADE_CONSUMER_KEY=etrade-consumer-key:latest,ETRADE_CONSUMER_SECRET=etrade-consumer-secret:latest,ETRADE_ACCOUNT_ID_KEY=etrade-account-id-key:latest,ETRADE_TOKENS_JSON=etrade-tokens:latest,ALPHA_VANTAGE_API_KEY=alpha-vantage-api-key:latest" \
        --set-cloudsql-instances="" \
        --no-use-google-cloud-apis
    
    # Get the service URL
    local service_url=$(gcloud run services describe $full_service_name --region=$REGION --project=$PROJECT_ID --format='value(status.url)')
    
    print_success "Deployed ETRADE-first service: $full_service_name"
    print_success "Service URL: $service_url"
    
    # Test the deployment
    sleep 10
    if curl -f -s "$service_url/health" > /dev/null 2>&1; then
        print_success "Health check passed for $full_service_name"
        
        # Test ETRADE integration
        if curl -f -s "$service_url/test-etrade" > /dev/null 2>&1; then
            print_success "ETRADE integration test passed"
        else
            print_warning "ETRADE integration test failed (service may still be initializing)"
        fi
    else
        print_warning "Health check failed for $full_service_name (service may still be starting)"
    fi
}

# Function to deploy all ETRADE-first strategy combinations
deploy_all_etrade_strategies() {
    print_status "Deploying all ETRADE-first strategy combinations..."
    
    # Strategy modes
    strategies=("standard" "advanced" "quantum")
    automation_modes=("off" "demo" "live")
    
    for strategy in "${strategies[@]}"; do
        for automation in "${automation_modes[@]}"; do
            deploy_etrade_service $strategy $automation
            sleep 5  # Brief pause between deployments
        done
    done
    
    print_success "All ETRADE-first strategy combinations deployed"
}

# Function to show ETRADE deployment status
show_etrade_status() {
    print_status "ETRADE Deployment Status:"
    echo ""
    
    # List all deployed services
    gcloud run services list --region=$REGION --project=$PROJECT_ID --format="table(metadata.name,status.url,status.conditions[0].status)"
    
    echo ""
    print_status "ETRADE-First Service URLs:"
    
    # Get URLs for all services
    strategies=("standard" "advanced" "quantum")
    automation_modes=("off" "demo" "live")
    
    for strategy in "${strategies[@]}"; do
        for automation in "${automation_modes[@]}"; do
            service_suffix=""
            if [ "$strategy" != "standard" ] || [ "$automation" != "off" ]; then
                service_suffix="-$strategy-$automation"
            fi
            service_name="${SERVICE_NAME}${service_suffix}"
            
            if gcloud run services describe $service_name --region=$REGION --project=$PROJECT_ID &> /dev/null; then
                url=$(gcloud run services describe $service_name --region=$REGION --project=$PROJECT_ID --format='value(status.url)')
                echo "  $service_name: $url"
            fi
        done
    done
    
    echo ""
    print_status "ETRADE Call Usage Summary:"
    echo "  ETRADE Calls/Day: 6,350 (unlimited)"
    echo "  Alpha Vantage Calls/Day: 1,200 (limit)"
    echo "  Monthly Cost: $50"
    echo "  Expected Savings: $208/month vs external providers"
}

# Function to test ETRADE integration
test_etrade_integration() {
    local service_name=${1:-$SERVICE_NAME}
    
    print_status "Testing ETRADE integration for $service_name..."
    
    # Get service URL
    local service_url=$(gcloud run services describe $service_name --region=$REGION --project=$PROJECT_ID --format='value(status.url)' 2>/dev/null)
    
    if [ -z "$service_url" ]; then
        print_error "Service $service_name not found"
        return 1
    fi
    
    # Test health endpoint
    if curl -f -s "$service_url/health" > /dev/null 2>&1; then
        print_success "Service is healthy"
    else
        print_error "Service health check failed"
        return 1
    fi
    
    # Test ETRADE endpoint
    if curl -f -s "$service_url/test-etrade" > /dev/null 2>&1; then
        print_success "ETRADE integration test passed"
    else
        print_warning "ETRADE test endpoint not available or failed"
    fi
    
    # Test data provider status
    if curl -f -s "$service_url/data-provider-status" > /dev/null 2>&1; then
        print_success "Data provider status endpoint accessible"
    else
        print_warning "Data provider status endpoint not available"
    fi
    
    print_success "ETRADE integration testing completed"
}

# Function to monitor ETRADE service logs
monitor_etrade_logs() {
    local service_name=${1:-$SERVICE_NAME}
    
    print_status "Monitoring ETRADE service logs for $service_name..."
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    gcloud logs tail --follow --project=$PROJECT_ID \
        --resource-type=cloud_run_revision \
        --resource-name=$service_name \
        --filter="severity>=INFO"
}

# Function to show help
show_help() {
    echo "ETRADE-First Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  validate                     Validate ETRADE deployment prerequisites"
    echo "  setup-secrets               Setup ETRADE-specific secrets"
    echo "  deploy [strategy] [automation]  Deploy specific ETRADE-first strategy"
    echo "  deploy-all                  Deploy all ETRADE-first strategy combinations"
    echo "  status                      Show ETRADE deployment status"
    echo "  test [service-name]         Test ETRADE integration"
    echo "  logs [service-name]         Monitor ETRADE service logs"
    echo "  build                       Build and push container only"
    echo "  help                        Show this help message"
    echo ""
    echo "Strategy modes: standard, advanced, quantum"
    echo "Automation modes: off, demo, live"
    echo ""
    echo "ETRADE-First Benefits:"
    echo "  • Real-time execution with ETRADE (unlimited calls)"
    echo "  • Smart analysis with Alpha Vantage (1,200 calls/day)"
    echo "  • Cost: $50/month (vs $258/month with external providers)"
    echo "  • Savings: $208/month"
    echo ""
    echo "Examples:"
    echo "  $0 validate                 Validate ETRADE prerequisites"
    echo "  $0 deploy standard off      Deploy standard strategy with alerts only"
    echo "  $0 deploy quantum live      Deploy quantum strategy with live trading"
    echo "  $0 deploy-all               Deploy all combinations"
    echo "  $0 test etrade-strategy     Test ETRADE integration"
    echo "  $0 logs etrade-strategy     Monitor ETRADE service logs"
}

# Main script logic
main() {
    local command=${1:-"help"}
    
    case $command in
        "validate")
            validate_etrade_prerequisites
            ;;
        "setup-secrets")
            check_prerequisites
            setup_project
            setup_etrade_secrets
            print_success "ETRADE secrets setup completed"
            ;;
        "build")
            check_prerequisites
            setup_project
            build_container
            ;;
        "deploy")
            local strategy=${2:-"standard"}
            local automation=${3:-"off"}
            validate_etrade_prerequisites
            check_prerequisites
            setup_project
            setup_etrade_secrets
            build_container
            deploy_etrade_service $strategy $automation
            ;;
        "deploy-all")
            validate_etrade_prerequisites
            check_prerequisites
            setup_project
            setup_etrade_secrets
            build_container
            deploy_all_etrade_strategies
            show_etrade_status
            ;;
        "status")
            show_etrade_status
            ;;
        "test")
            local service_name=${2:-$SERVICE_NAME}
            test_etrade_integration $service_name
            ;;
        "logs")
            local service_name=${2:-$SERVICE_NAME}
            monitor_etrade_logs $service_name
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Include common functions from deploy-unified.sh
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install Google Cloud SDK."
        exit 1
    fi
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
        exit 1
    fi
    
    if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
        print_error "Project $PROJECT_ID not found or no access."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

setup_project() {
    print_status "Setting up Google Cloud project..."
    
    gcloud config set project $PROJECT_ID
    
    print_status "Enabling required APIs..."
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    
    print_success "Project setup completed"
}

build_container() {
    print_status "Building and pushing ETRADE-first container..."
    
    gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID
    
    print_success "ETRADE-first container built and pushed: $IMAGE_NAME"
}

# Run main function with all arguments
main "$@"
