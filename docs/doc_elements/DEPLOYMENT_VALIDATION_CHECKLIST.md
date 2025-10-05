# 🔍 Deployment Validation Checklist - V2 ETrade Strategy

**Date**: October 1, 2025  
**Purpose**: Validate complete trading system deployment to Google Cloud  
**Mode**: Demo + Signal-Only (Sandbox tokens)

---

## ✅ **Pre-Deployment Validation**

### **1. OAuth Tokens Valid**
```bash
# Check via web app
URL: https://easy-trading-oauth-v2.web.app

Expected:
✅ Production Token: Valid
✅ Sandbox Token: Valid
✅ Cloud Keepalive: Active
```

### **2. Watchlist Ready**
```bash
# Local watchlist file exists
ls -lh data/watchlist/dynamic_watchlist.csv

Expected:
✅ File exists
✅ 118 symbols
✅ Created today (October 1, 2025)
```

### **3. Code Updated**
```bash
# Check key files modified today
ls -lt modules/prime_trading_system.py
ls -lt build_dynamic_watchlist.py
ls -lt main.py

Expected:
✅ All files show October 1 modification
✅ Watchlist scanning: 2 minutes
✅ Position monitoring: 60 seconds
✅ Batch size: 25 symbols
```

---

## 🚀 **Post-Deployment Validation**

### **1. Cloud Run Service Deployed**
```bash
gcloud run services describe easy-etrade-strategy \
  --region=us-central1 \
  --project=easy-etrade-strategy \
  --format="value(status.url,status.latestReadyRevisionName)"

Expected:
✅ Service URL returned
✅ Revision name shows today's date
✅ Status: Ready
```

### **2. Health Endpoint Check**
```bash
curl -s "https://easy-etrade-strategy-[hash].run.app/health" | python3 -m json.tool

Expected:
{
  "status": "healthy",
  "timestamp": "2025-10-01T...",
  "environment": "development",
  "strategy_mode": "standard",
  "system_mode": "signal_only"
}
```

### **3. Status Endpoint Check**
```bash
curl -s "https://easy-etrade-strategy-[hash].run.app/status" | python3 -m json.tool

Expected:
{
  "service": "Easy ETrade Strategy",
  "status": "active",
  "cloud_mode": true,
  "trading_thread_active": true,  ← CRITICAL: Should be TRUE
  "running": true
}
```

### **4. Trading Thread Active**
```bash
# Check logs for trading initialization
gcloud logging read \
  "resource.labels.service_name=easy-etrade-strategy AND textPayload=~'Trading system started'" \
  --limit=10 \
  --project=easy-etrade-strategy

Expected:
✅ "Trading system started in background thread"
✅ "Scanning 118 symbols for NEW signals every 2 minutes"
✅ "Monitoring OPEN positions every 60 seconds"
```

### **5. Watchlist Loading**
```bash
# Check logs for watchlist loading
gcloud logging read \
  "resource.labels.service_name=easy-etrade-strategy AND textPayload=~'watchlist'" \
  --limit=20 \
  --project=easy-etrade-strategy

Expected:
✅ "Loaded 118 symbols from data/watchlist/dynamic_watchlist.csv"
✅ "Symbols: ELIL, SHPU, NVDL, DFEN, GDXU..."
```

### **6. ETrade Integration Working**
```bash
# Check logs for ETrade calls
gcloud logging read \
  "resource.labels.service_name=easy-etrade-strategy AND textPayload=~'ETrade'" \
  --limit=20 \
  --project=easy-etrade-strategy

Expected:
✅ ETrade API calls successful
✅ Account data retrieved
✅ No authentication errors
```

### **7. Scanning Loop Running**
```bash
# Check logs for scan cycles
gcloud logging read \
  "resource.labels.service_name=easy-etrade-strategy AND textPayload=~'Scanning'" \
  --limit=10 \
  --project=easy-etrade-strategy \
  --freshness=10m

Expected:
✅ "Scanning 118 symbols for NEW buy signals (2-min interval)..."
✅ "Completed watchlist scan at HH:MM:SS"
✅ Logs show scan every 2 minutes
```

---

## 📊 **Cloud Scheduler Validation**

### **8. Watchlist Builder Job**
```bash
# Check Cloud Scheduler job exists
gcloud scheduler jobs describe build-daily-watchlist \
  --location=us-central1 \
  --project=easy-etrade-strategy

Expected:
✅ Schedule: "0 7 * * 1-5" (7 AM ET, weekdays)
✅ Time zone: America/New_York
✅ Target: /api/build-watchlist endpoint
✅ Status: ENABLED
```

### **9. OAuth Scheduler Jobs**
```bash
# List all scheduler jobs
gcloud scheduler jobs list \
  --location=us-central1 \
  --project=easy-etrade-strategy

Expected:
✅ oauth-keepalive-prod (every hour at :00)
✅ oauth-keepalive-sandbox (every hour at :30)
✅ oauth-midnight-alert (12:00 AM ET daily)
✅ oauth-market-open-alert (8:30 AM ET weekdays)
✅ build-daily-watchlist (7:00 AM ET weekdays)
```

---

## 🎯 **Functional Testing**

### **10. Manual Watchlist Build Test**
```bash
# Trigger watchlist build manually
SERVICE_URL=$(gcloud run services describe easy-etrade-strategy \
  --region=us-central1 \
  --project=easy-etrade-strategy \
  --format="value(status.url)")

curl -X POST "${SERVICE_URL}/api/build-watchlist" \
  -H "Content-Type: application/json" \
  -d '{}'

Expected:
{
  "status": "success",
  "message": "Watchlist built successfully",
  "symbols_count": 118,
  "timestamp": "2025-10-01T..."
}
```

### **11. Signal Generation Test (Wait 2-5 Minutes)**
```bash
# Monitor for signal generation
gcloud logging read \
  "resource.labels.service_name=easy-etrade-strategy AND textPayload=~'signal'" \
  --limit=20 \
  --project=easy-etrade-strategy \
  --freshness=10m

Expected:
✅ Logs show signal analysis
✅ Multi-strategy manager running
✅ Production signal generator active
✅ (May or may not find signals - depends on market conditions)
```

### **12. Telegram Alert Test**
```bash
# Check your Telegram for alerts
# Should see OAuth alerts working from earlier

Expected within next 2-5 minutes:
📱 If signal found: Buy signal alert with emoji (🔰🔰🔰/🔰🔰/🔰/📟/🟡)
📱 Signal details: Symbol, confidence, expected return, etc.
```

---

## 📋 **System Integration Validation**

### **13. UnifiedServicesManager Initialized**
```bash
gcloud logging read \
  "resource.labels.service_name=easy-etrade-strategy AND textPayload=~'UnifiedServicesManager'" \
  --limit=10 \
  --project=easy-etrade-strategy

Expected:
✅ "Initializing UnifiedServicesManager..."
✅ "Data Service initialized"
✅ "Signal Service initialized"
✅ "Trading Service initialized"
```

### **14. PrimeTradingSystem Started**
```bash
gcloud logging read \
  "resource.labels.service_name=easy-etrade-strategy AND textPayload=~'PrimeTradingSystem'" \
  --limit=10 \
  --project=easy-etrade-strategy

Expected:
✅ "Starting enhanced main trading loop"
✅ "Symbol list loaded"
✅ "Running: True"
```

### **15. Memory and Performance**
```bash
gcloud run services describe easy-etrade-strategy \
  --region=us-central1 \
  --project=easy-etrade-strategy \
  --format="yaml(spec.template.spec.containers[0].resources)"

Expected:
✅ Memory: 4Gi
✅ CPU: 2
✅ Timeout: 3600s (1 hour)
```

---

## 🎯 **Success Criteria**

### **All Must Pass:**
- ✅ **Cloud Run service**: Deployed and healthy
- ✅ **Trading thread**: Active (`trading_thread_active: true`)
- ✅ **Watchlist loaded**: 118 symbols from `dynamic_watchlist.csv`
- ✅ **Scanning active**: Logs show 2-minute scan cycles
- ✅ **ETrade integration**: API calls successful
- ✅ **OAuth tokens**: Valid sandbox tokens loaded
- ✅ **Cloud Scheduler**: 5 jobs configured and enabled
- ✅ **Alert system**: Telegram alerts working

### **Expected Behavior (Demo Mode):**
- 🔍 **7:00 AM ET**: Cloud Scheduler builds fresh watchlist
- 🔍 **9:30 AM - 4:00 PM ET**: System scans for signals every 2 minutes
- 📱 **When signal found**: Telegram alert sent (🔰🔰🔰/🔰🔰/🔰/📟/🟡)
- ⚠️ **NO TRADES EXECUTED**: System in signal_only mode
- 📊 **4:00 PM ET**: End-of-Day summary (may be empty if no signals)

---

## 🛠️ **Troubleshooting**

### **If trading_thread_active is FALSE:**
```bash
# Check for errors in logs
gcloud logging read \
  "resource.labels.service_name=easy-etrade-strategy AND severity>=ERROR" \
  --limit=50 \
  --project=easy-etrade-strategy

# Check thread initialization
gcloud logging read \
  "resource.labels.service_name=easy-etrade-strategy AND textPayload=~'thread'" \
  --limit=20 \
  --project=easy-etrade-strategy
```

### **If no signals generated:**
- ✅ **This is NORMAL** - system only generates signals when ALL confirmations pass
- ✅ **High confidence required** - 90%+ confidence for Standard strategy
- ✅ **Market conditions matter** - may not find signals every day
- ✅ **Signal-only mode** - confirms system is working even without trades

### **If watchlist not loading:**
```bash
# Manually trigger watchlist build
curl -X POST "${SERVICE_URL}/api/build-watchlist"

# Check if file was created
gcloud logging read \
  "resource.labels.service_name=easy-etrade-strategy AND textPayload=~'dynamic_watchlist'" \
  --limit=10 \
  --project=easy-etrade-strategy
```

---

## 📊 **Expected API Usage (After Full Day)**

Monitor API usage after first trading day:

```bash
# Check ETrade API usage (if available via logs)
gcloud logging read \
  "resource.labels.service_name=easy-etrade-strategy AND textPayload=~'API'" \
  --limit=100 \
  --project=easy-etrade-strategy \
  --freshness=24h

Expected Daily Total:
✅ Watchlist scanning: 975 calls
✅ Position monitoring: 0 calls (no positions in signal_only mode)
✅ Account checks: 35 calls
✅ Total: ~1,010 calls/day (10.1% of 10,000 limit)
```

---

## 🎉 **Deployment Success Confirmation**

When ALL these pass, your system is **FULLY DEPLOYED** and **OPERATIONAL**:

1. ✅ Cloud Run service healthy
2. ✅ Trading thread active
3. ✅ Watchlist loaded (118 symbols)
4. ✅ ETrade integration working
5. ✅ Scanning every 2 minutes
6. ✅ Cloud Scheduler configured
7. ✅ Alert system functional
8. ✅ API usage within limits

**System is ready to generate signals in Demo mode!** 🚀

---

**Version**: 1.0  
**Created**: October 1, 2025  
**Status**: Ready for deployment validation

