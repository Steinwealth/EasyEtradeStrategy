# 🔐 E*TRADE OAuth Token Management Guide - Easy ETrade Strategy

## Overview

The E*TRADE OAuth system is **critical** for continuous trading operations. E*TRADE tokens expire at **midnight ET every day** and require daily renewal to maintain uninterrupted trading. This comprehensive guide covers all aspects of OAuth token acquisition, management, and automated renewal.

## ⚠️ **CRITICAL: Daily Token Renewal Required**

### **Token Lifecycle Rules**
- **Daily Expiry**: E*TRADE tokens expire at **midnight ET every day**
- **Idle Timeout**: Tokens become inactive after **2 hours** of no API calls
- **Renewal Window**: Inactive tokens can be renewed (no re-authorization needed)
- **Expiration**: Expired tokens require full re-authentication

### **Why This Matters**
- **Trading Interruption**: Expired tokens will stop all trading operations
- **Position Risk**: Open positions cannot be managed without valid tokens
- **Data Access**: Market data and account information become unavailable
- **Revenue Loss**: Missed trading opportunities during token downtime

## 🏗️ OAuth Architecture

### **ETradeOAuth System Components**

```
ETradeOAuth/
├── etrade_oauth_manager.py          # Main OAuth manager
├── central_oauth_manager.py         # Advanced OAuth manager
├── simple_oauth_cli.py             # Simple CLI interface
├── token_loader.py                 # Integration utility
├── integration_example.py          # Usage examples
├── test_oauth_manager.py           # Test suite
├── README.md                       # Complete documentation
├── env_example.txt                 # Environment setup guide
├── tokens_sandbox.json             # Sandbox tokens
├── tokens_prod.json                # Production tokens
└── etrade_oauth.log                # Operation logs
```

### **OAuth Flow Types**

#### **1. Simple OAuth Flow (Recommended)**
- **File**: `simple_oauth_cli.py`
- **Use Case**: Daily token renewal, testing
- **Features**: Easy-to-use CLI interface
- **Best For**: Manual daily operations

#### **2. Central OAuth Manager (Advanced)**
- **File**: `central_oauth_manager.py`
- **Use Case**: Production automation, cloud deployment
- **Features**: Advanced token management, error handling
- **Best For**: Automated systems, cloud services

#### **3. Integration Utility (Development)**
- **File**: `token_loader.py`
- **Use Case**: Application integration
- **Features**: Clean interface for trading system
- **Best For**: Development and testing

## 🔧 Initial Setup

### **1. Environment Configuration**

```bash
# Navigate to OAuth directory
cd ETradeOAuth

# Copy environment template
cp env_example.txt .env

# Edit environment file
nano .env
```

#### **Environment Variables (.env)**
```env
# E*TRADE API Credentials
ETRADE_SANDBOX_KEY=your_sandbox_consumer_key
ETRADE_SANDBOX_SECRET=your_sandbox_consumer_secret
ETRADE_PROD_KEY=your_production_consumer_key
ETRADE_PROD_SECRET=your_production_consumer_secret

# OAuth Configuration
ETRADE_OAUTH_CALLBACK_URL=http://localhost:8080/oauth/callback
ETRADE_TOKEN_STORAGE_PATH=./tokens/
ETRADE_LOG_LEVEL=INFO

# Environment Selection
ETRADE_ENVIRONMENT=sandbox  # or 'production'
```

### **2. E*TRADE API Credentials Setup**

#### **Sandbox Credentials (Testing)**
1. Visit [E*TRADE Developer Portal](https://developer.etrade.com/)
2. Create a new application
3. Select "Sandbox" environment
4. Copy Consumer Key and Consumer Secret
5. Set callback URL: `http://localhost:8080/oauth/callback`

#### **Production Credentials (Live Trading)**
1. Complete E*TRADE application process
2. Submit for production approval
3. Receive production Consumer Key and Consumer Secret
4. Update environment variables

### **3. Initial Token Acquisition**

#### **Sandbox Environment**
```bash
# Get fresh tokens (run daily after midnight ET)
python3 simple_oauth_cli.py start sandbox

# Test API connection
python3 simple_oauth_cli.py test sandbox

# Check token status
python3 simple_oauth_cli.py status
```

#### **Production Environment**
```bash
# Get fresh tokens (run daily after midnight ET)
python3 simple_oauth_cli.py start production

# Test API connection
python3 simple_oauth_cli.py test production

# Check token status
python3 simple_oauth_cli.py status
```

## 🔄 Daily Token Management

### **Daily Routine (CRITICAL)**

#### **Morning Routine (After Midnight ET)**
```bash
# 1. Navigate to OAuth directory
cd ETradeOAuth

# 2. Get fresh tokens (REQUIRED DAILY)
python3 simple_oauth_cli.py start sandbox

# 3. Test connection
python3 simple_oauth_cli.py test sandbox

# 4. Start keepalive (RECOMMENDED)
python3 simple_oauth_cli.py keepalive sandbox --minutes 70
```

#### **During Trading Hours**
```bash
# Keep tokens alive (run every 70 minutes)
python3 simple_oauth_cli.py keepalive sandbox --minutes 70

# Or run continuously
python3 simple_oauth_cli.py keepalive sandbox --continuous
```

#### **Evening Routine**
```bash
# Check token status
python3 simple_oauth_cli.py status

# Tokens will expire at midnight ET
# System will warn you to re-authenticate
```

### **Automated Daily Renewal**

#### **Cron Job Setup (Linux/Mac)**
```bash
# Edit crontab
crontab -e

# Add daily renewal at 12:05 AM ET (5:05 AM UTC)
5 5 * * * cd /path/to/ETradeOAuth && python3 simple_oauth_cli.py start sandbox >> /var/log/etrade_oauth.log 2>&1

# Add keepalive every 70 minutes during trading hours (9:30 AM - 4:00 PM ET)
*/70 14-20 * * 1-5 cd /path/to/ETradeOAuth && python3 simple_oauth_cli.py keepalive sandbox --minutes 70 >> /var/log/etrade_oauth.log 2>&1
```

#### **Windows Task Scheduler**
```batch
# Create batch file: daily_oauth_renewal.bat
@echo off
cd /d C:\path\to\ETradeOAuth
python3 simple_oauth_cli.py start sandbox
python3 simple_oauth_cli.py test sandbox
```

### **Cloud Deployment Automation**

#### **Google Cloud Run OAuth Service**
```yaml
# cloudrun-oauth.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: etrade-strategy-oauth
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/execution-environment: gen2
    spec:
      containers:
        - name: etrade-oauth
          image: gcr.io/project/etrade-strategy:latest
          command: ["python", "ETradeOAuth/etrade_oauth_manager.py"]
          args: ["keepalive", "production", "--minutes", "70"]
          env:
            - name: ETRADE_CONSUMER_KEY
              valueFrom:
                secretKeyRef:
                  name: etrade-consumer-key
                  key: latest
            - name: ETRADE_CONSUMER_SECRET
              valueFrom:
                secretKeyRef:
                  name: etrade-consumer-secret
                  key: latest
```

## 🔧 OAuth Manager Commands

### **Simple OAuth CLI Commands**

#### **Token Management**
```bash
# Start OAuth flow (get fresh tokens)
python3 simple_oauth_cli.py start {sandbox|prod}

# Renew existing tokens (keeps alive for 2+ hours)
python3 simple_oauth_cli.py renew {sandbox|prod}

# Test API connection
python3 simple_oauth_cli.py test {sandbox|prod}

# Check token status for all environments
python3 simple_oauth_cli.py status

# Keep tokens alive during trading hours
python3 simple_oauth_cli.py keepalive {sandbox|prod} [--minutes 70] [--continuous]
```

#### **Advanced Commands**
```bash
# Get detailed token information
python3 simple_oauth_cli.py info {sandbox|prod}

# Validate token without API call
python3 simple_oauth_cli.py validate {sandbox|prod}

# Clear stored tokens
python3 simple_oauth_cli.py clear {sandbox|prod}

# Show help
python3 simple_oauth_cli.py --help
```

### **Central OAuth Manager Commands**

#### **Advanced Token Management**
```bash
# Start OAuth flow with advanced options
python3 central_oauth_manager.py start sandbox --verbose --log-level DEBUG

# Renew tokens with error handling
python3 central_oauth_manager.py renew sandbox --retry 3 --timeout 30

# Test with comprehensive validation
python3 central_oauth_manager.py test sandbox --validate-all

# Monitor token health
python3 central_oauth_manager.py monitor sandbox --interval 60
```

## 📊 Token Status Monitoring

### **Token Status Check**

```bash
# Check all environments
python3 simple_oauth_cli.py status

# Output example:
# Environment: sandbox
# Status: ACTIVE
# Expires: 2024-01-16 00:00:00 ET
# Last Used: 2024-01-15 14:32:15 ET
# API Calls Today: 1,180
# 
# Environment: production
# Status: EXPIRED
# Expires: 2024-01-15 00:00:00 ET
# Last Used: 2024-01-14 16:45:30 ET
# API Calls Today: 0
```

### **Token Health Indicators**

#### **Healthy Token**
- **Status**: ACTIVE
- **Expires**: Future date/time
- **Last Used**: Recent (within 2 hours)
- **API Calls**: Normal usage pattern

#### **Expiring Token**
- **Status**: EXPIRING_SOON
- **Expires**: Within 1 hour
- **Last Used**: Recent
- **Action Required**: Renew immediately

#### **Expired Token**
- **Status**: EXPIRED
- **Expires**: Past date/time
- **Last Used**: Old
- **Action Required**: Full re-authentication

#### **Inactive Token**
- **Status**: INACTIVE
- **Expires**: Future date/time
- **Last Used**: >2 hours ago
- **Action Required**: Renew to reactivate

## 🔄 Token Renewal Process

### **Automatic Renewal (Recommended)**

#### **Renewal Triggers**
- **Daily Schedule**: Every day at 12:05 AM ET
- **Idle Detection**: When token hasn't been used for 1.5 hours
- **Expiry Warning**: 1 hour before token expires
- **Error Recovery**: When API calls fail due to token issues

#### **Renewal Process**
```python
# Automatic renewal logic
def auto_renew_tokens():
    """Automatically renew tokens when needed"""
    
    # Check if renewal is needed
    if needs_renewal():
        try:
            # Attempt renewal
            result = renew_tokens()
            if result.success:
                log.info("Tokens renewed successfully")
                return True
            else:
                log.error(f"Token renewal failed: {result.error}")
                return False
        except Exception as e:
            log.error(f"Token renewal exception: {e}")
            return False
    
    return True
```

### **Manual Renewal**

#### **When to Renew Manually**
- **Token Expiry**: When tokens are about to expire
- **API Errors**: When getting 401 Unauthorized errors
- **Trading Issues**: When trading operations fail
- **Preventive**: Before important trading sessions

#### **Manual Renewal Steps**
```bash
# 1. Check current status
python3 simple_oauth_cli.py status

# 2. Renew if needed
python3 simple_oauth_cli.py renew sandbox

# 3. Test connection
python3 simple_oauth_cli.py test sandbox

# 4. Verify in trading system
python3 -c "from modules.etrade_oauth_integration import get_etrade_oauth_integration; print('OAuth OK' if get_etrade_oauth_integration('sandbox').is_authenticated() else 'OAuth FAILED')"
```

## 🚨 Error Handling & Recovery

### **Common OAuth Errors**

#### **1. Token Expired Error**
```python
# Error: 401 Unauthorized - Token expired
# Solution: Full re-authentication required
python3 simple_oauth_cli.py start sandbox
```

#### **2. Invalid Token Error**
```python
# Error: 401 Unauthorized - Invalid token
# Solution: Clear and re-authenticate
python3 simple_oauth_cli.py clear sandbox
python3 simple_oauth_cli.py start sandbox
```

#### **3. Rate Limit Error**
```python
# Error: 429 Too Many Requests
# Solution: Wait and retry with backoff
python3 simple_oauth_cli.py renew sandbox --retry 3 --backoff 60
```

#### **4. Network Error**
```python
# Error: Connection timeout
# Solution: Check network and retry
python3 simple_oauth_cli.py test sandbox --timeout 30
```

### **Recovery Procedures**

#### **Complete Token Reset**
```bash
# 1. Clear all stored tokens
python3 simple_oauth_cli.py clear sandbox
python3 simple_oauth_cli.py clear production

# 2. Re-authenticate both environments
python3 simple_oauth_cli.py start sandbox
python3 simple_oauth_cli.py start production

# 3. Test both environments
python3 simple_oauth_cli.py test sandbox
python3 simple_oauth_cli.py test production

# 4. Verify integration
python3 -c "from modules.etrade_oauth_integration import get_etrade_oauth_integration; print('Integration OK')"
```

#### **Emergency Token Recovery**
```bash
# Emergency script for token recovery
#!/bin/bash
echo "Starting emergency token recovery..."

# Stop trading system
pkill -f "main.py"

# Clear tokens
cd ETradeOAuth
python3 simple_oauth_cli.py clear sandbox
python3 simple_oauth_cli.py clear production

# Re-authenticate
python3 simple_oauth_cli.py start sandbox
python3 simple_oauth_cli.py start production

# Test connections
python3 simple_oauth_cli.py test sandbox
python3 simple_oauth_cli.py test production

# Restart trading system
cd ..
python3 main.py --strategy-mode standard --automation-mode live &

echo "Emergency recovery complete"
```

## 🔐 Security Best Practices

### **Token Storage Security**

#### **File Permissions**
```bash
# Secure token files
chmod 600 tokens_sandbox.json
chmod 600 tokens_prod.json
chmod 600 .env

# Restrict directory access
chmod 700 ETradeOAuth/
```

#### **Encryption at Rest**
```python
# Encrypt token files
from cryptography.fernet import Fernet

def encrypt_tokens(token_data, key):
    """Encrypt token data before storage"""
    f = Fernet(key)
    encrypted_data = f.encrypt(json.dumps(token_data).encode())
    return encrypted_data

def decrypt_tokens(encrypted_data, key):
    """Decrypt token data for use"""
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data)
    return json.loads(decrypted_data.decode())
```

### **Access Control**

#### **Environment Separation**
- **Sandbox Tokens**: Only for testing and development
- **Production Tokens**: Only for live trading
- **Separate Storage**: Different files for each environment
- **Access Logging**: Log all token access and modifications

#### **Audit Trail**
```python
# Log all OAuth operations
import logging

oauth_logger = logging.getLogger('etrade_oauth')
oauth_logger.setLevel(logging.INFO)

def log_oauth_operation(operation, environment, success, details=None):
    """Log OAuth operations for audit trail"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'operation': operation,
        'environment': environment,
        'success': success,
        'details': details
    }
    oauth_logger.info(json.dumps(log_data))
```

## 📱 Integration with Trading System

### **OAuth Integration in Trading Code**

#### **Token Loader Integration**
```python
# In your trading code
from modules.etrade_oauth_integration import get_etrade_oauth_integration

# Get OAuth integration
oauth_integration = get_etrade_oauth_integration('sandbox')

# Check authentication status
if oauth_integration.is_authenticated():
    # Make API calls
    accounts = oauth_integration.get_accounts()
    result = oauth_integration.make_api_call('/v1/accounts/list')
else:
    print("Please run: cd ETradeOAuth && python3 simple_oauth_cli.py start sandbox")
```

#### **Automatic Token Refresh**
```python
# Automatic token refresh in trading system
class ETradeTradingManager:
    def __init__(self):
        self.oauth = get_etrade_oauth_integration('sandbox')
        self.last_token_check = datetime.now()
    
    def ensure_authenticated(self):
        """Ensure OAuth tokens are valid before trading"""
        if not self.oauth.is_authenticated():
            # Attempt to renew tokens
            if self.oauth.renew_tokens():
                log.info("Tokens renewed successfully")
            else:
                log.error("Token renewal failed - stopping trading")
                raise AuthenticationError("Unable to authenticate with E*TRADE")
    
    def make_trading_call(self, endpoint, data=None):
        """Make trading API call with automatic token refresh"""
        self.ensure_authenticated()
        return self.oauth.make_api_call(endpoint, data)
```

### **Health Monitoring Integration**

#### **OAuth Health Check**
```python
# Health check endpoint
@app.route('/health/oauth')
def oauth_health_check():
    """Check OAuth token health"""
    try:
        oauth = get_etrade_oauth_integration('sandbox')
        
        if oauth.is_authenticated():
            # Check token expiry
            expires_at = oauth.get_token_expiry()
            time_to_expiry = expires_at - datetime.now()
            
            if time_to_expiry.total_seconds() < 3600:  # Less than 1 hour
                return {
                    'status': 'warning',
                    'message': f'Tokens expire in {time_to_expiry}',
                    'expires_at': expires_at.isoformat()
                }
            else:
                return {
                    'status': 'healthy',
                    'message': 'OAuth tokens are valid',
                    'expires_at': expires_at.isoformat()
                }
        else:
            return {
                'status': 'error',
                'message': 'OAuth tokens are invalid or expired'
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'OAuth health check failed: {str(e)}'
        }
```

## 🚀 Cloud Deployment OAuth

### **Google Cloud Run OAuth Service**

#### **OAuth Service Configuration**
```yaml
# cloudrun-oauth.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: etrade-strategy-oauth
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/execution-environment: gen2
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containers:
        - name: etrade-oauth
          image: gcr.io/project/etrade-strategy:latest
          command: ["python", "ETradeOAuth/central_oauth_manager.py"]
          args: ["monitor", "production", "--interval", "60", "--auto-renew"]
          env:
            - name: ETRADE_CONSUMER_KEY
              valueFrom:
                secretKeyRef:
                  name: etrade-consumer-key
                  key: latest
            - name: ETRADE_CONSUMER_SECRET
              valueFrom:
                secretKeyRef:
                  name: etrade-consumer-secret
                  key: latest
          resources:
            limits:
              cpu: "1"
              memory: "1Gi"
```

#### **Cloud Scheduler for Daily Renewal**
```yaml
# cloudscheduler-oauth.yaml
apiVersion: cloud.google.com/v1
kind: CloudSchedulerJob
metadata:
  name: etrade-oauth-daily-renewal
spec:
  schedule: "5 5 * * *"  # 12:05 AM ET daily
  timeZone: "America/New_York"
  httpTarget:
    uri: "https://etrade-strategy-oauth-xxxxx-uc.a.run.app/renew"
    httpMethod: POST
    headers:
      Content-Type: "application/json"
    body: |
      {
        "environment": "production",
        "auto_test": true
      }
```

### **Docker OAuth Service**

#### **Dockerfile for OAuth Service**
```dockerfile
# Dockerfile.oauth
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy OAuth code
COPY ETradeOAuth/ ./ETradeOAuth/
COPY modules/ ./modules/

# Set up OAuth service
WORKDIR /app/ETradeOAuth

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 simple_oauth_cli.py status || exit 1

# Default command
CMD ["python3", "central_oauth_manager.py", "monitor", "production", "--interval", "60"]
```

## 📊 Monitoring & Alerting

### **OAuth Monitoring Metrics**

#### **Key Metrics to Track**
- **Token Expiry Time**: Time until token expiration
- **Token Renewal Success Rate**: Percentage of successful renewals
- **API Call Success Rate**: Percentage of successful API calls
- **Token Refresh Frequency**: How often tokens are refreshed
- **Authentication Errors**: Number of authentication failures

#### **Alerting Rules**
```yaml
# oauth-alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: etrade-oauth-alerts
spec:
  groups:
  - name: etrade-oauth
    rules:
    - alert: TokenExpiringSoon
      expr: etrade_token_expiry_seconds < 3600
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "E*TRADE token expiring soon"
        description: "Token expires in {{ $value }} seconds"
    
    - alert: TokenExpired
      expr: etrade_token_expiry_seconds < 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "E*TRADE token expired"
        description: "Trading operations will fail"
    
    - alert: TokenRenewalFailed
      expr: rate(etrade_token_renewal_failures[5m]) > 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "E*TRADE token renewal failed"
        description: "Token renewal failure rate is {{ $value }}"
    
    - alert: HighAPIFailureRate
      expr: rate(etrade_api_failures[5m]) / rate(etrade_api_calls[5m]) > 0.1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High E*TRADE API failure rate"
        description: "API failure rate is {{ $value }}"
```

### **Telegram OAuth Alerts**

#### **OAuth Status Notifications**
```python
# OAuth status notifications
def send_oauth_alert(message, level="info"):
    """Send OAuth status alert to Telegram"""
    alert_data = {
        "level": level,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "service": "etrade_oauth"
    }
    
    # Send to Telegram
    send_telegram_alert(f"🔐 OAuth Alert: {message}", level)

# Usage examples
send_oauth_alert("Tokens renewed successfully", "success")
send_oauth_alert("Token renewal failed - manual intervention required", "error")
send_oauth_alert("Tokens expire in 1 hour", "warning")
```

## 🎯 Best Practices

### **Daily Operations**

#### **Morning Checklist**
1. **Check Token Status**: Verify tokens are active
2. **Renew if Needed**: Get fresh tokens if expired
3. **Test Connection**: Verify API connectivity
4. **Start Keepalive**: Begin token maintenance
5. **Monitor Alerts**: Watch for OAuth issues

#### **Evening Checklist**
1. **Check Token Health**: Verify tokens are still valid
2. **Review Logs**: Check for any OAuth errors
3. **Prepare for Renewal**: Ensure renewal process is ready
4. **Backup Tokens**: Save current token state

### **Error Prevention**

#### **Proactive Measures**
- **Automated Renewal**: Set up automatic daily renewal
- **Health Monitoring**: Continuous token health checks
- **Alerting**: Immediate notification of OAuth issues
- **Backup Procedures**: Recovery plans for token failures

#### **Redundancy**
- **Multiple Renewal Methods**: Both manual and automated
- **Fallback Procedures**: Alternative authentication methods
- **Emergency Contacts**: Quick access to OAuth support
- **Documentation**: Clear procedures for all scenarios

### **Security**

#### **Token Protection**
- **Secure Storage**: Encrypted token files
- **Access Control**: Limited access to OAuth credentials
- **Audit Logging**: Complete OAuth operation logs
- **Regular Rotation**: Periodic credential updates

#### **Environment Separation**
- **Sandbox vs Production**: Clear separation of environments
- **Different Credentials**: Separate API keys for each environment
- **Isolated Storage**: Separate token files for each environment
- **Independent Monitoring**: Separate monitoring for each environment

## 🚨 Emergency Procedures

### **Token Emergency Recovery**

#### **Complete System Failure**
```bash
# 1. Stop all trading operations
pkill -f "main.py"
pkill -f "scanner"

# 2. Emergency token renewal
cd ETradeOAuth
python3 simple_oauth_cli.py clear sandbox
python3 simple_oauth_cli.py clear production
python3 simple_oauth_cli.py start sandbox
python3 simple_oauth_cli.py start production

# 3. Test all connections
python3 simple_oauth_cli.py test sandbox
python3 simple_oauth_cli.py test production

# 4. Restart trading system
cd ..
python3 main.py --strategy-mode standard --automation-mode live
```

#### **Partial Token Failure**
```bash
# 1. Identify failed environment
python3 simple_oauth_cli.py status

# 2. Renew specific environment
python3 simple_oauth_cli.py renew sandbox  # or production

# 3. Test specific environment
python3 simple_oauth_cli.py test sandbox

# 4. Verify trading system
python3 -c "from modules.etrade_oauth_integration import get_etrade_oauth_integration; print('OK' if get_etrade_oauth_integration('sandbox').is_authenticated() else 'FAILED')"
```

### **Contact Information**

#### **E*TRADE Support**
- **Developer Portal**: https://developer.etrade.com/
- **API Support**: api-support@etrade.com
- **Emergency Line**: 1-800-ETRADE-1

#### **Internal Support**
- **System Administrator**: admin@yourcompany.com
- **Trading Team**: trading@yourcompany.com
- **Emergency Contact**: +1-XXX-XXX-XXXX

---

**E*TRADE OAuth Token Management Guide - Complete and Ready for Production!** 🔐

*For Google Cloud deployment details, see [Cloud.md](Cloud.md)*  
*For trading strategy details, see [Strategy.md](Strategy.md)*  
*For system configuration, see [Settings.md](Settings.md)*
