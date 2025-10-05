# Alert System Documentation
## V2 ETrade Strategy - Comprehensive Alert Management

**Last Updated**: October 1, 2025  
**Version**: 2.2  
**Purpose**: Complete documentation of the alert system including Telegram notifications, OAuth alerts, trade signals, and end-of-day reports.

---

## 📋 **Table of Contents**

1. [Alert System Overview](#alert-system-overview)
2. [Telegram Integration](#telegram-integration)
3. [OAuth Token Alerts](#oauth-token-alerts)
4. [Trade Signal Alerts](#trade-signal-alerts)
5. [Demo Mode Alerts](#demo-mode-alerts)
6. [End-of-Day Reports](#end-of-day-reports)
7. [Alert Configuration](#alert-configuration)
8. [Alert Types and Levels](#alert-types-and-levels)
9. [Integration Guide](#integration-guide)
10. [Troubleshooting](#troubleshooting)

---

## 🚨 **Alert System Overview**

The V2 ETrade Strategy implements a comprehensive alert system that provides real-time notifications for all critical system events. The system is designed for 24/7 operation with intelligent throttling, rich formatting, and multi-channel delivery.

### **Core Features**

- **Multi-Channel Delivery**: Telegram, email, and webhook support
- **Intelligent Throttling**: Prevents alert spam while maintaining critical notifications
- **Rich Formatting**: Emoji-enhanced messages with structured data and HTML formatting
- **Priority Levels**: Critical, warning, info, and success classifications
- **Dual Timezone Support**: All alerts display both PT and ET times with AM/PM format
- **Historical Tracking**: Complete alert history and analytics
- **Mobile Optimization**: Responsive design for mobile devices

### **Alert Categories**

1. **OAuth Token Management**: Daily renewal reminders, expiry alerts, and status updates
2. **Trade Signals**: Entry/exit notifications with detailed trade information and emoji confidence system
3. **Demo Mode Validation**: Simulated trading alerts for system validation
4. **Performance Monitoring**: Real-time P&L updates and system status
5. **End-of-Day Summaries**: Comprehensive daily trading reports
6. **Holiday Alerts**: Future-proof holiday detection and market closure notifications
7. **System Alerts**: Error notifications and system health updates

---

## 📱 **Telegram Integration**

### **Setup Requirements**

1. **Bot Token**: Create a Telegram bot via @BotFather
2. **Chat ID**: Obtain your personal chat ID or channel ID
3. **Environment Variables**:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   TELEGRAM_PARSE_MODE=HTML
   TELEGRAM_ENABLED=true
   ```

### **Message Formatting Standards**

The alert system uses rich HTML formatting for better readability:

```python
# Standard Alert Format
message = f"""
===========================================================

🚀 <b>ALERT TITLE</b> — {pt_time} ({et_time})

📊 <b>Alert Details:</b> {details}
⏰ <b>Time:</b> {pt_time} ({et_time})
🔗 <b>Action Required:</b> {action}

<b>Status:</b> {status}
===========================================================
"""
```

### **Emoji Confidence System**

The system uses a comprehensive emoji-based confidence system for Buy Signals:

| Confidence Range | Emoji | Description | Usage |
|------------------|-------|-------------|-------|
| **98%+** | 🔰🔰🔰 | Ultra High Confidence | Perfect setup, exceptional conditions |
| **85-97%** | 🔰🔰 | High Confidence | Strong setup, very good conditions |
| **70-84%** | 🔰 | Medium Confidence | Good setup, solid conditions |
| **60-69%** | 📟 | Standard Confidence | Acceptable setup, moderate conditions |
| **<60%** | 🟡 | Lower Confidence | Basic setup, minimal conditions |

---

## 🔐 **OAuth Token Alerts**

### **Daily Renewal Process**

The OAuth alert system ensures continuous trading capability through automated token management:

#### **1. Token Expiry Alert (12:01 AM ET / 9:01 PM PT)**
- **Trigger**: Cloud Scheduler cron job
- **Purpose**: Alert when tokens just expired at midnight ET
- **Message**: Includes direct link to OAuth renewal page
- **Mobile Optimized**: One-tap access to renewal process

```
===========================================================

🌙 <b>OAuth Token Renewal Alert —</b> 21:01 PT (12:01 AM ET)

⚠️ <b>Action Required:</b> E*TRADE tokens just expired at midnight ET

🌐 <b>Public Dashboard:</b> https://easy-trading-oauth-v2.web.app
🦜💼 <b>Management Portal:</b> https://easy-trading-oauth-v2.web.app/manage.html

<b>Status:</b> Tokens expired - renewal required
<b>Expired:</b> Midnight ET (just now)
<b>Keep-Alive:</b> Running every 90 minutes until renewal

<b>Next Steps:</b>
1. Visit the public dashboard
2. Click "Renew Production" or "Renew Sandbox"
3. Enter access code (easy2025) on management portal
4. Complete the OAuth authorization flow
5. Tokens will be automatically renewed and stored in Secret Manager
```

#### **2. Market Open Alert (8:30 AM ET - Only if Production Token Invalid)**
- **Trigger**: Cloud Scheduler cron job
- **Purpose**: Final reminder 1 hour before market open
- **Condition**: Only sent if production tokens still invalid

#### **3. Token Renewal Success**
- **Trigger**: Successful token renewal and validation
- **Purpose**: Confirmation when tokens are successfully renewed
- **Validation**: Only sent if token validation confirms validity

```
===========================================================

✅ <b>OAuth Production Token Renewed —</b> 21:00 PT (12:00 AM ET)

🎉 <b>Success!</b> E*TRADE production token has been successfully renewed
⏰ <b>Renewed at:</b> 21:00 PT (12:00 AM ET)
☁️ <b>Cloud Keepalive:</b> ✅ Active — token will remain valid until expiry at 12:00 AM ET (midnight)

📊 <b>System Mode:</b> Live Trading Enabled
🔄 <b>Next Renewal:</b> Required before next market open

🌐 <b>Public Dashboard:</b> https://easy-trading-oauth-v2.web.app
🦜💼 <b>Management Portal:</b> https://easy-trading-oauth-v2.web.app/manage.html

💎 <b>Status:</b> Trading system ready and operational
```

#### **4. Token Expired Alert (Real-time Detection)**
- **Trigger**: Real-time token validation failure
- **Purpose**: Immediate notification when tokens are confirmed expired
- **Impact**: Trading operations disabled until renewal

---

## 📊 **Trade Signal Alerts**

### **Buy Signal Alert Format**

The system provides comprehensive buy signal alerts with detailed trade information:

```
===========================================================

📈 <b>TRADING SIGNAL ALERT</b> - 10:34 PT (1:34 PM ET)

📋 <b>BUY Signal Detected</b> • <b>Confidence: 98%</b>
🔰🔰🔰 <b>OPEN POSITION EXECUTED</b> - 10:34 PT (1:34 PM ET)

📊 <b>BUY</b> - 100 shares - GOOGL (Alphabet Inc.)
• Entry: $142.00
• Total Value: $14,200.00

💰 <b>Order Status:</b> FILLED
⏰ <b>Execution Time:</b> 10:34 PT (1:34 PM ET)
🆔 <b>Order ID:</b> 1234567901

📊 <b>Position Setup:</b>
• Stop Loss: $139.50 (-1.8%)
• Take Profit: $165.00 (+16.2%)
• Risk/Reward: 1:9.0
• Strategy: Quantum Perfect Setup

🔍 <b>Signal Analysis:</b>
• RSI: 65.8 (Perfect momentum)
• Volume: 3.1x average (Exceptional interest)
• MACD: Strong bullish confirmation
• Trend: Perfect uptrend alignment
• Support: $140.00 (Very strong support)

📊 <b>Performance Summary:</b>
• Signal Quality: Ultra High Confidence (98%)
• Entry Strategy: Perfect Setup
• Risk Management: Quantum trailing
• Target: 16.2% profit potential
• Strategy: Quantum
```

### **Exit Signal Format**

```
📤 <b>POSITION CLOSED</b> 📤

📊 Symbol: {symbol}
📈 Action: {action}
💰 Exit Price: ${price:.2f}
📦 Quantity: {quantity}
💵 P&L: ${pnl:.2f} ({pnl_pct:.1%})
📋 Strategy: {strategy}
⏰ Time: {timestamp}

💡 Reason: {reason}
```

---

## 🎯 **Demo Mode Alerts**

### **Simulated Entry Alert Format**

Demo Mode provides complete trading cycle validation with simulated position tracking:

```
📈 BUY SIGNAL - TQQQ 🔰🔰🔰

📊 BUY - 50 shares - TQQQ ETF  
Entry: $48.50 • Total Value: $2,425.00

🎯 SIMULATED (Signal-Only Mode) - Position tracked for exit timing validation

💼 POSITION DETAILS:
Symbol: TQQQ
Confidence: 95%
Expected Return: 6.5%
Quality Score: 52%

📊 RISK MANAGEMENT:
Stop Loss: $47.04 (3.0%)
Take Profit: $51.00 (5.2%)

⏰ Entry Time: 10:34:15 UTC
```

### **Simulated Exit Alert Format**

```
📉 SELL SIGNAL - TQQQ

📊 SELL - 50 shares - TQQQ • Exit: $49.00

Order Status: SIMULATED (Signal-Only Mode)

💼 POSITION CLOSED:
Entry: $48.50
Exit: $49.00
P&L: +$25.00 (+1.03%)
Duration: 34 minutes

🎯 EXIT REASON:
Trailing Stop Hit (Breakeven Protection)

💎 DEMO VALIDATION:
Simulated Performance: 100% win rate
Total Simulated P&L: +$25.00

⏰ Exit Time: 11:08:23 UTC

🎯 Signal-Only Mode: This validates the system would have closed this position at $49.00 in Live Mode
```

---

## 📈 **End-of-Day Reports**

### **Daily Summary Format**

```
===========================================================

📊 <b>END OF DAY TRADE REPORT</b> - Monday, October 1, 2025

💰 <b>PERFORMANCE SUMMARY</b>
📈 <b>Total Trades:</b> 8
🎯 <b>Win Rate:</b> 87.5%
💵 <b>Total P&L:</b> $1,245.30
📊 <b>Daily Return:</b> 2.4%
🏆 <b>Best Trade:</b> $425.50
📉 <b>Worst Trade:</b> -$85.20

📋 <b>STRATEGY BREAKDOWN</b>
• Quantum Strategy: 3 trades, 100% win rate, $890.40
• Advanced Strategy: 4 trades, 75% win rate, $445.10
• Standard Strategy: 1 trade, 100% win rate, -$90.20

🛡️ <b>RISK METRICS</b>
📉 <b>Max Drawdown:</b> 0.8%
⚖️ <b>Risk-Adjusted Return:</b> 2.1
📊 <b>Average Position Size:</b> $2,450.00

🔧 <b>SYSTEM STATUS</b>
✅ <b>ETrade API:</b> Healthy (1,180 calls used)
✅ <b>Data Feed:</b> Real-time (99.9% uptime)
✅ <b>Alerts:</b> All systems operational

⏰ <b>Report Generated:</b> 4:30 PM PT (7:30 PM ET)
===========================================================
```

---

## ⚙️ **Alert Configuration**

### **Environment Variables**

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_PARSE_MODE=HTML
TELEGRAM_ENABLED=true

# Alert Settings
ALERT_ENABLED=true
ALERT_THROTTLE_SECONDS=60
ALERT_MAX_PER_HOUR=50

# OAuth Alerts
OAUTH_ALERT_ENABLED=true
OAUTH_MORNING_HOUR=21
OAUTH_MARKET_OPEN_HOUR=5
OAUTH_RENEWAL_URL=https://easy-trading-oauth-v2.web.app
OAUTH_TIMEZONE=America/Los_Angeles

# Trade Alerts
TRADE_ALERT_ENABLED=true
TRADE_CONFIDENCE_THRESHOLD=0.7
TRADE_MIN_SIZE=100
STOCK_DETAILS_FORMAT=true

# EOD Reports
EOD_REPORT_ENABLED=true
END_OF_DAY_REPORT_TIME=16:30
EOD_REPORT_TIMEZONE=America/New_York
```

### **Alert Manager Configuration**

```python
# Alert Manager Settings
alert_config = {
    "telegram": {
        "enabled": True,
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        "parse_mode": "HTML",
        "throttle_seconds": 60,
        "max_per_hour": 50
    },
    "oauth": {
        "enabled": True,
        "morning_alert_time": "21:00",  # 9 PM PT
        "market_open_alert_time": "05:30",  # 5:30 AM PT
        "timezone": "America/Los_Angeles",
        "renewal_url": "https://easy-trading-oauth-v2.web.app"
    },
    "trading": {
        "enabled": True,
        "confidence_threshold": 0.7,
        "min_position_size": 100,
        "include_metadata": True,
        "emoji_confidence_system": True
    },
    "eod": {
        "enabled": True,
        "report_time": "16:30",  # 4:30 PM ET
        "timezone": "America/New_York",
        "include_charts": True
    }
}
```

---

## 🎯 **Alert Types and Levels**

### **Alert Levels**

| Level | Description | Usage | Example |
|-------|-------------|-------|---------|
| `CRITICAL` | System failure, immediate action required | OAuth token expired, API down | 🔴 **CRITICAL: OAuth token expired** |
| `ERROR` | Error condition, investigation needed | Failed trade execution, data error | ⚠️ **ERROR: Trade execution failed** |
| `WARNING` | Potential issue, monitoring required | Low confidence signal, high risk | ⚠️ **WARNING: Low confidence signal** |
| `INFO` | Informational message | Trade executed, position updated | ℹ️ **INFO: Position opened** |
| `SUCCESS` | Successful operation | Token renewed, trade profitable | ✅ **SUCCESS: Token renewed** |

### **Alert Types**

| Type | Description | Frequency | Priority |
|------|-------------|-----------|----------|
| `OAUTH_RENEWAL` | Token expiry alert | Daily 12:01 AM | High |
| `OAUTH_FALLBACK` | Fallback renewal alert | Daily 7:30 AM | Critical |
| `OAUTH_TOKEN_RENEWED_CONFIRMATION` | Token renewal confirmation | As needed | Medium |
| `OAUTH_EXPIRED` | Token confirmed expired | Real-time | Critical |
| `TRADE_ENTRY` | New trade signal | Every 2 minutes | High |
| `TRADE_EXIT` | Position closed | Every 60 seconds | High |
| `DEMO_MOCK_TRADING` | Demo mode simulation | As needed | Medium |
| `PERFORMANCE_UPDATE` | P&L update | Every trade | Medium |
| `EOD_SUMMARY` | End-of-day report | Daily 4:30 PM | Medium |
| `SYSTEM_STATUS` | System health update | Hourly | Low |

---

## 🔗 **Integration Guide**

### **PrimeAlertManager Class Usage**

```python
from modules.prime_alert_manager import PrimeAlertManager, AlertType, AlertLevel

# Initialize alert manager
alert_manager = PrimeAlertManager()

# Send OAuth renewal alert
await alert_manager.send_oauth_morning_alert()

# Send trade signal alert
await alert_manager.send_trade_execution_alert(
    symbol="AAPL",
    side="BUY",
    price=150.25,
    quantity=100,
    trade_id="AAPL_001",
    mode="LIVE"
)

# Send demo mode alert
await alert_manager.send_alert(
    AlertType.DEMO_MOCK_TRADING,
    AlertLevel.INFO,
    "Demo Trade Executed",
    "Mock position created for validation"
)

# Send end-of-day report
await alert_manager.send_eod_report(eod_report_data)
```

### **Alert Data Structures**

```python
@dataclass
class Alert:
    alert_id: str
    alert_type: AlertType
    level: AlertLevel
    title: str
    message: str
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    confidence: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TradeAlert:
    symbol: str
    strategy: str
    action: str  # "BUY" or "SELL"
    price: float
    quantity: int
    confidence: float
    trade_id: str
    mode: str  # "LIVE" or "DEMO"
    timestamp: datetime = field(default_factory=datetime.now)
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### 1. Telegram Notifications Not Working
**Symptoms**: No alerts received via Telegram
**Solutions**:
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check `TELEGRAM_CHAT_ID` format
- Ensure bot is not blocked
- Test with `/start` command

#### 2. OAuth Alerts Not Triggering
**Symptoms**: No morning renewal alerts
**Solutions**:
- Check Cloud Scheduler configuration
- Verify cron job is enabled
- Check timezone settings
- Review Cloud Run logs

#### 3. Alert Throttling Issues
**Symptoms**: Alerts being suppressed
**Solutions**:
- Adjust `ALERT_THROTTLE_SECONDS`
- Increase `ALERT_MAX_PER_HOUR`
- Check for duplicate alert conditions

#### 4. Message Formatting Issues
**Symptoms**: Malformed or incomplete messages
**Solutions**:
- Check HTML formatting syntax
- Verify string formatting
- Review message length limits
- Test with simple messages first

### **Debug Commands**

```python
# Test alert system
await alert_manager.test_alert()

# Check configuration
alert_manager.print_config()

# View alert history
alert_manager.get_alert_history(limit=10)

# Test specific alert type
await alert_manager.send_test_alert(AlertType.OAUTH_RENEWAL)
```

---

## 🚀 **Getting Started**

### **Quick Setup**

1. **Configure Telegram Bot**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   export TELEGRAM_PARSE_MODE="HTML"
   ```

2. **Initialize Alert Manager**:
   ```python
   from modules.prime_alert_manager import PrimeAlertManager
   
   alert_manager = PrimeAlertManager()
   await alert_manager.initialize()
   ```

3. **Send Test Alert**:
   ```python
   await alert_manager.send_alert(
       AlertType.SYSTEM_STATUS,
       AlertLevel.INFO,
       "System Started",
       "Alert system is now active"
   )
   ```

### **Integration Example**

```python
import asyncio
from modules.prime_alert_manager import PrimeAlertManager, AlertType, AlertLevel

async def main():
    # Initialize alert manager
    alert_manager = PrimeAlertManager()
    await alert_manager.initialize()
    
    # Send OAuth renewal alert
    await alert_manager.send_oauth_morning_alert()
    
    # Send trade signal alert
    await alert_manager.send_trade_execution_alert(
        symbol="AAPL",
        side="BUY", 
        price=150.25,
        quantity=100,
        trade_id="AAPL_001",
        mode="LIVE"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📞 **Support**

For issues and questions regarding the alert system:

1. **Check Logs**: Review Cloud Run logs for error messages
2. **Test Configuration**: Use debug commands to verify setup
3. **Review Documentation**: Check this guide for common solutions
4. **Contact Support**: Reach out for advanced troubleshooting

---

**Alert System Documentation - Complete and Ready for Production!** 🚀

*Last Updated: October 1, 2025*  
*Version: 2.2*  
*Maintainer: V2 ETrade Strategy Team*