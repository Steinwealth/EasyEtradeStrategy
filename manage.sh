#!/bin/bash
# ETrade Strategy Management Script
# Unified script for deployment, monitoring, and management

set -e

# Configuration
PROJECT_ID="odin-187104"
REGION="us-west2"
SERVICE_NAME="etrade-strategy"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Strategy modes to deploy
STRATEGIES=("standard" "advanced" "quantum")
AUTOMATION_MODES=("off" "demo" "live")

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install Google Cloud SDK."
        exit 1
    fi
    
    # Check if user is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
        exit 1
    fi
    
    # Check if project exists
    if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
        print_error "Project $PROJECT_ID not found or no access."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to setup Google Cloud project
setup_project() {
    print_status "Setting up Google Cloud project..."
    
    # Set the project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    print_status "Enabling required APIs..."
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    
    print_success "Project setup completed"
}

# Function to create secrets
create_secrets() {
    print_status "Creating secrets in Google Secret Manager..."
    
    # List of secrets to create
    declare -A secrets=(
        ["telegram-bot-token"]="TELEGRAM_BOT_TOKEN"
        ["telegram-chat-id"]="TELEGRAM_CHAT_ID"
        ["etrade-consumer-key"]="ETRADE_CONSUMER_KEY"
        ["etrade-consumer-secret"]="ETRADE_CONSUMER_SECRET"
        ["etrade-account-id-key"]="ETRADE_ACCOUNT_ID_KEY"
        ["polygon-api-key"]="POLYGON_API_KEY"
        ["alpha-vantage-api-key"]="ALPHA_VANTAGE_API_KEY"
    )
    
    for secret_name in "${!secrets[@]}"; do
        env_var="${secrets[$secret_name]}"
        
        # Check if secret exists
        if gcloud secrets describe $secret_name --project=$PROJECT_ID &> /dev/null; then
            print_warning "Secret $secret_name already exists"
        else
            # Create secret
            print_status "Creating secret: $secret_name"
            echo "placeholder" | gcloud secrets create $secret_name --data-file=- --project=$PROJECT_ID
            
            print_warning "Please update the secret value for $secret_name:"
            echo "gcloud secrets versions add $secret_name --data-file=- --project=$PROJECT_ID"
        fi
    done
    
    print_success "Secrets setup completed"
}

# Function to build and push container
build_container() {
    print_status "Building and pushing container..."
    
    # Build the container
    gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID
    
    print_success "Container built and pushed: $IMAGE_NAME"
}

# Function to deploy service
deploy_service() {
    local strategy_mode=$1
    local automation_mode=$2
    local service_suffix=""
    
    # Create service name suffix for different modes
    if [ "$strategy_mode" != "standard" ] || [ "$automation_mode" != "off" ]; then
        service_suffix="-$strategy_mode-$automation_mode"
    fi
    
    local full_service_name="${SERVICE_NAME}${service_suffix}"
    
    print_status "Deploying $full_service_name (strategy: $strategy_mode, automation: $automation_mode)..."
    
    # Deploy to Cloud Run
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
        --set-env-vars "STRATEGY_MODE=$strategy_mode,AUTOMATION_MODE=$automation_mode,ENVIRONMENT=production" \
        --port 8080 \
        --set-secrets "TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,TELEGRAM_CHAT_ID=telegram-chat-id:latest,ETRADE_CONSUMER_KEY=etrade-consumer-key:latest,ETRADE_CONSUMER_SECRET=etrade-consumer-secret:latest,ETRADE_ACCOUNT_ID_KEY=etrade-account-id-key:latest,POLYGON_API_KEY=polygon-api-key:latest,ALPHA_VANTAGE_API_KEY=alpha-vantage-api-key:latest"
    
    # Get the service URL
    local service_url=$(gcloud run services describe $full_service_name --region=$REGION --project=$PROJECT_ID --format='value(status.url)')
    
    print_success "Deployed $full_service_name"
    print_success "Service URL: $service_url"
    
    # Test the deployment
    sleep 10
    if curl -f -s "$service_url/health" > /dev/null 2>&1; then
        print_success "Health check passed for $full_service_name"
    else
        print_warning "Health check failed for $full_service_name (service may still be starting)"
    fi
}

# Function to deploy all strategy combinations
deploy_all_strategies() {
    print_status "Deploying all strategy combinations..."
    
    for strategy in "${STRATEGIES[@]}"; do
        for automation in "${AUTOMATION_MODES[@]}"; do
            deploy_service $strategy $automation
            sleep 5  # Brief pause between deployments
        done
    done
    
    print_success "All strategy combinations deployed"
}

# Function to show deployment status
show_status() {
    print_status "Deployment Status:"
    echo ""
    
    # List all deployed services
    gcloud run services list --region=$REGION --project=$PROJECT_ID --format="table(metadata.name,status.url,status.conditions[0].status)"
    
    echo ""
    print_status "Service URLs:"
    
    # Get URLs for all services
    for strategy in "${STRATEGIES[@]}"; do
        for automation in "${AUTOMATION_MODES[@]}"; do
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
}

# Function to monitor logs
monitor_logs() {
    local service_name=${1:-$SERVICE_NAME}
    
    print_status "Monitoring logs for $service_name..."
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    gcloud logs tail --follow --project=$PROJECT_ID --resource-type=cloud_run_revision --resource-name=$service_name
}

# Function to get Telegram chat IDs
get_telegram_ids() {
    print_status "Getting Telegram chat IDs..."
    
    # Check if telegram bot token is available
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        print_warning "TELEGRAM_BOT_TOKEN not set. Please set it in your environment or secrets."
        return 1
    fi
    
    print_status "Send a message to your bot and then run:"
    echo "curl -s \"https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates\" | jq '.result[].message.chat.id'"
}

# Function to test Telegram integration
test_telegram() {
    local service_name=${1:-$SERVICE_NAME}
    
    print_status "Testing Telegram integration for $service_name..."
    
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
    
    # Test telegram endpoint if available
    if curl -f -s "$service_url/test-telegram" > /dev/null 2>&1; then
        print_success "Telegram integration test passed"
    else
        print_warning "Telegram test endpoint not available or failed"
    fi
}

# Function to create configuration files
create_configs() {
    print_status "Creating configuration files..."
    
    # Create base configuration if it doesn't exist
    if [ ! -f "configs/base.env" ]; then
        print_status "Creating base.env template..."
        cat > configs/base.env << EOF
# Base Configuration
STRATEGY_MODE=standard
AUTOMATION_MODE=off
ENVIRONMENT=development

# Data Sources
POLYGON_API_KEY=your_polygon_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# ETrade Configuration
ETRADE_CONSUMER_KEY=your_consumer_key_here
ETRADE_CONSUMER_SECRET=your_consumer_secret_here
ETRADE_ACCOUNT_ID_KEY=your_account_id_key_here
EOF
        print_success "Created configs/base.env template"
    fi
    
    # Create other config templates
    for config in alerts automation data-providers deployment strategies; do
        if [ ! -f "configs/${config}.env" ]; then
            print_status "Creating ${config}.env template..."
            touch "configs/${config}.env"
            print_success "Created configs/${config}.env"
        fi
    done
    
    print_success "Configuration files created"
}

# Function to show help
show_help() {
    echo "ETrade Strategy Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  deploy [strategy] [automation]  Deploy specific strategy/automation combination"
    echo "  deploy-all                     Deploy all strategy combinations"
    echo "  status                         Show deployment status"
    echo "  logs [service-name]            Monitor logs for service"
    echo "  setup                          Setup Google Cloud project and secrets"
    echo "  build                          Build and push container only"
    echo "  create-configs                 Create configuration file templates"
    echo "  get-telegram-ids               Get Telegram chat IDs"
    echo "  test-telegram [service-name]   Test Telegram integration"
    echo "  help                           Show this help message"
    echo ""
    echo "Strategy modes: standard, advanced, quantum"
    echo "Automation modes: off, demo, live"
    echo ""
    echo "Examples:"
    echo "  $0 deploy standard off         Deploy standard strategy with alerts only"
    echo "  $0 deploy quantum live         Deploy quantum strategy with live trading"
    echo "  $0 deploy-all                  Deploy all combinations"
    echo "  $0 logs etrade-strategy        Monitor logs for main service"
    echo "  $0 create-configs              Create configuration templates"
    echo "  $0 test-telegram               Test Telegram integration"
}

# Main script logic
main() {
    local command=${1:-"help"}
    
    case $command in
        "setup")
            check_prerequisites
            setup_project
            create_secrets
            print_success "Setup completed. Please update secret values before deploying."
            ;;
        "build")
            check_prerequisites
            setup_project
            build_container
            ;;
        "deploy")
            local strategy=${2:-"standard"}
            local automation=${3:-"off"}
            check_prerequisites
            setup_project
            build_container
            deploy_service $strategy $automation
            ;;
        "deploy-all")
            check_prerequisites
            setup_project
            build_container
            deploy_all_strategies
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            local service_name=${2:-$SERVICE_NAME}
            monitor_logs $service_name
            ;;
        "create-configs")
            create_configs
            ;;
        "get-telegram-ids")
            get_telegram_ids
            ;;
        "test-telegram")
            local service_name=${2:-$SERVICE_NAME}
            test_telegram $service_name
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
