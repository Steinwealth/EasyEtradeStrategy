# ETrade OAuth Web App

A mobile-friendly web application for managing E*TRADE OAuth tokens with daily renewal capabilities.

## Overview

This FastAPI application provides a streamlined interface for:
- Managing E*TRADE consumer keys and secrets
- Daily OAuth token renewal via PIN-based flow
- Telegram notifications for morning token renewal
- Integration with Google Cloud Secret Manager and Pub/Sub

## Features

- **Mobile-Optimized UI**: Responsive design for easy mobile access
- **PIN-Based OAuth Flow**: Secure token renewal without complex redirects
- **Cloud Integration**: Uses GCP Secret Manager for secure credential storage
- **Automated Notifications**: Telegram alerts for daily token renewal
- **Hot-Reload Support**: Pub/Sub integration for instant token updates

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud Project with required APIs enabled
- E*TRADE API consumer keys
- Telegram bot token and chat ID

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export GCP_PROJECT="your-gcp-project-id"
export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
export TELEGRAM_CHAT_ID="your-telegram-chat-id"
export APP_BASE_URL="http://localhost:8080"
```

3. Run the application:
```bash
uvicorn oauth_web_app:app --host 0.0.0.0 --port 8080
```

### Google Cloud Deployment

1. Make the deployment script executable:
```bash
chmod +x deploy.sh
```

2. Set your GCP project:
```bash
export GCP_PROJECT="your-gcp-project-id"
```

3. Deploy to Cloud Run:
```bash
./deploy.sh
```

## API Endpoints

### Admin Interface
- `GET /admin/secrets` - View/manage consumer keys and secrets
- `POST /admin/secrets` - Save consumer keys and secrets

### OAuth Flow
- `GET /oauth/start?env=prod` - Start OAuth PIN flow
- `POST /oauth/verify` - Verify PIN and generate access tokens

### Automation
- `GET /cron/morning-alert` - Send Telegram morning alert (for Cloud Scheduler)
- `GET /healthz` - Health check endpoint

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GCP_PROJECT` | Google Cloud Project ID | Yes |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Yes |
| `TELEGRAM_CHAT_ID` | Telegram chat ID for notifications | Yes |
| `APP_BASE_URL` | Base URL of the deployed application | Yes |
| `PUBSUB_TOPIC` | Pub/Sub topic for token updates | No |

### Secret Manager Secrets

The application expects the following secrets in Google Cloud Secret Manager:

- `etrade/prod/consumer_key`
- `etrade/prod/consumer_secret`
- `etrade/prod/access_token`
- `etrade/prod/access_token_secret`
- `etrade/sandbox/consumer_key`
- `etrade/sandbox/consumer_secret`
- `etrade/sandbox/access_token`
- `etrade/sandbox/access_token_secret`

## Cloud Scheduler Setup

Set up a Cloud Scheduler job to call the morning alert endpoint:

- **Target**: `GET https://your-app-url/cron/morning-alert`
- **Schedule**: `30 8 * * 1-5` (8:30 AM ET, Monday-Friday)
- **Time Zone**: `America/New_York`

## Security Features

- Consumer keys and secrets are masked in the UI (shows first 4 characters + bullets)
- All sensitive data stored in Google Cloud Secret Manager
- OAuth tokens are never displayed in full
- CORS enabled for cross-origin requests

## Mobile Usage

1. Receive Telegram alert in the morning
2. Tap the authorization link
3. Open E*TRADE in browser and approve
4. Copy the 6-digit PIN
5. Paste PIN in the web form
6. Tokens are automatically updated and propagated

## Integration with Trading Service

The application publishes token updates to a Pub/Sub topic. Your trading service should:

1. Subscribe to the `token-rotated` topic
2. Pull new tokens from Secret Manager when notified
3. Update in-memory credentials without restart

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify consumer keys are correct in Secret Manager
2. **Permission Denied**: Ensure the service account has Secret Manager access
3. **Telegram Notifications**: Check bot token and chat ID configuration
4. **OAuth Flow Fails**: Verify E*TRADE API endpoints and consumer key validity

### Logs

View application logs in Google Cloud Console:
- Go to Cloud Run → etrade-oauth-web → Logs
- Filter by severity level and time range

## Development

### Project Structure

```
login/
├── oauth_web_app.py      # Main FastAPI application
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
├── .dockerignore        # Docker ignore patterns
├── cloudbuild.yaml      # Cloud Build configuration
├── deploy.sh           # Deployment script
└── README.md           # This file
```

### Adding Features

1. Modify `oauth_web_app.py` for new endpoints
2. Update `requirements.txt` for new dependencies
3. Test locally with `uvicorn oauth_web_app:app --reload`
4. Deploy with `./deploy.sh`

## Support

For issues and questions:
1. Check the logs in Google Cloud Console
2. Verify Secret Manager configuration
3. Test OAuth flow manually
4. Review Cloud Scheduler job status
