# 🔐 OAuth Alert Usage Guide - Token Validation & Expiry Alerts

**Created**: October 1, 2025  
**Version**: 1.0  
**Purpose**: Guide for using the new validated OAuth alert system

---

## 📋 Overview

The OAuth alert system has been enhanced to ensure alerts are only sent when token status is **confirmed**, preventing false positive success alerts and adding real-time expiry detection.

---

## ✅ Token Renewal Success Alert

### **Method Signature**

```python
async def send_oauth_renewal_success(self, environment: str, token_valid: bool = True) -> bool:
    """
    Send OAuth token renewal success notification
    
    Args:
        environment: Environment (prod or sandbox)
        token_valid: Whether token has been confirmed valid (default: True)
        
    Returns:
        True if alert sent successfully
        
    Note:
        Only sends success alert if token_valid is True.
        If token_valid is False, this method returns False without sending.
    """
```

### **Usage Examples**

#### **✅ Correct Usage - With Token Validation**

```python
from modules.prime_alert_manager import get_prime_alert_manager

# After OAuth flow completes
alert_manager = get_prime_alert_manager()

# Step 1: Exchange PIN for access tokens
tokens = await oauth_backend.exchange_pin_for_tokens(environment, pin)

# Step 2: Store tokens in Secret Manager
await secret_manager.store_tokens(environment, tokens)

# Step 3: VALIDATE the token by testing API connection
token_is_valid = await test_token_connection(environment, tokens)

# Step 4: Only send success alert if token is confirmed valid
if token_is_valid:
    await alert_manager.send_oauth_renewal_success(environment, token_valid=True)
    log.info(f"✅ {environment} token renewed and validated successfully")
else:
    # Token is invalid - send error alert instead
    await alert_manager.send_oauth_renewal_error(
        environment, 
        "Token validation failed - please try renewal again"
    )
    log.error(f"❌ {environment} token renewal completed but validation failed")
```

#### **❌ Incorrect Usage - Without Validation**

```python
# DON'T DO THIS - No validation before success alert
tokens = await oauth_backend.exchange_pin_for_tokens(environment, pin)
await secret_manager.store_tokens(environment, tokens)

# ❌ BAD: Sending success alert without confirming token is valid
await alert_manager.send_oauth_renewal_success(environment)
# This could send a success alert even if the token is actually invalid!
```

### **Token Validation Methods**

```python
async def test_token_connection(environment: str, tokens: dict) -> bool:
    """
    Test if OAuth token is valid by making API call
    
    Returns:
        True if token is valid and API call succeeds
        False if token is invalid or API call fails
    """
    try:
        # Make a simple API call to test token
        from modules.prime_etrade_trading import PrimeETradeTrading
        
        etrade = PrimeETradeTrading(environment)
        etrade.oauth_token = tokens['oauth_token']
        etrade.oauth_token_secret = tokens['oauth_token_secret']
        
        # Test connection with account list call
        accounts = etrade.get_accounts()
        
        if accounts and len(accounts) > 0:
            log.info(f"✅ Token validation successful for {environment}")
            return True
        else:
            log.warning(f"⚠️ Token validation failed for {environment} - no accounts returned")
            return False
            
    except Exception as e:
        log.error(f"❌ Token validation error for {environment}: {e}")
        return False
```

---

## ⚠️ Token Expired Alert

### **Method Signature**

```python
async def send_oauth_token_expired_alert(self, environment: str) -> bool:
    """
    Send OAuth token expired alert when token is confirmed expired
    
    Args:
        environment: Environment (prod or sandbox)
        
    Returns:
        True if alert sent successfully
    """
```

### **When to Use**

Send this alert when:
1. **Real-time token check** detects expired token
2. **API call fails** with 401 Unauthorized (token expired)
3. **Scheduled token validation** finds expired token
4. **Before market open** if token is detected as expired

### **Usage Examples**

#### **Example 1: Real-Time Token Check**

```python
async def check_token_health():
    """Periodic token health check (runs every hour)"""
    for environment in ['prod', 'sandbox']:
        try:
            # Test if token is valid
            is_valid = await test_token_connection(environment)
            
            if not is_valid:
                # Token is expired or invalid
                log.warning(f"⚠️ {environment} token detected as expired")
                
                # Send expired alert
                await alert_manager.send_oauth_token_expired_alert(environment)
                
        except Exception as e:
            log.error(f"Error checking {environment} token health: {e}")
```

#### **Example 2: API Call Failure Detection**

```python
async def make_trading_api_call(endpoint: str):
    """Make API call with token validation"""
    try:
        response = await etrade_api.call(endpoint)
        return response
        
    except Exception as e:
        # Check if error is due to expired token
        if "401" in str(e) or "Unauthorized" in str(e):
            log.error(f"API call failed - token may be expired: {e}")
            
            # Send expired alert
            await alert_manager.send_oauth_token_expired_alert('prod')
            
            raise Exception("OAuth token expired - renewal required")
        else:
            raise e
```

#### **Example 3: Pre-Market Token Validation**

```python
async def pre_market_token_check():
    """Check token status before market open (runs at 7:00 AM ET)"""
    log.info("Running pre-market token validation")
    
    # Check production token
    prod_valid = await test_token_connection('prod')
    
    if not prod_valid:
        log.warning("Production token is EXPIRED before market open")
        
        # Send expired alert
        await alert_manager.send_oauth_token_expired_alert('prod')
        
        # Check if sandbox is valid as fallback
        sandbox_valid = await test_token_connection('sandbox')
        
        if sandbox_valid:
            log.info("Sandbox token is valid - system can run in demo mode")
        else:
            log.error("ALL tokens are expired - system cannot operate")
            await alert_manager.send_oauth_token_expired_alert('sandbox')
```

---

## 🔄 Complete OAuth Flow with Validation

### **Backend Integration (oauth_backend.py)**

```python
@app.post("/oauth/verify")
async def oauth_verify(session_id: str = Form(...), verifier: str = Form(...)):
    """Complete OAuth flow and validate token"""
    try:
        # Step 1: Exchange PIN for access tokens
        tokens = await exchange_pin_for_tokens(session_id, verifier)
        
        if not tokens:
            log.error("Failed to exchange PIN for tokens")
            return {"success": False, "error": "Token exchange failed"}
        
        # Step 2: Store tokens in Secret Manager
        environment = get_session_environment(session_id)
        await store_tokens_in_secret_manager(environment, tokens)
        
        # Step 3: VALIDATE the token
        log.info(f"Validating {environment} token...")
        token_is_valid = await test_token_connection(environment, tokens)
        
        # Step 4: Send appropriate alert based on validation result
        alert_manager = get_prime_alert_manager()
        
        if token_is_valid:
            # Token is confirmed valid - send success alert
            log.info(f"✅ {environment} token validated successfully")
            await alert_manager.send_oauth_renewal_success(
                environment, 
                token_valid=True
            )
            
            return {
                "success": True,
                "message": f"{environment} token renewed and validated successfully",
                "token_valid": True
            }
        else:
            # Token validation failed - send error alert
            log.error(f"❌ {environment} token validation failed")
            await alert_manager.send_oauth_renewal_error(
                environment,
                "Token validation failed - token may be invalid or API is down"
            )
            
            return {
                "success": False,
                "error": "Token validation failed",
                "token_valid": False
            }
            
    except Exception as e:
        log.error(f"OAuth verification error: {e}")
        
        # Send error alert
        await alert_manager.send_oauth_renewal_error(
            environment,
            f"OAuth verification failed: {str(e)}"
        )
        
        return {
            "success": False,
            "error": str(e)
        }
```

---

## 📊 Alert Decision Matrix

### **When OAuth Flow Completes:**

| Token Status | Alert to Send | Method |
|--------------|--------------|---------|
| ✅ **Valid** (confirmed via API test) | Success Alert | `send_oauth_renewal_success(env, token_valid=True)` |
| ❌ **Invalid** (failed API test) | Error Alert | `send_oauth_renewal_error(env, "Validation failed")` |
| ⚠️ **Unknown** (couldn't test) | Warning Alert | `send_oauth_warning(env, "Unable to validate")` |

### **When Checking Token Status:**

| Token Status | Alert to Send | Method |
|--------------|--------------|---------|
| ✅ **Valid** | No alert needed | Continue operations |
| ❌ **Expired** (detected anytime) | Expired Alert | `send_oauth_token_expired_alert(env)` |
| ⚠️ **Expiring Soon** (<1 hour) | Warning Alert | `send_oauth_warning(env, "Expires in X minutes")` |

---

## 🎯 Implementation Checklist

### **For Backend OAuth Verification:**

- [x] Exchange PIN for access tokens
- [x] Store tokens in Secret Manager
- [x] **Validate token with API test call**
- [x] **Only send success alert if validated**
- [x] Send error alert if validation fails
- [x] Return validation status to frontend

### **For Token Health Monitoring:**

- [x] Schedule hourly token health checks
- [x] Test token with API call
- [x] **Send expired alert if token is expired**
- [x] Send warning if token expiring soon
- [x] Track token status in memory

### **For Trading System:**

- [x] Validate token before trading operations
- [x] **Send expired alert if API calls fail with 401**
- [x] Attempt token renewal if expired
- [x] Graceful degradation if tokens unavailable

---

## 📱 Alert Examples

### **Success Alert (Only sent if token validated)**
```
🌙 OAuth Production Token Alert — 21:00 PT

💎 Trading Ready: E*TRADE prod token has been successfully renewed 🤓
☁️ Cloud Keepalive: ✅ Active — token will remain valid until expiry at 12:00 AM ET (midnight)

📊 System Mode: Live Trading Enabled
🔄 Next Renewal: Required before next market open
```

### **Expired Alert (Sent anytime token detected as expired)**
```
⚠️ OAuth Production Token Expired — 14:30 PT

🚨 Token Status: E*TRADE prod token is EXPIRED ❌
⏰ Detected: 14:30 PT

🌐 Public Dashboard: https://easy-trading-oauth-v2.web.app
🦜💼 Management Portal: https://easy-trading-oauth-v2.web.app/manage.html

⚠️ Impact: Live trading disabled until token renewed

👉 Action Required:
1. Visit the public dashboard
2. Click "Renew Production"
3. Enter access code (easy2025) on management portal
4. Complete OAuth authorization
5. Token will be renewed and stored
```

### **Error Alert (Sent if OAuth flow completes but token is invalid)**
```
❌ OAuth Token Renewal Failed

🔐 Environment: PROD
⏰ Time: 21:15 PT
🚨 Error: Token validation failed - token may be invalid or API is down

🔧 Please try renewal again
🔗 Management Portal: https://easy-trading-oauth-v2.web.app/manage.html
```

---

## 🔑 Key Improvements

### **1. Validation Before Success**
- ✅ Success alerts only sent when token is **confirmed valid**
- ✅ Prevents false positive success notifications
- ✅ Ensures trading system has working tokens

### **2. Real-Time Expiry Detection**
- ✅ Detects expired tokens at any time (not just midnight)
- ✅ Immediate notification when token becomes expired
- ✅ Clear impact statement (trading disabled)
- ✅ Step-by-step renewal instructions

### **3. Better Error Handling**
- ✅ Distinguishes between OAuth flow errors and validation failures
- ✅ Appropriate alert sent for each scenario
- ✅ Clear error messages for troubleshooting

---

## 🚀 Quick Reference

### **Available Alert Methods:**

```python
from modules.prime_alert_manager import get_prime_alert_manager

alert_manager = get_prime_alert_manager()

# Token renewal success (validated)
await alert_manager.send_oauth_renewal_success('prod', token_valid=True)

# Token confirmed expired
await alert_manager.send_oauth_token_expired_alert('prod')

# Token renewal error
await alert_manager.send_oauth_renewal_error('prod', "Error message")

# Token warning
await alert_manager.send_oauth_warning('prod', "Warning message")

# Morning renewal reminder
await alert_manager.send_oauth_morning_alert()

# Market open alert
await alert_manager.send_oauth_market_open_alert()
```

---

## ✅ Summary

**Updated Behavior**:
1. ✅ Success alerts **require token validation** - won't send if token is invalid
2. ✅ New expired alert **detects token expiry anytime** - not just at midnight
3. ✅ Clear separation between **validated success** and **renewal errors**
4. ✅ Real-time detection and notification of token issues

**Result**: More accurate alerts that reflect actual token status! 🎉

---

**Maintained By**: €£$¥ Trading Software Development Team  
**Last Updated**: October 1, 2025

