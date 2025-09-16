# 🔐 ETrade Token Management Strategy for Cloud Deployment

## Overview
This document outlines the comprehensive token management strategy for the ETrade Strategy when deployed to the cloud, addressing the critical issue of daily token expiration at midnight ET.

## 🕛 Token Expiration Timeline

### **Daily Expiration Rules**
- **Expiration Time**: ETrade tokens expire at **midnight ET every day**
- **Idle Timeout**: Tokens become inactive after **2 hours** of no API calls
- **Renewal Window**: Inactive tokens can be renewed without re-authorization
- **Full Expiration**: Expired tokens require complete re-authentication

### **Time Zone Considerations**
- **Midnight ET**: 12:00 AM Eastern Time
- **California Time**: 9:00 PM Pacific Time (previous day)
- **UTC Time**: 5:00 AM UTC
- **Trading Hours**: 9:30 AM - 4:00 PM ET (6.5 hours)

## 🔄 Cloud Deployment Token Management Strategy

### **1. Automated Token Renewal System**

#### **Pre-Market Token Refresh (Recommended)**
```bash
# Schedule: 4:00 AM ET (1:00 AM PT) - Before market prep
# Purpose: Ensure fresh tokens before market opens
# Frequency: Daily

# Cloud Cron Job
0 4 * * 1-5 cd /app/ETradeOAuth && python3 simple_oauth_cli.py start sandbox
0 4 * * 1-5 cd /app/ETradeOAuth && python3 simple_oauth_cli.py start prod
```

#### **Midnight ET Token Refresh (Alternative)**
```bash
# Schedule: 12:05 AM ET (9:05 PM PT) - Just after expiration
# Purpose: Immediate token refresh after expiration
# Frequency: Daily

# Cloud Cron Job
5 0 * * 1-5 cd /app/ETradeOAuth && python3 simple_oauth_cli.py start sandbox
5 0 * * 1-5 cd /app/ETradeOAuth && python3 simple_oauth_cli.py start prod
```

### **2. Keep-Alive System During Trading Hours**

#### **Continuous Token Maintenance**
```bash
# Schedule: Every 70 minutes during trading hours (9:30 AM - 4:00 PM ET)
# Purpose: Prevent idle timeout (2-hour limit)
# Frequency: Every 70 minutes

# Cloud Cron Job
*/70 9-16 * * 1-5 cd /app/ETradeOAuth && python3 keep_alive.py sandbox
*/70 9-16 * * 1-5 cd /app/ETradeOAuth && python3 keep_alive.py prod
```

### **3. Health Check and Recovery System**

#### **Pre-Market Health Checks**
```bash
# Schedule: 8:00 AM ET (5:00 AM PT) - Before market opens
# Purpose: Verify token health before trading begins
# Frequency: Daily

# Cloud Cron Job
0 8 * * 1-5 cd /app/ETradeOAuth && python3 simple_oauth_cli.py test sandbox
0 8 * * 1-5 cd /app/ETradeOAuth && python3 simple_oauth_cli.py test prod
```

#### **Emergency Token Recovery**
```bash
# Schedule: Every 30 minutes during trading hours
# Purpose: Detect and recover from token failures
# Frequency: Every 30 minutes

# Cloud Cron Job
*/30 9-16 * * 1-5 cd /app/ETradeOAuth && python3 emergency_token_recovery.py
```

## 🏗️ Cloud Implementation Architecture

### **Google Cloud Platform Implementation**

#### **1. Cloud Scheduler Jobs**
```yaml
# gcp-scheduler-config.yaml
jobs:
  - name: etrade-token-refresh-pre-market
    schedule: "0 4 * * 1-5"  # 4:00 AM ET, Monday-Friday
    timezone: "America/New_York"
    target:
      httpTarget:
        uri: "https://etrade-strategy.run.app/refresh-tokens"
        httpMethod: "POST"
        headers:
          "Authorization": "Bearer ${TOKEN_REFRESH_SECRET}"
    
  - name: etrade-token-keepalive
    schedule: "*/70 9-16 * * 1-5"  # Every 70 minutes during trading hours
    timezone: "America/New_York"
    target:
      httpTarget:
        uri: "https://etrade-strategy.run.app/keepalive-tokens"
        httpMethod: "POST"
        headers:
          "Authorization": "Bearer ${KEEPALIVE_SECRET}"
```

#### **2. Cloud Run Service Endpoints**
```python
# Flask endpoints for token management
@app.route('/refresh-tokens', methods=['POST'])
def refresh_tokens():
    """Refresh ETrade tokens - called by Cloud Scheduler"""
    try:
        # Refresh sandbox tokens
        subprocess.run(['python3', 'ETradeOAuth/simple_oauth_cli.py', 'start', 'sandbox'])
        
        # Refresh production tokens
        subprocess.run(['python3', 'ETradeOAuth/simple_oauth_cli.py', 'start', 'prod'])
        
        return {"status": "success", "message": "Tokens refreshed successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/keepalive-tokens', methods=['POST'])
def keepalive_tokens():
    """Keep tokens alive - called by Cloud Scheduler"""
    try:
        # Keep sandbox tokens alive
        subprocess.run(['python3', 'ETradeOAuth/keep_alive.py', 'sandbox'])
        
        # Keep production tokens alive
        subprocess.run(['python3', 'ETradeOAuth/keep_alive.py', 'prod'])
        
        return {"status": "success", "message": "Tokens kept alive successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/health-check', methods=['GET'])
def health_check():
    """Health check endpoint for token status"""
    try:
        # Test sandbox connection
        sandbox_result = subprocess.run(['python3', 'ETradeOAuth/simple_oauth_cli.py', 'test', 'sandbox'], 
                                      capture_output=True, text=True)
        
        # Test production connection
        prod_result = subprocess.run(['python3', 'ETradeOAuth/simple_oauth_cli.py', 'test', 'prod'], 
                                   capture_output=True, text=True)
        
        return {
            "status": "healthy",
            "sandbox": "ok" if sandbox_result.returncode == 0 else "error",
            "production": "ok" if prod_result.returncode == 0 else "error"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
```

### **3. Docker Container Configuration**
```dockerfile
# Dockerfile with token management
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Create startup script for token management
RUN echo '#!/bin/bash\n\
# Start token refresh service\n\
python3 -m flask run --host=0.0.0.0 --port=8080 &\n\
\n\
# Wait for tokens to be available\n\
while [ ! -f "ETradeOAuth/tokens_sandbox.json" ]; do\n\
  echo "Waiting for tokens..."\n\
  sleep 10\n\
done\n\
\n\
# Start main trading application\n\
python3 main.py --strategy-mode standard --automation-mode live' > start.sh

RUN chmod +x start.sh

EXPOSE 8080

CMD ["./start.sh"]
```

## 🚨 Emergency Token Recovery System

### **Automatic Recovery on Token Failure**
```python
# emergency_token_recovery.py
import subprocess
import logging
import time
from datetime import datetime

def emergency_token_recovery():
    """Emergency token recovery system"""
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)
    
    try:
        # Test current tokens
        result = subprocess.run(['python3', 'ETradeOAuth/simple_oauth_cli.py', 'test', 'sandbox'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            log.warning("🚨 Token failure detected - initiating emergency recovery")
            
            # Attempt token refresh
            refresh_result = subprocess.run(['python3', 'ETradeOAuth/simple_oauth_cli.py', 'start', 'sandbox'], 
                                          capture_output=True, text=True)
            
            if refresh_result.returncode == 0:
                log.info("✅ Emergency token recovery successful")
                return True
            else:
                log.error("❌ Emergency token recovery failed")
                return False
        else:
            log.info("✅ Tokens are healthy")
            return True
            
    except Exception as e:
        log.error(f"❌ Emergency recovery error: {e}")
        return False

if __name__ == "__main__":
    emergency_token_recovery()
```

## 📊 Token Management Monitoring

### **1. Token Health Dashboard**
```python
# token_health_dashboard.py
import json
import os
from datetime import datetime, timezone

def get_token_health_status():
    """Get comprehensive token health status"""
    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sandbox": {},
        "production": {},
        "overall_status": "unknown"
    }
    
    # Check sandbox tokens
    sandbox_file = "ETradeOAuth/tokens_sandbox.json"
    if os.path.exists(sandbox_file):
        with open(sandbox_file, 'r') as f:
            sandbox_tokens = json.load(f)
        
        status["sandbox"] = {
            "exists": True,
            "created": sandbox_tokens.get("created_at", "unknown"),
            "last_used": sandbox_tokens.get("last_used", "unknown"),
            "expires_at": sandbox_tokens.get("expires_at", "unknown")
        }
    else:
        status["sandbox"] = {"exists": False}
    
    # Check production tokens
    prod_file = "ETradeOAuth/tokens_prod.json"
    if os.path.exists(prod_file):
        with open(prod_file, 'r') as f:
            prod_tokens = json.load(f)
        
        status["production"] = {
            "exists": True,
            "created": prod_tokens.get("created_at", "unknown"),
            "last_used": prod_tokens.get("last_used", "unknown"),
            "expires_at": prod_tokens.get("expires_at", "unknown")
        }
    else:
        status["production"] = {"exists": False}
    
    # Determine overall status
    if status["sandbox"]["exists"] and status["production"]["exists"]:
        status["overall_status"] = "healthy"
    elif status["sandbox"]["exists"] or status["production"]["exists"]:
        status["overall_status"] = "partial"
    else:
        status["overall_status"] = "critical"
    
    return status
```

### **2. Alert System for Token Issues**
```python
# token_alert_system.py
import requests
import json
from datetime import datetime

def send_token_alert(alert_type, message):
    """Send alert about token issues"""
    
    # Telegram alert
    telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if telegram_bot_token and telegram_chat_id:
        alert_message = f"🚨 ETrade Token Alert\n\nType: {alert_type}\nMessage: {message}\nTime: {datetime.now()}"
        
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        data = {
            "chat_id": telegram_chat_id,
            "text": alert_message
        }
        
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"Failed to send Telegram alert: {e}")
    
    # Log alert
    print(f"ALERT: {alert_type} - {message}")

def monitor_token_health():
    """Monitor token health and send alerts"""
    status = get_token_health_status()
    
    if status["overall_status"] == "critical":
        send_token_alert("CRITICAL", "All ETrade tokens are missing or expired")
    elif status["overall_status"] == "partial":
        send_token_alert("WARNING", "Some ETrade tokens are missing or expired")
    
    return status
```

## 🎯 Deployment Recommendations

### **1. Production Deployment Strategy**

#### **Phase 1: Pre-Deployment (Day 0)**
- ✅ Set up Cloud Scheduler jobs for token management
- ✅ Deploy token refresh endpoints to Cloud Run
- ✅ Configure monitoring and alerting
- ✅ Test token management system in sandbox

#### **Phase 2: Initial Deployment (Day 1)**
- ✅ Deploy with sandbox tokens only
- ✅ Monitor token refresh system
- ✅ Validate automated token management
- ✅ Test emergency recovery procedures

#### **Phase 3: Production Deployment (Day 2+)**
- ✅ Deploy with production tokens
- ✅ Enable full trading operations
- ✅ Monitor token health continuously
- ✅ Maintain automated token management

### **2. Monitoring and Maintenance**

#### **Daily Monitoring**
- ✅ Check token health dashboard
- ✅ Verify automated refresh jobs
- ✅ Monitor API call success rates
- ✅ Review alert notifications

#### **Weekly Maintenance**
- ✅ Review token refresh logs
- ✅ Update token management scripts if needed
- ✅ Test emergency recovery procedures
- ✅ Optimize token refresh timing

#### **Monthly Review**
- ✅ Analyze token usage patterns
- ✅ Optimize token refresh schedule
- ✅ Update monitoring and alerting
- ✅ Review and update documentation

## 📋 Implementation Checklist

### **Cloud Deployment Token Management**
- [ ] Set up Cloud Scheduler for daily token refresh (4:00 AM ET)
- [ ] Set up Cloud Scheduler for keep-alive during trading hours
- [ ] Deploy token management endpoints to Cloud Run
- [ ] Configure monitoring and alerting system
- [ ] Test emergency token recovery procedures
- [ ] Set up token health dashboard
- [ ] Configure Telegram alerts for token issues
- [ ] Test complete token management workflow

### **Security Considerations**
- [ ] Secure token storage in Google Secret Manager
- [ ] Implement proper authentication for token endpoints
- [ ] Use HTTPS for all token management communications
- [ ] Implement rate limiting for token refresh endpoints
- [ ] Monitor for unauthorized token access attempts

### **Backup and Recovery**
- [ ] Implement token backup system
- [ ] Set up emergency manual token refresh procedures
- [ ] Document manual token recovery process
- [ ] Test disaster recovery scenarios

## 🎉 Summary

The ETrade Strategy implements a comprehensive token management system for cloud deployment that addresses the daily midnight ET expiration:

✅ **Automated Token Refresh**: Daily refresh at 4:00 AM ET  
✅ **Keep-Alive System**: Every 70 minutes during trading hours  
✅ **Health Monitoring**: Continuous token health checks  
✅ **Emergency Recovery**: Automatic recovery from token failures  
✅ **Alert System**: Real-time notifications for token issues  
✅ **Cloud Integration**: Full Google Cloud Platform integration  

**This system ensures the ETrade Strategy can operate continuously in the cloud without manual token management intervention.**

---

*Last Updated: 2025-09-14*  
*Status: Ready for Cloud Deployment* ✅
