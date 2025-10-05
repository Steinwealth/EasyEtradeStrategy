# ETrade Strategy - Prime Settings & Configuration

## Overview
The V2 ETrade Strategy uses a **prime configuration system** with multiple deployment modes and environment-based settings for flexible operation across different market conditions and performance requirements. The system is designed for 24/7 operation in Google Cloud with seamless configuration management.

## 🚀 Prime Configuration Benefits

### **System Consolidation**
- **6 Core Modules**: All functionality consolidated into high-performance modules
- **Prime Configuration Manager**: Single configuration management system
- **Environment-Based**: Development, production, sandbox modes
- **Mode-Specific**: Standard, Advanced, Quantum overrides
- **Hot Reloading**: Runtime configuration updates

### **Critical Features Configuration**
- **News Sentiment Analysis**: Multi-source news aggregation configuration
- **Move Capture System**: Explosive move detection and trailing stop settings
- **Quantum Strategy Engine**: ML-enhanced strategy configuration
- **Async Data Processing**: High-performance data processing settings
- **Multi-Tier Timing System**: Daily watchlist, hourly symbol updates, 2-min signals, 60-sec positions
- **Unified Models Integration**: PrimeSignal, PrimePosition, PrimeTrade data structure configuration

## Unified Configuration System

The ETrade Strategy implements a comprehensive unified configuration system that consolidates all environment variables into a structured, maintainable, and scalable configuration management system.

## 🕐 Multi-Tier Timing Configuration

### **System Timing Architecture**
The trading system implements a sophisticated multi-tier timing system for optimal performance:

#### **Daily Operations**
- **Watchlist Building**: 7:00 AM ET (once daily) - 118 symbols from core_109.csv
- **Mid-day Initialization**: Automatic watchlist building if missing/stale

#### **Hourly Operations**
- **Symbol Selector Updates**: Every 1 hour - Fresh analysis of top 50 high-probability symbols
- **Quality Reassessment**: RSI, volume, momentum, technical analysis updates

#### **High-Frequency Operations**
- **Multi-Strategy Manager**: Every 2 minutes - Cross-validation screening
- **Production Signal Generator**: Every 2 minutes - Final BUY signal confirmation
- **Position Monitoring**: Every 60 seconds - OPEN trades monitoring

#### **Configuration Variables**
```env
# Timing Configuration
WATCHLIST_BUILD_TIME=07:00              # Daily watchlist building (ET)
SYMBOL_UPDATE_INTERVAL=3600             # Symbol selector updates (seconds)
SIGNAL_SCAN_INTERVAL=120                # Signal generation (seconds)
POSITION_MONITOR_INTERVAL=60            # Position monitoring (seconds)
MARKET_OPEN_BUFFER=30                   # Market open buffer (minutes)
MARKET_CLOSE_BUFFER=30                  # Market close buffer (minutes)
```

### Configuration Structure
```
configs/
├── base.env                    # Core system configuration
├── data-providers.env          # Data provider settings
├── strategies.env              # Strategy-specific parameters
├── position-sizing.env         # Position sizing configuration
├── risk-management.env         # Risk management settings
├── automation.env              # Automation mode settings
├── alerts.env                  # Alerting configuration
├── deployment.env              # Deployment settings
├── trading-parameters.env      # Trading parameters
├── modes/                      # Strategy mode overrides
│   ├── standard.env           # Standard strategy
│   ├── advanced.env           # Advanced strategy
│   └── quantum.env            # Quantum strategy
└── environments/               # Environment-specific settings
    ├── development.env        # Development environment
    ├── production.env         # Production environment
    ├── optimized_development.env # Optimized development
    └── optimized_production.env  # Optimized production
```

### Configuration Loading System
The system automatically combines configuration files based on the selected mode and environment:

1. **Base Configuration** - Core system settings
2. **Data Providers** - Data source configuration  
3. **Strategies** - Strategy parameters
4. **Position Sizing** - Position sizing and boosting configuration
5. **Risk Management** - Risk management settings
6. **Automation** - Automation mode settings
7. **Alerts** - Alerting configuration
8. **Deployment** - Deployment settings
9. **Trading Parameters** - Trading-specific parameters
10. **Mode Override** - Strategy-specific overrides
11. **Environment Override** - Environment-specific settings

## Position Sizing Configuration

### **Position Sizing System**
The system implements a comprehensive position sizing system with multiple boosting scenarios:

#### **Base Position Sizing**
- **Base Position Size**: 10% of available capital
- **Maximum Position Size**: 35% absolute cap
- **Minimum Position Size**: 1% minimum
- **Position Splitting**: Even distribution from 80% trading capital

#### **80/20 Rule Implementation**
- **Trading Capital**: 80% of available capital for trading
- **Cash Reserve**: 20% buffer for risk management
- **Available Capital**: Cash + current ETrade Strategy positions
- **Position Splitting**: New positions split evenly from trading capital

#### **Boosting Scenarios**
- **Confidence-Based**: 1.0x to 1.5x multipliers based on signal confidence
- **Strategy Agreement**: 25% to 100% bonuses for multiple strategy confirmation
- **Profit-Based Scaling**: 1.1x to 1.8x multipliers based on account growth
- **Win Streak**: Framework for consecutive win position scaling

#### **Position Sizing Configuration File**
The `position-sizing.env` file contains all position sizing parameters:

```env
# Base Position Sizing
BASE_POSITION_SIZE_PCT=10.0
MAX_POSITION_SIZE_PCT=35.0
MIN_POSITION_SIZE_PCT=1.0
MIN_POSITION_VALUE=50.0

# 80/20 Rule Configuration
TRADING_CASH_PCT=80.0
CASH_RESERVE_PCT=20.0
POSITION_SPLITTING_ENABLED=true

# Confidence-Based Boosting
ULTRA_HIGH_CONFIDENCE_THRESHOLD=0.995
HIGH_CONFIDENCE_THRESHOLD=0.95
MEDIUM_CONFIDENCE_THRESHOLD=0.90
ULTRA_HIGH_CONFIDENCE_MULTIPLIER=1.5
HIGH_CONFIDENCE_MULTIPLIER=1.2
MEDIUM_CONFIDENCE_MULTIPLIER=1.0

# Strategy Agreement Boosting
AGREEMENT_MEDIUM_BONUS=0.25
AGREEMENT_HIGH_BONUS=0.50
AGREEMENT_MAXIMUM_BONUS=1.00

# Profit-Based Scaling
PROFIT_SCALING_200_PCT_MULTIPLIER=1.8
PROFIT_SCALING_100_PCT_MULTIPLIER=1.4
PROFIT_SCALING_50_PCT_MULTIPLIER=1.2
PROFIT_SCALING_25_PCT_MULTIPLIER=1.1

# Win Streak Boosting
WIN_STREAK_ENABLED=true
WIN_STREAK_BASE_MULTIPLIER=1.0
WIN_STREAK_MAX_MULTIPLIER=2.0
WIN_STREAK_TRACKING_DAYS=30
```

## Configuration Improvements & Analysis

### **Configuration System Enhancements**
- **File Consolidation**: Reduced from 17 to 8 core configuration files (53% reduction)
- **Standardization**: Consistent naming conventions and value formats across all files
- **ETRADE Integration**: ETRADE-first approach implemented throughout all configurations
- **Cost Optimization**: Aligned to $100/month total cost with proper call limits
- **Validation**: Type checking and range validation for all configuration values
- **OAuth Keep-Alive**: Consolidated keepalive_oauth.py system with 90-minute intervals
- **Position Sizing**: Comprehensive position sizing system with 80/20 rule and boosting scenarios

### **Configuration Analysis Results**
- **API Call Limits**: Standardized to 3,910 calls/day for ETRADE (39.1% of 10,000 limit), 1,200 for Alpha Vantage
- **Symbol Management**: 118 symbols in dynamic watchlist, scanned every 2 minutes
- **Cost Management**: Total monthly cost optimized to $100 (ETRADE: $0, Alpha Vantage: $50, Google Cloud: $50)
- **Performance Settings**: Optimized for <100ms latency and 99.9% uptime
- **Monitoring Frequencies**: Watchlist scanning every 2 minutes, position monitoring every 60 seconds
- **Security**: Enhanced with proper secret management and environment separation

### **Environment Management**
- **Development Environment**: Full debugging and testing capabilities
- **Production Environment**: Optimized for performance and reliability
- **Sandbox Environment**: ETRADE sandbox for safe testing
- **Configuration Inheritance**: Base → Environment → Mode override system

## 🔧 Configuration Improvements Summary

### **Configuration System Enhancements**
- **File Consolidation**: Reduced from 17 to 8 core configuration files (53% reduction)
- **Standardization**: Consistent naming conventions and value formats across all files
- **ETRADE Integration**: ETRADE-first approach implemented throughout all configurations
- **Cost Optimization**: Aligned to $100/month total cost with proper call limits
- **Validation**: Type checking and range validation for all configuration values
- **OAuth Keep-Alive**: Consolidated keepalive_oauth.py system with 90-minute intervals

### **Configuration Analysis Results**
- **API Call Limits**: Standardized to 3,910 calls/day for ETRADE (39.1% of 10,000 limit), 1,200 for Alpha Vantage
- **Symbol Management**: 118 symbols in dynamic watchlist, scanned every 2 minutes
- **Cost Management**: Total monthly cost optimized to $100 (ETRADE: $0, Alpha Vantage: $50, Google Cloud: $50)
- **Performance Settings**: Optimized for <100ms latency and 99.9% uptime
- **Monitoring Frequencies**: Watchlist scanning every 2 minutes, position monitoring every 60 seconds
- **Security**: Enhanced with proper secret management and environment separation

### **Configuration Quality Improvements**
- **Type Safety**: Configuration validator with type checking and range validation
- **Dependency Validation**: Related fields validation and ETRADE-specific rules
- **Data Structures**: Standardized Quote, Bar, MarketData, Signal, Position, Alert structures
- **Error Handling**: Comprehensive error handling and validation feedback
- **Documentation**: Inline documentation and examples for all configuration options

## Key Configuration Parameters

### Trading Parameters
```env
# Risk Management
RESERVE_CASH_PCT=20                    # Reserve 20% cash floor
ALLOC_PCT_DEFAULT=25                   # Default allocation per trade
PER_TRADE_RISK_CAP_PCT=10              # Max risk per trade (10% of equity)
PER_TRADE_ALLOC_CAP_PCT=25             # Max allocation per trade

# Stop Loss & Take Profit
ATR_MULTIPLIER_STOP=1.5                # ATR multiplier for stop loss
TP_TRIM_PCT=25                         # Take profit percentage
TP2_PCT=45                             # Second take profit level
ENABLE_TP2=true                        # Enable partial profit taking

# Entry Validation
SPREAD_BPS_LIMIT=40                    # Max spread in basis points (0.4%)
MIN_TOB_SIZE=200                       # Minimum top-of-book size
MAX_SLIPPAGE_PCT=0.8                   # Max acceptable slippage
ENTRY_PRICE_BUFFER_PCT=0.10            # Entry price safety buffer

# Enhanced RSI Criteria
RSI_BUY_THRESHOLD=55.0                 # RSI > 55 signals Buy positions opening
RSI_STRONG_BUY_THRESHOLD=70.0          # RSI > 70 indicates Strong Buy conditions
RSI_CONSIDER_BUY_THRESHOLD=50.0        # RSI > 50 may be considered for buys
RSI_CLOSE_THRESHOLD=50.0               # Close positions if RSI < 50
RSI_NO_TRADE_THRESHOLD=45.0            # No trading if RSI < 45

# Opening Range Breakout (ORB) Configuration
ORB_START_TIME=09:30                   # ORB window start (9:30 AM ET)
ORB_END_TIME=09:45                     # ORB window end (9:45 AM ET)
# ORB Scoring System:
# +1.0: Price above 15-minute opening candle highest high (strong buy opportunity)
# +0.5: Price above 15-minute opening candle lowest low (moderate buy opportunity)  
# -1.0: Price below 15-minute opening candle lowest low (no buy opportunity)
ORB_BREAKOUT_WEIGHT=0.3                # Weight for ORB in confidence calculation

# Volume Surge Detection
VOLUME_MAJOR_SURGE_THRESHOLD=2.0       # 100% above average volume
VOLUME_EXPLOSIVE_SURGE_THRESHOLD=3.0   # 200% above average volume
SELLING_VOLUME_PROTECTION_THRESHOLD=-0.4  # Threshold for selling volume protection
VOLUME_SURGE_WEIGHT=0.2                # Weight for volume surge in confidence
```

### Data Provider Configuration
```env
# Data Priority - E*TRADE as primary
DATA_PRIORITY=etrade,alpha_vantage,yfinance
FAILOVER_BAD_PULLS=3                   # Failover threshold

# E*TRADE Configuration
ETRADE_CONSUMER_KEY=your_key_here      # E*TRADE API credentials
ETRADE_CONSUMER_SECRET=your_secret
ETRADE_SANDBOX=false                   # Use sandbox mode
ETRADE_TOKENS_PATH=data/etrade_tokens.json

# Alpha Vantage Configuration
ALPHA_VANTAGE_API_KEY=your_key_here    # Alpha Vantage API key
ALPHA_VANTAGE_TIMEOUT=30               # Request timeout
ALPHA_VANTAGE_RETRIES=3                # Retry attempts

# Market Data
TIMEFRAME=1m                           # Primary timeframe
WATCHLIST_FILE=data/hybrid_watchlist.csv
```

### Execution Settings
```env
# Broker Configuration
BROKER_TYPE=etrade                     # Primary broker
ETRADE_CONSUMER_KEY=your_key           # E*TRADE API credentials
ETRADE_CONSUMER_SECRET=your_secret
ETRADE_SANDBOX=false                   # Use sandbox mode

# Order Management
BOT_TAG=EES                            # Bot position identifier
HIDDEN_STOPS=true                      # Software-managed stops
AUTOMATION_MODE=on                     # Enable automated trading
```

### Enhanced Alerting Configuration
```env
# Alert Channels
ALERT_CHANNELS=telegram,webhook,email
TELEGRAM_ALERTS_ENABLED=true
WEBHOOK_ALERTS_ENABLED=false
EMAIL_ALERTS_ENABLED=false

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_token          # Telegram bot token
TELEGRAM_CHAT_ID=your_chat_id          # Target chat ID
TELEGRAM_ALERT_TYPES=entry,exit,error,performance
TELEGRAM_MAX_MESSAGES_PER_MINUTE=20
TELEGRAM_PARSE_MODE=HTML               # Use HTML formatting for alerts

# Webhook Configuration
WEBHOOK_URL=your_webhook_url           # Custom webhook endpoint
WEBHOOK_SECRET=your_secret             # Webhook authentication
WEBHOOK_TIMEOUT_SECONDS=10

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=etrade-strategy@yourdomain.com
EMAIL_TO=alerts@yourdomain.com

# Alert Triggers
ALERT_ON_ENTRY_SIGNALS=true
ALERT_ON_EXIT_SIGNALS=true
ALERT_ON_ERRORS=true
ALERT_ON_PERFORMANCE_ISSUES=true
ALERT_ON_DATA_FAILURES=true
ALERT_ON_API_LIMITS=true

# Buy Signal Emoji Confidence System
BUY_SIGNAL_EMOJI_ULTRA_HIGH=🔰🔰🔰      # 98%+ confidence
BUY_SIGNAL_EMOJI_HIGH=🔰🔰              # 85-97% confidence
BUY_SIGNAL_EMOJI_MEDIUM=🔰              # 70-84% confidence
BUY_SIGNAL_EMOJI_STANDARD=📟            # 60-69% confidence
BUY_SIGNAL_EMOJI_LOWER=🟡               # <60% confidence

# OAuth Alert Configuration
OAUTH_ALERTS_ENABLED=true              # Enable OAuth renewal alerts
OAUTH_RENEWAL_URL=https://easy-strategy-oauth.web.app
OAUTH_MORNING_HOUR=21                   # 9 PM PT (midnight ET)
OAUTH_MORNING_MINUTE=0
OAUTH_MARKET_OPEN_HOUR=5               # 5 AM PT (8:30 AM ET)
OAUTH_MARKET_OPEN_MINUTE=30
OAUTH_TIMEZONE=America/Los_Angeles     # Pacific Time

# Stock Details Display
STOCK_DETAILS_ENABLED=true             # Show stock details in buy alerts
STOCK_DETAILS_FORMAT=📊 BUY - {shares} shares - {symbol} ({company}) • Entry: ${price} • Total Value: ${value}

# End of Day Reports
END_OF_DAY_REPORTS_ENABLED=true        # Enable daily performance reports
END_OF_DAY_REPORT_TIME=16:30           # 4:30 PM ET
END_OF_DAY_REPORT_TIMEZONE=America/New_York
```

### Critical Features Configuration
```env
# News Sentiment Analysis
NEWS_SENTIMENT_ENABLED=true            # Enable news sentiment analysis
NEWS_SENTIMENT_WEIGHT=0.15             # Weight in confidence calculation
POLYGON_API_KEY=your_polygon_key       # Polygon.io API key
FINNHUB_API_KEY=your_finnhub_key       # Finnhub API key
NEWSAPI_KEY=your_newsapi_key           # NewsAPI key
NEWS_LOOKBACK_HOURS=24                 # Hours to look back for news
NEWS_CONFIDENCE_THRESHOLD=0.7          # Minimum confidence for news sentiment

# Move Capture System
MOVE_CAPTURE_ENABLED=true              # Enable move capture system
EXPLOSIVE_MOVE_THRESHOLD=2.0           # Threshold for explosive moves
VOLUME_SPIKE_THRESHOLD=1.5             # Volume spike threshold
MOMENTUM_THRESHOLD=1.0                 # Momentum threshold
SMALL_MOVE_MIN_PCT=1.0                 # Minimum percentage for small moves
MODERATE_MOVE_MIN_PCT=3.0              # Minimum percentage for moderate moves
LARGE_MOVE_MIN_PCT=5.0                 # Minimum percentage for large moves
EXPLOSIVE_MOVE_MIN_PCT=10.0            # Minimum percentage for explosive moves
MOON_MOVE_MIN_PCT=20.0                 # Minimum percentage for moon moves

# Quantum Strategy
QUANTUM_STRATEGY_ENABLED=true          # Enable quantum strategy
QUANTUM_TARGET_WEEKLY_RETURN=0.35      # 35% weekly target
QUANTUM_BASE_RISK_PER_TRADE=0.10       # 10% base risk per trade
QUANTUM_MAX_RISK_PER_TRADE=0.25        # 25% maximum risk per trade
QUANTUM_MIN_CONFIDENCE=0.95            # 95% minimum confidence
QUANTUM_ML_WEIGHT=0.4                  # ML weight in analysis
QUANTUM_TECHNICAL_WEIGHT=0.3           # Technical analysis weight
QUANTUM_VOLUME_WEIGHT=0.2              # Volume analysis weight
QUANTUM_SENTIMENT_WEIGHT=0.1           # Sentiment analysis weight

# Async Data Processing
ASYNC_PROCESSING_ENABLED=true          # Enable async processing
MAX_WORKERS=10                         # Number of worker threads
BATCH_SIZE=20                          # Batch size for processing
CONNECTION_POOL_SIZE=100               # Connection pool size
RATE_LIMIT_CALLS_PER_MINUTE=1000       # Rate limit for API calls
RATE_LIMIT_BURST_CAPACITY=100          # Burst capacity for rate limiting
DATA_CACHE_MAX_SIZE=1000               # Maximum cache size
DATA_CACHE_DEFAULT_TTL=300             # Default TTL for cache (seconds)
```

### Market Hours & Holidays
```env
# Timezone Configuration
TZ=America/New_York                    # Market timezone
MARKET_HOURS_START=09:30               # Market open time
MARKET_HOURS_END=16:00                 # Market close time

# Holiday Configuration
HOLIDAY_FILE=data/holidays_custom.json # Custom holiday calendar (2025-2035)
HOLIDAYS_ENABLED=true                  # Enable future-proof holiday system
DYNAMIC_HOLIDAY_CALCULATOR=true        # Use mathematical algorithms for any year
SKIP_PRE_MARKET=false                  # Skip pre-market trading
SKIP_AFTER_HOURS=false                 # Skip after-hours trading
```

### Logging & Monitoring
```env
# Logging Configuration
SESSION_LOG_LEVEL=INFO                 # Log level (DEBUG, INFO, WARNING, ERROR)
LOG_PATH=logs/signals.log              # Log file path
FILE_LOGGING=true                      # Enable file logging

# Performance Monitoring
METRICS_ENABLED=true                   # Enable metrics collection
HEALTH_CHECK_INTERVAL=60               # Health check frequency (seconds)
```

## Deployment Modes

### 1. Demo Mode (signal_only) - **RECOMMENDED FOR VALIDATION** ⭐
- **Complete position tracking** with simulated positions
- **Real ETrade data** for accurate market simulation
- **Entry signals** create simulated positions (no real trades)
- **Exit signals** generated by stealth trailing system
- **Telegram alerts** for both entry and exit
- **Performance metrics** tracked (win rate, P&L, exit timing)
- **Zero risk** - validates complete Buy→Sell cycle before live trading
- **Use Case**: 3-5 day validation period before switching to Live Mode

### 2. Standard Trading Mode
- Full automated trading with E*TRADE integration
- Real-time market data from E*TRADE with Alpha Vantage fallback
- Complete risk management and position sizing
- Hidden stop-loss and take-profit management

### 3. Alert-Only Mode
- No actual trading execution
- Signal generation and alerting only
- Useful for strategy validation and monitoring
- Reduced resource requirements

### 3. Cost-Optimized Mode
- Minimized data provider costs
- Reduced API call frequency
- Optimized for longer-term strategies
- Lower operational overhead

### 4. High-Performance Mode
- Maximum data refresh rates
- Ultra-low latency execution
- Advanced position sizing algorithms
- Real-time market scanning

### 5. Quantum Strategy Mode
- Advanced machine learning integration
- Dynamic strategy adaptation
- Multi-timeframe analysis
- Enhanced confidence scoring
- Target: 50% weekly return
- Risk: 10% base risk per trade (max 25%)
- Position Size: 30% of equity per trade
- Confidence Threshold: 90%

## Performance Optimization Settings

### High-Performance Configuration
```env
# Performance Configuration
POLL_SECONDS=0.5                    # Reduce polling frequency
MAX_WORKERS=8                       # Parallel processing workers
DATA_BATCH_SIZE=20                  # Batch size for data operations
SIGNAL_BATCH_SIZE=20                # Batch size for signal processing
INDICATOR_CACHE_TTL=30              # Cache TTL in seconds
DATA_CACHE_SIZE=1000                # Data cache size
FAILOVER_BAD_PULLS=2                # Reduce failover threshold

# Memory Optimization
MEMORY_CLEANUP_INTERVAL=300         # Cleanup every 5 minutes
MAX_HISTORICAL_BARS=1000            # Limit historical data retention
ENABLE_MEMORY_PROFILING=true        # Enable memory monitoring

# API Optimization
ALPHA_VANTAGE_RETRIES=3             # Alpha Vantage retry attempts
ENABLE_CONNECTION_POOLING=true      # Enable connection pooling
REQUEST_TIMEOUT=10                  # Request timeout in seconds
```

### Expected Performance Improvements
- **Latency Reduction**: 75% reduction in processing time
- **Memory Efficiency**: 60% reduction in memory usage
- **CPU Utilization**: 70%+ CPU utilization
- **API Efficiency**: 90%+ API quota utilization

## Strategy-Specific Configuration

### Standard Strategy Parameters
```env
STANDARD_TARGET_WEEKLY_RETURN=0.01     # 1% weekly target
STANDARD_BASE_RISK_PER_TRADE=0.02      # 2% base risk
STANDARD_MAX_RISK_PER_TRADE=0.05       # 5% maximum risk
STANDARD_MIN_QUALITY_SCORE=60          # 60% minimum quality
STANDARD_MIN_CONFIDENCE_SCORE=0.9      # 90% minimum confidence (6+ confirmations required)
STANDARD_POSITION_SIZE_PCT=10.0        # 10% position size
STANDARD_CONFIDENCE_MULTIPLIER=1.0     # 1x confidence multiplier
```

### Advanced Strategy Parameters
```env
ADVANCED_TARGET_WEEKLY_RETURN=0.10     # 10% weekly target
ADVANCED_BASE_RISK_PER_TRADE=0.05      # 5% base risk
ADVANCED_MAX_RISK_PER_TRADE=0.15       # 15% maximum risk
ADVANCED_MIN_QUALITY_SCORE=70          # 70% minimum quality
ADVANCED_MIN_CONFIDENCE_SCORE=0.9      # 90% minimum confidence (8+ score required)
ADVANCED_POSITION_SIZE_PCT=20.0        # 20% position size
ADVANCED_CONFIDENCE_MULTIPLIER=2.0     # 2x confidence multiplier
```

### Quantum Strategy Parameters
```env
QUANTUM_TARGET_WEEKLY_RETURN=0.50      # 50% weekly target
QUANTUM_BASE_RISK_PER_TRADE=0.10       # 10% base risk
QUANTUM_MAX_RISK_PER_TRADE=0.25        # 25% maximum risk
QUANTUM_MIN_QUALITY_SCORE=80           # 80% minimum quality
QUANTUM_MIN_CONFIDENCE_SCORE=0.95      # 95% minimum confidence (10+ quantum score required)
QUANTUM_POSITION_SIZE_PCT=30.0         # 30% position size
QUANTUM_CONFIDENCE_MULTIPLIER=5.0      # 5x confidence multiplier

# ML Configuration
ML_MODELS_ENABLED=true
ML_RETRAINING_INTERVAL=24
ML_FEATURE_ENGINEERING=true
ML_PATTERN_RECOGNITION=true
ML_CONFIDENCE_SCORING=true
```

## Alert System Configuration

### Buy Signal Emoji Confidence System
The enhanced alert system includes a comprehensive emoji-based confidence scoring system for Buy Signals:

#### **Confidence Levels & Emojis**
- **🔰🔰🔰 Ultra High Confidence (98%+)**: Perfect setup, exceptional conditions
- **🔰🔰 High Confidence (85-97%)**: Strong setup, very good conditions  
- **🔰 Medium Confidence (70-84%)**: Good setup, solid conditions
- **📟 Standard Confidence (60-69%)**: Acceptable setup, moderate conditions
- **🟡 Lower Confidence (<60%)**: Basic setup, minimal conditions

#### **Stock Details Display**
Buy Signal alerts now include comprehensive stock information:
- **Symbol & Company**: Full stock symbol and company name
- **Position Details**: Number of shares, entry price, total value
- **Format**: `📊 BUY - 100 shares - AAPL (Apple Inc.) • Entry: $150.25 • Total Value: $15,025.00`
- **Positioning**: Displayed between "OPEN POSITION EXECUTED" and "Order Status: FILLED"

### OAuth Integration Alerts
The system includes comprehensive OAuth token management alerts:

#### **Token Expiry Alerts (Midnight ET)**
- **Timing**: 12:00 AM ET (9:00 PM PT)
- **Format**: HTML with bold formatting and separators
- **Content**: Token status, renewal instructions, web app link
- **Web App**: Direct link to https://easy-strategy-oauth.web.app

#### **Market Open Alerts (8:30 AM ET)**
- **Trigger**: Only when production token is invalid
- **Timing**: 8:30 AM ET (5:30 AM PT)
- **Conditions**: 
  - If production valid: No alert sent
  - If sandbox valid: Demo mode reminder
  - If both invalid: Urgent system blocked alert

### End of Day Reports
Daily performance summaries with comprehensive metrics:
- **Timing**: 4:30 PM ET (1:30 PM PT)
- **Format**: HTML with bold formatting and separators
- **Content**: Trade summary, performance metrics, P&L analysis
- **Structure**: Clean, professional presentation

## Configuration Management

### Dynamic Configuration
The system supports runtime configuration changes through:
- REST API endpoints for parameter updates
- Configuration hot-reloading
- A/B testing capabilities
- Strategy switching without restart

### Validation
All configuration parameters are validated at startup:
- API key format validation
- Numeric range checks
- File path existence verification
- Broker connectivity testing

### Security
- Environment variable encryption for sensitive data
- API key rotation support
- Secure credential storage in Google Secret Manager
- Audit logging for configuration changes

## Google Cloud Configuration

### Cloud Run Settings
```env
# Cloud Run Configuration
CLOUD_RUN_REGION=us-west2
CLOUD_RUN_MEMORY=2Gi
CLOUD_RUN_CPU=2
CLOUD_RUN_CONCURRENCY=1
CLOUD_RUN_MAX_INSTANCES=1
CLOUD_RUN_TIMEOUT=3600

# Environment
ENVIRONMENT=production
STRATEGY_MODE=standard
AUTOMATION_MODE=live
```

### Secret Management
```env
# Google Secret Manager
SECRET_MANAGER_PROJECT_ID=your-project-id
TELEGRAM_BOT_TOKEN_SECRET=telegram-bot-token
TELEGRAM_CHAT_ID_SECRET=telegram-chat-id
ETRADE_CONSUMER_KEY_SECRET=etrade-consumer-key
ETRADE_CONSUMER_SECRET_SECRET=etrade-consumer-secret
ALPHA_VANTAGE_API_KEY_SECRET=alpha-vantage-api-key
```

## Performance Tuning

### Data Provider Optimization
- Intelligent failover between providers
- Request batching and caching
- Rate limiting and quota management
- Connection pooling

### Memory Management
- Efficient data structure usage
- Garbage collection optimization
- Memory leak prevention
- Resource cleanup on shutdown

### CPU Optimization
- Asynchronous processing where possible
- Thread pool management
- CPU-intensive task optimization
- Load balancing across cores

## Monitoring & Alerts

### Health Monitoring
- System health endpoints (`/healthz`, `/metrics`)
- Performance metrics collection
- Error rate monitoring
- Resource usage tracking

### Alerting System
- Multi-channel alert delivery (Telegram, webhook, email)
- Alert throttling and deduplication
- Escalation procedures
- Custom alert rules

### Logging
- Structured logging with JSON format
- Log rotation and archival
- Search and filtering capabilities
- Integration with Google Cloud Logging

## Best Practices

### Configuration Management
- **Version Control**: Track all configuration changes
- **Environment Separation**: Clear separation between dev/staging/prod
- **Security**: Encrypt sensitive configuration data
- **Validation**: Validate all configuration parameters

### Performance Optimization
- **Resource Monitoring**: Monitor CPU, memory, and network usage
- **Caching**: Implement intelligent caching strategies
- **Connection Pooling**: Use connection pooling for external APIs
- **Batch Processing**: Batch operations when possible

### Operational Excellence
- **Health Checks**: Implement comprehensive health checks
- **Graceful Shutdown**: Handle shutdown signals properly
- **Error Handling**: Implement robust error handling
- **Monitoring**: Set up comprehensive monitoring and alerting

## ⚠️ Configuration Issues & Recommendations

### **Main .env File Issues**
The current `.env` file has several outdated and inconsistent settings that should be addressed:

#### **❌ Critical Issues:**
1. **Outdated Data Provider Priority**: `DATA_PRIORITY=polygon,yfinance` should be `DATA_PRIORITY=etrade,alpha_vantage,polygon,yfinance`
2. **Missing E*TRADE Configuration**: Missing `ETRADE_ENABLED=true` and related settings
3. **Inconsistent Bot Tag**: `BOT_TAG=EUR-LY` should be `BOT_TAG=EES` (matches base.env)
4. **Missing Strategy Mode**: Missing `STRATEGY_MODE=standard` and `ENVIRONMENT=development`
5. **Empty Telegram Configuration**: Should use values from base.env

#### **✅ Recommended Actions:**
1. **Update .env file** with values from the comprehensive template
2. **Use E*TRADE as primary** data provider for real-time data
3. **Standardize bot tag** to `EES` across all configurations
4. **Add missing configuration** keys for proper system operation
5. **Validate configuration** using the improved config_loader.py

### **Configuration Template**
A comprehensive `.env.template` file should be created with all required settings and proper defaults.

## 🔧 Configuration System Improvements

### **Critical Issues Fixed**

#### **1. Data Provider Priority Consistency**
**Before**: Each mode file had different data provider priorities
**After**: All modes now use `DATA_PRIORITY=etrade,polygon,yfinance`

**Fixed Files:**
- ✅ `configs/modes/standard.env`: Updated from `yfinance,finviz,news_api` 
- ✅ `configs/modes/advanced.env`: Updated from `etrade,polygon,alpha_vantage,yahoo_finance`
- ✅ `configs/modes/quantum.env`: Updated from `etrade,polygon,alpha_vantage,yahoo_finance`
- ✅ `configs/modes/alert-only.env`: Updated from `yfinance,finviz,news_api`

#### **2. ETRADE API Call Limits Alignment**
**Before**: Inconsistent call limits across configuration files
**After**: Standardized to 1,510 calls/day (15.1% of 10,000 daily limit)

**Fixed Values:**
- ✅ `ETRADE_DAILY_CALL_LIMIT`: Updated to 1,510 calls/day
- ✅ `TARGET_DAILY_CALLS_ETRADE`: Updated to 1,510 calls/day
- ✅ Monitoring frequencies: Watchlist every 2 minutes, positions every 60 seconds

#### **3. Confidence Score Standardization**
**Before**: Inconsistent confidence requirements
**After**: All strategies require 90% confidence (0.9)

**Fixed Values:**
- ✅ `STANDARD_MIN_CONFIDENCE_SCORE`: 0.7 → 0.9
- ✅ `ADVANCED_MIN_CONFIDENCE_SCORE`: 0.8 → 0.9
- ✅ `QUANTUM_MIN_CONFIDENCE_SCORE`: 0.9 (already correct)

#### **4. Provider Budget Optimization**
**Before**: Unrealistic API budgets that would exceed free tiers
**After**: Conservative budgets aligned with free tier limits

**Updated Budgets:**
- **Standard Mode**: 
  - Polygon: 5 → 100 QPM
  - Alpha Vantage: 100 → 400 calls/day
- **Advanced Mode**:
  - Polygon: 1500 → 500 QPM
  - Alpha Vantage: 1200 → 800 calls/day
- **Quantum Mode**:
  - Polygon: 2000 → 1000 QPM
  - Alpha Vantage: 1200 → 1000 calls/day

### **Configuration Architecture Improvements**

#### **1. Clear Configuration Hierarchy**
```
.env (main, user-customizable)
├── configs/base.env (core settings)
├── configs/data-providers.env (data configuration)
├── configs/strategies.env (strategy parameters)
├── configs/environments/ (environment-specific)
└── configs/modes/ (strategy mode overrides)
```

#### **2. Consistent Naming Conventions**
- **ETRADE settings**: `ETRADE_*` prefix
- **Data priorities**: `DATA_PRIORITY` format
- **Rate limits**: `*_RATE_LIMIT_CALLS_PER_MINUTE`
- **Daily limits**: `*_DAILY_LIMIT`

#### **3. Environment-Specific Overrides**
- **Development**: Debug mode, sandbox APIs
- **Production**: Live trading, production APIs
- **Sandbox**: Testing mode with mock data

### **Configuration Validation**

#### **Required Settings Checklist:**
- [ ] `ETRADE_CONSUMER_KEY` and `ETRADE_CONSUMER_SECRET`
- [ ] `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- [ ] `DATA_PRIORITY` set to `etrade,polygon,yfinance`
- [ ] `STRATEGY_MODE` set to desired mode
- [ ] `ENVIRONMENT` set to `development` or `production`

#### **Validation Commands:**
```bash
# Test ETRADE connection
python scripts/etrade_connection_test.py

# Validate configuration
python scripts/validate_config.py

# Test data providers
python scripts/test_data_providers.py
```

### **Usage Instructions**

#### **1. Quick Start Configuration:**
```bash
# Copy base configuration
cp configs/base.env .env.local

# Edit with your credentials
nano .env.local

# Test configuration
python scripts/validate_config.py
```

#### **2. Mode Selection:**
```bash
# Standard mode (conservative)
./deploy-unified.sh deploy standard off

# Advanced mode (aggressive)
./deploy-unified.sh deploy advanced off

# Quantum mode (maximum risk)
./deploy-unified.sh deploy quantum off

# Alert-only mode (no trading)
./deploy-unified.sh deploy alert-only off
```

#### **3. Environment Selection:**
```bash
# Development (sandbox)
export ENVIRONMENT=development

# Production (live trading)
export ENVIRONMENT=production
```

### **Benefits of Improvements**

#### **1. Consistency**
- All configuration files now use consistent data provider priorities
- API call limits are aligned across all files
- Confidence scores are standardized

#### **2. ETRADE Optimization**
- Optimized for ETRADE free tier (1,180 calls/day)
- Batch requests for maximum efficiency
- Intelligent fallback to paid providers

#### **3. Cost Efficiency**
- Reduced external API usage
- Optimized budget allocation
- Free tier utilization maximized

#### **4. Maintainability**
- Clear configuration hierarchy
- Consistent naming conventions
- Easy to understand and modify

### **Configuration Files Status**

| File | Status | Issues Fixed |
|------|--------|--------------|
| `configs/modes/standard.env` | ✅ Fixed | Data priority, budgets |
| `configs/modes/advanced.env` | ✅ Fixed | Data priority, budgets |
| `configs/modes/quantum.env` | ✅ Fixed | Data priority, budgets |
| `configs/modes/alert-only.env` | ✅ Fixed | Data priority, budgets |
| `configs/data-providers.env` | ✅ Fixed | ETRADE limits, rate limits |
| `configs/strategies.env` | ✅ Fixed | Confidence scores |
| `.env` (main) | ⚠️ Needed | Create template file |

This comprehensive configuration system ensures flexible, secure, and optimized operation of the V2 ETrade Strategy across different environments and deployment scenarios.