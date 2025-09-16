# ETradeOAuth - Complete OAuth 1.0a Integration System

**Complete OAuth 1.0a implementation with HMAC-SHA1 signature for The Easy ETrade Strategy.**
**✅ WORKING: Correct OAuth signature, Production API access, Real account balance retrieval**

## 🎯 **OAuth Token Management Overview**

### **Why OAuth Tokens Are Critical**
E*TRADE OAuth 1.0a tokens are the **lifeblood** of The Easy ETrade Strategy system. Without valid tokens, the entire trading automation cannot function. These tokens provide secure access to:

- **Real-time market data** for scanning and analysis
- **Account balance and portfolio** information for position sizing
- **Order placement and management** for automated trading
- **Risk management** and position monitoring

### **Token Lifespan & Requirements**
- **Daily Expiry**: Tokens expire at **midnight Eastern Time** every day
- **Idle Timeout**: Tokens become inactive after **2 hours** of no API calls
- **Renewal Window**: Inactive tokens can be renewed (no re-authorization needed)
- **Expiry**: Expired tokens require **full re-authentication** with E*TRADE

### **Critical Daily Cadence**
The trading system **MUST** have fresh tokens before market operations begin:

1. **1 Hour Before Market Open**: Telegram alert sent with token renewal link
2. **Token Renewal**: User accesses web app to get new tokens
3. **Premarket Scanner**: System builds watchlist with fresh tokens
4. **Trading Hours**: Keep-alive system maintains token activity
5. **Next Day**: Cycle repeats

## 🚀 **Frontend Web Application**

### **Mobile-Friendly Token Management Interface**

The system includes a **FastAPI-based web application** hosted on **Firebase Hosting** that provides:

#### **Key Features:**
- 📱 **Mobile-optimized interface** for easy token renewal
- ⏰ **Real-time countdown timer** showing token expiry
- 🔄 **One-click token renewal** process
- 📊 **Token status dashboard** for both environments
- 🚨 **Keep-alive system monitoring** and control
- 🔐 **Secure token storage** in Google Cloud Secret Manager

#### **Web App Endpoints:**
```
/                    # Main dashboard with countdown timer
/status              # Detailed token status for prod/sandbox
/keepalive/status    # Keep-alive system health
/keepalive/force     # Manual keep-alive trigger
/cron/morning-alert  # Cloud Scheduler endpoint
```

#### **Token Renewal Process:**
1. **User receives Telegram alert** 1 hour before market open
2. **Clicks deep link** to access web app
3. **Views countdown timer** showing time until token expiry
4. **Clicks "Renew Tokens"** button
5. **Redirected to E*TRADE** for authorization
6. **Copies PIN** from E*TRADE authorization page
7. **Pastes PIN** into web app form
8. **Tokens automatically generated** and stored in Secret Manager
9. **Trading system notified** of new tokens via Pub/Sub

## 🏗️ **System Architecture**

### **OAuth Integration Components**

#### **1. Core OAuth Manager (`central_oauth_manager.py`)**
- **Centralized token management** for all environments
- **Automatic token renewal** when idle for 2+ hours
- **Integration with Google Cloud Secret Manager**
- **Pub/Sub notifications** for token updates

#### **2. Keep-Alive System (`oauth_keepalive.py`)**
- **Background task** making API calls every 1.5 hours
- **Prevents token idle timeout** (2-hour limit)
- **Health monitoring** and failure alerting
- **Graceful shutdown** and error recovery

#### **3. Web Application (`login/oauth_web_app.py`)**
- **FastAPI-based** mobile-friendly interface
- **Real-time token status** and countdown timer
- **Integration with alert system** for notifications
- **Secure token generation** and storage

#### **4. Simple CLI Interface (`simple_oauth_cli.py`)**
- **Manual token management** for development/testing
- **Health checks** and status monitoring
- **Backup authentication** method

## 🔄 **Token Lifecycle Management**

### **Daily Token Cycle**

#### **Phase 1: Token Expiry (Midnight ET)**
```
00:00 ET - Tokens expire, trading system stops
00:01 ET - System enters "token renewal required" state
```

#### **Phase 2: Morning Alert (1 Hour Before Market Open)**
```
08:30 ET - Telegram alert sent with renewal link
08:30 ET - Web app shows countdown timer
08:30 ET - User can begin token renewal process
```

#### **Phase 3: Token Renewal (Before Premarket)**
```
09:00 ET - User completes token renewal
09:00 ET - New tokens stored in Secret Manager
09:00 ET - Trading system notified via Pub/Sub
09:00 ET - System ready for premarket operations
```

#### **Phase 4: Trading Hours (Keep-Alive Active)**
```
09:30 ET - Market opens, keep-alive system active
09:30 ET - API calls every 1.5 hours maintain tokens
16:00 ET - Market closes, keep-alive continues
```

#### **Phase 5: Next Day Preparation**
```
23:59 ET - Keep-alive system prepares for shutdown
00:00 ET - Cycle repeats
```

### **Token Storage & Security**

#### **Google Cloud Secret Manager Integration**
```python
# Token storage locations
ETRADE_OAUTH_PROD_ACCESS_TOKEN
ETRADE_OAUTH_PROD_ACCESS_SECRET
ETRADE_OAUTH_SANDBOX_ACCESS_TOKEN
ETRADE_OAUTH_SANDBOX_ACCESS_SECRET
```

#### **Local Development Files**
- `tokens_prod.json` - Production tokens (development only)
- `tokens_sandbox.json` - Sandbox tokens (development only)

## 🎯 **Integration with Trading System**

### **Main System Integration (`main.py`)**

The OAuth system is fully integrated into the main trading system:

```python
# OAuth initialization in main.py
from modules.etrade_oauth_integration import get_etrade_oauth_integration
from modules.oauth_keepalive import start_oauth_keepalive, stop_oauth_keepalive

# Initialize OAuth integration
oauth_integration = get_etrade_oauth_integration(etrade_mode)

# Start keep-alive system
await start_oauth_keepalive()

# Trading system operations...
# - Premarket scanner
# - Watchlist building
# - Signal generation
# - Order execution

# Graceful shutdown
await stop_oauth_keepalive()
```

### **Trading Module Integration (`prime_etrade_trading.py`)**

The trading module includes comprehensive OAuth validation:

```python
class PrimeETradeTrading:
    def initialize(self):
        """Initialize with OAuth token validation"""
        # Validate OAuth tokens
        if not self._validate_oauth_tokens():
            # Attempt token renewal
            if not self._renew_tokens():
                raise OAuthError("Token renewal failed")
        
        # Test API connection
        if not self._test_api_connection():
            raise OAuthError("API connection failed")
        
        # Load trading account
        self._select_primary_account()
```

## 📱 **Mobile Web App Features**

### **Countdown Timer Interface**
```html
<!-- Real-time countdown to token expiry -->
<div class="countdown-timer">
    <h2>Access Token Status</h2>
    <div class="timer-display">
        <span id="countdown">09:34:23</span>
        <p>Access Token good until: 09:34:23</p>
    </div>
    <button onclick="renewTokens()">Renew Tokens</button>
</div>
```

### **Token Status Dashboard**
```html
<!-- Environment status grid -->
<div class="status-grid">
    <div class="env-status prod">
        <h3>Production</h3>
        <span class="status-indicator active">●</span>
        <p>Last Used: 2 hours ago</p>
    </div>
    <div class="env-status sandbox">
        <h3>Sandbox</h3>
        <span class="status-indicator warning">●</span>
        <p>Last Used: 3 hours ago</p>
    </div>
</div>
```

### **Keep-Alive System Control**
```html
<!-- Keep-alive monitoring -->
<div class="keepalive-controls">
    <h3>Keep-Alive System</h3>
    <div class="keepalive-status">
        <span class="status-indicator healthy">●</span>
        <p>Status: Healthy</p>
        <p>Next Call: 1.2 hours</p>
    </div>
    <button onclick="forceKeepAlive()">Force Keep-Alive</button>
</div>
```

## 🚨 **Alert System Integration**

### **Telegram Alerts (`prime_alert_manager.py`)**

The system includes comprehensive alerting for OAuth management:

#### **Morning Token Renewal Alert**
```
🔐 OAuth Token Renewal Required
⏰ 1 hour until market open
🔗 Renew tokens: https://your-app.web.app
📱 Mobile-friendly interface ready
```

#### **Token Renewal Success**
```
✅ OAuth Tokens Renewed Successfully
🕘 Production: Active
🕘 Sandbox: Active
🚀 Trading system ready for market open
```

#### **Token Renewal Error**
```
❌ OAuth Token Renewal Failed
⚠️ Production: Expired
⚠️ Sandbox: Expired
🔧 Manual intervention required
```

#### **Keep-Alive Warnings**
```
⚠️ OAuth Keep-Alive Warning
🔄 Production: 3 consecutive failures
⏰ Tokens may go idle soon
🔧 Check system status
```

## 🔧 **Deployment & Configuration**

### **Google Cloud Platform Deployment**

#### **Cloud Run Services**
- **OAuth Web App**: `etrade-oauth-webapp`
- **Trading System**: `etrade-trading-system`
- **Keep-Alive Service**: Integrated with trading system

#### **Cloud Scheduler Jobs**
```yaml
# Morning OAuth Alert (1 hour before market open)
name: oauth-morning-alert
schedule: "30 8 * * 1-5"  # 8:30 AM ET, weekdays
timezone: "America/New_York"
target: https://etrade-oauth-webapp.run.app/cron/morning-alert
```

#### **Secret Manager Secrets**
```yaml
# OAuth tokens
ETRADE_OAUTH_PROD_ACCESS_TOKEN
ETRADE_OAUTH_PROD_ACCESS_SECRET
ETRADE_OAUTH_SANDBOX_ACCESS_TOKEN
ETRADE_OAUTH_SANDBOX_ACCESS_SECRET

# E*TRADE credentials
ETRADE_PROD_CONSUMER_KEY
ETRADE_PROD_CONSUMER_SECRET
ETRADE_SANDBOX_CONSUMER_KEY
ETRADE_SANDBOX_CONSUMER_SECRET
```

### **Firebase Hosting Configuration**

#### **Frontend Deployment**
```bash
# Deploy to Firebase Hosting
firebase deploy --only hosting

# Custom domain configuration
# oauth.yourdomain.com -> Firebase Hosting
```

#### **Environment Variables**
```javascript
// Firebase Hosting environment
VITE_OAUTH_WEBAPP_URL=https://etrade-oauth-webapp.run.app
VITE_TELEGRAM_BOT_TOKEN=your_bot_token
VITE_GOOGLE_CLOUD_PROJECT=your_project_id
```

## 📊 **Monitoring & Health Checks**

### **System Health Endpoints**

#### **Token Status API**
```bash
GET /status
# Returns comprehensive token status for all environments
```

#### **Keep-Alive Status API**
```bash
GET /keepalive/status
# Returns keep-alive system health and statistics
```

#### **Force Keep-Alive API**
```bash
POST /keepalive/force
# Manually triggers keep-alive calls for all environments
```

### **Logging & Debugging**

#### **OAuth Operations Log**
```bash
# OAuth system logs
tail -f etrade_oauth.log

# Keep-alive system logs
tail -f oauth_keepalive.log

# Web app logs (Cloud Run)
gcloud logs tail etrade-oauth-webapp
```

#### **Token File Inspection**
```bash
# Check token file contents
cat tokens_prod.json | jq '.'
cat tokens_sandbox.json | jq '.'

# Check last renewal time
cat tokens_prod.json | jq '.last_renewed'
```

## ⚠️ **Critical Requirements & Best Practices**

### **Daily Token Management**
1. **Never skip daily renewal** - System will not function without fresh tokens
2. **Renew before premarket** - Tokens must be active before scanner runs
3. **Monitor keep-alive system** - Ensure tokens stay active during trading
4. **Test both environments** - Verify both prod and sandbox tokens work

### **Security Best Practices**
1. **Store tokens in Secret Manager** - Never commit tokens to version control
2. **Use HTTPS only** - All web app communications must be encrypted
3. **Rotate credentials regularly** - Update E*TRADE consumer keys periodically
4. **Monitor access logs** - Watch for unauthorized token usage

### **Error Handling**
1. **Graceful degradation** - System should handle token failures gracefully
2. **Automatic retry** - Implement retry logic for transient failures
3. **Alert escalation** - Multiple alert levels for different failure types
4. **Manual override** - Always provide manual token renewal option

## 🚨 **Troubleshooting Guide**

### **Common Issues & Solutions**

#### **"Tokens expired at midnight ET"**
```bash
# Solution: Access web app and renew tokens
# 1. Check Telegram for renewal link
# 2. Access web app
# 3. Complete token renewal process
# 4. Verify tokens are active
```

#### **"Keep-alive system not running"**
```bash
# Solution: Check system status and restart
curl https://etrade-oauth-webapp.run.app/keepalive/status
curl -X POST https://etrade-oauth-webapp.run.app/keepalive/force
```

#### **"Web app not accessible"**
```bash
# Solution: Check Firebase Hosting and Cloud Run
firebase hosting:channel:list
gcloud run services list
gcloud run services describe etrade-oauth-webapp
```

#### **"Token renewal failed"**
```bash
# Solution: Manual CLI renewal
cd ETradeOAuth/modules
python3 oauth_keepalive.py prod
python3 oauth_keepalive.py sandbox
```

## 🔮 **Future Enhancements**

### **Planned Features**
- **Multi-account support** - Manage multiple E*TRADE accounts
- **Advanced monitoring** - Real-time token health dashboard
- **Automated testing** - Automated token validation tests
- **Slack integration** - Additional notification channels
- **Token analytics** - Usage patterns and optimization

### **Integration Improvements**
- **Ultima Bot integration** - Display token status in main dashboard
- **Advanced alerting** - Escalation policies and notification preferences
- **Performance optimization** - Faster token renewal and validation
- **Mobile app** - Native mobile app for token management

---

## 📞 **Support & Documentation**

- **Main Documentation**: `V2 Cursor Etrade Strategy/docs/`
- **OAuth Guide**: `docs/OAuth.md`
- **Cloud Deployment**: `docs/Cloud.md`
- **Frontend Setup**: `docs/Firebase.md`
- **Alert System**: `docs/Alerts.md`

**The Easy ETrade Strategy OAuth System - Secure, Automated, Production-Ready** 🚀