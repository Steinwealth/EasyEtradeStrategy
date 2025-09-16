# Enhanced Alert System

## Overview

The Enhanced Alert System provides comprehensive notification capabilities for the ETrade Strategy, supporting multiple channels, intelligent filtering, and real-time monitoring. It ensures you stay informed about all critical trading events and system status.

## Alert Channels

### 1. Telegram Alerts
Primary notification channel with rich formatting and interactive features.

#### Configuration
```bash
# Environment variables
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TELEGRAM_ENABLED=true
TELEGRAM_MAX_MESSAGES_PER_MINUTE=20
```

#### Alert Types
- **Entry Signals**: New trade opportunities
- **Exit Signals**: Position exits and profit taking
- **Error Alerts**: System errors and failures
- **Performance Updates**: Daily/weekly performance summaries
- **System Status**: Health checks and maintenance alerts

#### Message Formatting
```python
def format_telegram_alert(alert_type, data):
    """Format alert for Telegram with rich text"""
    if alert_type == "entry_signal":
        return f"""
🚀 **ENTRY SIGNAL**
Symbol: {data['symbol']}
Price: ${data['price']:.2f}
Confidence: {data['confidence']:.1%}
Reason: {data['reason']}
Time: {data['timestamp']}
        """
    elif alert_type == "exit_signal":
        return f"""
💰 **EXIT SIGNAL**
Symbol: {data['symbol']}
Entry: ${data['entry_price']:.2f}
Exit: ${data['exit_price']:.2f}
P&L: {data['pnl']:.2f} ({data['pnl_pct']:.1%})
Reason: {data['reason']}
Time: {data['timestamp']}
        """
```

### 2. Webhook Alerts
Custom webhook integration for external systems and dashboards.

#### Configuration
```bash
# Environment variables
WEBHOOK_URL=https://your-webhook-endpoint.com/alerts
WEBHOOK_SECRET=your_webhook_secret
WEBHOOK_ENABLED=true
WEBHOOK_TIMEOUT_SECONDS=10
```

#### Webhook Payload
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "alert_type": "entry_signal",
  "severity": "info",
  "data": {
    "symbol": "AAPL",
    "price": 150.25,
    "confidence": 0.85,
    "reason": "RSI oversold with volume confirmation"
  },
  "system": {
    "service": "etrade-strategy",
    "version": "2.0",
    "environment": "production"
  }
}
```

### 3. Email Alerts
Email notifications for critical alerts and daily summaries.

#### Configuration
```bash
# Environment variables
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=etrade-strategy@yourdomain.com
EMAIL_TO=alerts@yourdomain.com
EMAIL_ENABLED=true
```

#### Email Templates
- **Daily Summary**: Performance overview and trade summary
- **Error Alerts**: Critical system errors requiring attention
- **Weekly Report**: Comprehensive performance analysis
- **System Maintenance**: Scheduled maintenance notifications

## Alert Types and Triggers

### 1. Trading Alerts

#### Entry Signals
```python
# Trigger conditions
- Signal confidence > 70%
- Volume confirmation
- Trend alignment
- Risk/reward ratio > 2:1

# Alert data
{
  "symbol": "AAPL",
  "price": 150.25,
  "confidence": 0.85,
  "reason": "RSI oversold with volume confirmation",
  "risk_reward": 2.5,
  "position_size": 100,
  "stop_loss": 145.00,
  "take_profit": 160.00
}
```

#### Exit Signals
```python
# Trigger conditions
- Stop loss hit
- Take profit reached
- Trailing stop triggered
- Signal reversal

# Alert data
{
  "symbol": "AAPL",
  "entry_price": 150.25,
  "exit_price": 155.50,
  "pnl": 525.00,
  "pnl_pct": 0.035,
  "reason": "Take profit reached",
  "hold_time": "2h 15m"
}
```

### 2. System Alerts

#### Error Alerts
```python
# Trigger conditions
- API failures
- Data provider errors
- Order execution failures
- System exceptions

# Alert data
{
  "error_type": "api_failure",
  "error_message": "Polygon API rate limit exceeded",
  "severity": "warning",
  "retry_count": 3,
  "last_success": "2024-01-15T10:25:00Z"
}
```

#### Performance Alerts
```python
# Trigger conditions
- High memory usage (>80%)
- High CPU usage (>90%)
- Slow response times (>5s)
- Low cache hit rate (<50%)

# Alert data
{
  "metric": "memory_usage",
  "value": 85.5,
  "threshold": 80.0,
  "severity": "warning",
  "recommendation": "Consider increasing memory allocation"
}
```

### 3. Market Alerts

#### Market Regime Changes
```python
# Trigger conditions
- Bull to bear market transition
- High volatility periods (VIX >30)
- Sector rotation events
- Economic news impact

# Alert data
{
  "regime_change": "bull_to_bear",
  "spy_price": 420.50,
  "vix_level": 25.5,
  "sector_rotation": "technology_to_utilities",
  "confidence": 0.75
}
```

## Alert Configuration

### 1. Alert Levels
```python
ALERT_LEVELS = {
    "CRITICAL": {
        "channels": ["telegram", "webhook", "email"],
        "throttle": 0,  # No throttling
        "retry": 5
    },
    "WARNING": {
        "channels": ["telegram", "webhook"],
        "throttle": 300,  # 5 minutes
        "retry": 3
    },
    "INFO": {
        "channels": ["telegram"],
        "throttle": 60,  # 1 minute
        "retry": 1
    }
}
```

### 2. Alert Filtering
```python
# Filter configuration
ALERT_FILTERS = {
    "trading_hours_only": True,
    "min_confidence": 0.7,
    "max_alerts_per_hour": 50,
    "duplicate_threshold": 300,  # 5 minutes
    "symbol_whitelist": ["AAPL", "MSFT", "GOOGL", "TSLA"],
    "exclude_after_hours": True
}
```

### 3. Throttling and Deduplication
```python
class AlertThrottler:
    def __init__(self):
        self.alert_history = {}
        self.throttle_rules = {
            "entry_signal": 60,  # 1 minute
            "exit_signal": 30,   # 30 seconds
            "error": 300,        # 5 minutes
            "performance": 600   # 10 minutes
        }
    
    def should_send_alert(self, alert_type, data):
        """Check if alert should be sent based on throttling rules"""
        key = f"{alert_type}_{data.get('symbol', 'system')}"
        now = time.time()
        
        if key in self.alert_history:
            last_sent = self.alert_history[key]
            throttle_time = self.throttle_rules.get(alert_type, 60)
            
            if now - last_sent < throttle_time:
                return False
        
        self.alert_history[key] = now
        return True
```

## Implementation

### 1. Alert Manager Class
```python
class AlertManager:
    def __init__(self):
        self.telegram = TelegramNotifier()
        self.webhook = WebhookNotifier()
        self.email = EmailNotifier()
        self.throttler = AlertThrottler()
        self.logger = logging.getLogger("alert_manager")
    
    def send_alert(self, alert_type, data, severity="INFO"):
        """Send alert through appropriate channels"""
        if not self.throttler.should_send_alert(alert_type, data):
            return
        
        # Format message
        message = self.format_message(alert_type, data)
        
        # Send to enabled channels
        if self.telegram.enabled and severity in ["INFO", "WARNING", "CRITICAL"]:
            self.telegram.send(message)
        
        if self.webhook.enabled and severity in ["WARNING", "CRITICAL"]:
            self.webhook.send(alert_type, data)
        
        if self.email.enabled and severity == "CRITICAL":
            self.email.send(alert_type, data)
        
        self.logger.info(f"Alert sent: {alert_type} - {severity}")
    
    def format_message(self, alert_type, data):
        """Format message based on alert type"""
        formatters = {
            "entry_signal": self.format_entry_signal,
            "exit_signal": self.format_exit_signal,
            "error": self.format_error_alert,
            "performance": self.format_performance_alert
        }
        
        formatter = formatters.get(alert_type, self.format_generic_alert)
        return formatter(data)
```

### 2. Integration with Trading System
```python
# In entry_executor.py
from modules.alerting import AlertManager

class EntryExecutor:
    def __init__(self):
        self.alert_manager = AlertManager()
    
    def execute_entry(self, signal):
        """Execute entry and send alert"""
        try:
            # Execute trade
            result = self._execute_trade(signal)
            
            # Send success alert
            self.alert_manager.send_alert("entry_signal", {
                "symbol": signal.symbol,
                "price": result.price,
                "confidence": signal.confidence,
                "reason": signal.reason,
                "position_size": result.quantity
            })
            
        except Exception as e:
            # Send error alert
            self.alert_manager.send_alert("error", {
                "error_type": "entry_execution_failed",
                "error_message": str(e),
                "symbol": signal.symbol
            }, severity="CRITICAL")
```

## Monitoring and Analytics

### 1. Alert Metrics
```python
class AlertMetrics:
    def __init__(self):
        self.metrics = {
            "total_alerts": 0,
            "alerts_by_type": {},
            "alerts_by_channel": {},
            "failed_deliveries": 0,
            "throttled_alerts": 0
        }
    
    def record_alert(self, alert_type, channel, success=True):
        """Record alert metrics"""
        self.metrics["total_alerts"] += 1
        self.metrics["alerts_by_type"][alert_type] = \
            self.metrics["alerts_by_type"].get(alert_type, 0) + 1
        self.metrics["alerts_by_channel"][channel] = \
            self.metrics["alerts_by_channel"].get(channel, 0) + 1
        
        if not success:
            self.metrics["failed_deliveries"] += 1
    
    def get_metrics(self):
        """Get current alert metrics"""
        return self.metrics.copy()
```

### 2. Alert Dashboard
```python
@app.route('/alerts/metrics')
def get_alert_metrics():
    """Get alert metrics for dashboard"""
    metrics = alert_manager.get_metrics()
    return jsonify(metrics)

@app.route('/alerts/history')
def get_alert_history():
    """Get recent alert history"""
    history = alert_manager.get_recent_alerts(limit=100)
    return jsonify(history)
```

## Best Practices

### 1. Alert Design
- **Clear and Concise**: Use clear language and formatting
- **Actionable**: Include relevant information for decision making
- **Consistent**: Use consistent formatting across all channels
- **Timely**: Send alerts as soon as possible after events

### 2. Channel Selection
- **Telegram**: Real-time trading alerts and quick updates
- **Webhook**: Integration with external systems and dashboards
- **Email**: Critical alerts and daily summaries

### 3. Throttling Strategy
- **Trading Alerts**: Minimal throttling for time-sensitive information
- **System Alerts**: Moderate throttling to avoid spam
- **Performance Alerts**: Higher throttling for non-critical metrics

### 4. Error Handling
- **Retry Logic**: Implement retry mechanisms for failed deliveries
- **Fallback Channels**: Use multiple channels for critical alerts
- **Graceful Degradation**: Continue operation even if alerting fails

This enhanced alert system ensures you stay informed about all critical trading events while avoiding alert fatigue through intelligent filtering and throttling.
