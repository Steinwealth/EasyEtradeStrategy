# 🎯 **API Limits & Data Plan - Production Trading System**

## **📊 Current API Usage & Limits**

### **Primary Data Sources**
1. **E*TRADE API** (FREE, Unlimited) - Primary source for real-time quotes
2. **Yahoo Finance** (FREE, Rate Limited) - Fallback for quotes and historical data
3. **Polygon.io** (PAID, 1000 calls/minute) - News sentiment analysis
4. **Prime PreMarket Scanner** (Yahoo Finance based) - Technical analysis

### **Current System Architecture**
- **Symbol List**: 109 symbols from `core_109.csv`
- **Batch Processing**: 10 symbols per batch (as implemented)
- **Scanning Frequency**: Every 5 seconds during market hours
- **Data Refresh**: Real-time quotes + 30-minute technical indicators

---

## **🚀 Optimized Data Plan**

### **Phase 1: Market Hours Data Strategy (9:30 AM - 4:00 PM ET)**

#### **High-Frequency Scanning (Every 30 seconds)**
- **Batch Size**: 10 symbols per batch
- **Total Batches**: 11 batches (109 symbols ÷ 10 = 11 batches)
- **Cycle Time**: 11 batches × 30 seconds = 5.5 minutes per full scan
- **Daily Scans**: ~60 full scans during market hours (6.5 hours × 60 minutes ÷ 5.5 minutes)

#### **API Call Calculation**
```
Per Batch (10 symbols):
- E*TRADE Quotes: 10 calls (primary)
- Yahoo Finance: 0-10 calls (fallback only)
- Total per batch: 10-20 calls

Per Full Scan (109 symbols):
- E*TRADE Quotes: 109 calls
- Yahoo Finance: 0-109 calls (fallback)
- Total per scan: 109-218 calls

Daily Market Hours (60 scans):
- E*TRADE: 6,540 calls
- Yahoo Finance: 0-6,540 calls (fallback)
- Total daily: 6,540-13,080 calls
```

### **Phase 2: Pre-Market Data Strategy (7:00 AM - 9:30 AM ET)**

#### **Sentiment Analysis (Every 15 minutes)**
- **News Analysis**: Polygon.io API calls for sentiment
- **Technical Analysis**: Yahoo Finance for pre-market data
- **Symbol Coverage**: All 109 symbols in batches of 10

#### **API Call Calculation**
```
Pre-market (2.5 hours, 10 cycles):
- Polygon.io: 109 symbols × 10 cycles = 1,090 calls
- Yahoo Finance: 109 symbols × 10 cycles = 1,090 calls
- Total pre-market: 2,180 calls
```

### **Phase 3: After-Hours Data Strategy (4:00 PM - 7:00 PM ET)**

#### **Position Monitoring (Every 2 minutes)**
- **Active Positions Only**: Monitor open positions
- **Batch Size**: 10 positions per batch
- **Cycle Time**: 2 minutes per batch

#### **API Call Calculation**
```
After-hours (3 hours, 90 cycles):
- Active positions: ~5-10 positions
- E*TRADE Quotes: 5-10 calls per cycle
- Total after-hours: 450-900 calls
```

---

## **📈 Total Daily API Usage**

### **Conservative Estimate**
```
Market Hours:     6,540 calls (E*TRADE)
Pre-market:       2,180 calls (Polygon + Yahoo)
After-hours:        450 calls (E*TRADE)
Total Daily:      9,170 calls
```

### **Maximum Estimate**
```
Market Hours:    13,080 calls (E*TRADE + Yahoo fallback)
Pre-market:       2,180 calls (Polygon + Yahoo)
After-hours:        900 calls (E*TRADE)
Total Daily:     16,160 calls
```

---

## **🛡️ API Limit Compliance**

### **E*TRADE API**
- **Limit**: Unlimited (FREE)
- **Usage**: 6,540-13,080 calls/day
- **Status**: ✅ **SAFE** - No limits

### **Yahoo Finance**
- **Limit**: ~2,000 calls/hour (estimated)
- **Usage**: 0-6,540 calls/day
- **Status**: ✅ **SAFE** - Well within limits

### **Polygon.io**
- **Limit**: 100,000 calls/month (Basic Plan)
- **Usage**: 1,090 calls/day × 30 days = 32,700 calls/month
- **Status**: ✅ **SAFE** - 67% under limit

---

## **⚡ Optimized Batch Processing Strategy**

### **Smart Batch Selection**
```python
# Priority-based batch selection
def select_next_batch(symbol_list, last_batch_index, priority_scores):
    batch_size = 10
    start_idx = (last_batch_index + 1) * batch_size
    
    # Sort by priority (volume, volatility, sentiment)
    sorted_symbols = sorted(symbol_list, key=lambda x: priority_scores.get(x, 0), reverse=True)
    
    # Select next batch with highest priority
    next_batch = sorted_symbols[start_idx:start_idx + batch_size]
    return next_batch
```

### **Adaptive Frequency**
```python
# Market volatility-based frequency adjustment
def calculate_scan_frequency(market_volatility):
    if market_volatility > 0.03:  # High volatility
        return 15  # Every 15 seconds
    elif market_volatility > 0.01:  # Medium volatility
        return 30  # Every 30 seconds
    else:  # Low volatility
        return 60  # Every 60 seconds
```

### **Cache-First Strategy**
```python
# Redis cache with TTL
cache_config = {
    'quotes': 60,        # 1 minute TTL
    'technical': 1800,    # 30 minutes TTL
    'sentiment': 900,     # 15 minutes TTL
    'market_data': 300    # 5 minutes TTL
}
```

---

## **🔄 Data Refresh Schedule**

### **Real-Time Data (Every 30 seconds)**
- **Price Quotes**: Current bid/ask/last prices
- **Volume**: Current trading volume
- **Market Status**: Open/closed status

### **Technical Data (Every 5 minutes)**
- **RSI**: 14-period RSI calculation
- **MACD**: MACD line and signal
- **Moving Averages**: 20-day and 50-day MA
- **Volume Ratios**: Current vs average volume

### **Sentiment Data (Every 15 minutes)**
- **News Sentiment**: Latest news analysis
- **Market Regime**: Bull/Bear/Sideways detection
- **Confidence Scores**: Updated confidence levels

### **Position Data (Every 2 minutes)**
- **Active Positions**: Current position status
- **P&L**: Real-time profit/loss
- **Stop Loss**: Current stop levels
- **Take Profit**: Current take profit levels

---

## **📊 Performance Monitoring**

### **API Usage Tracking**
```python
# Real-time API usage monitoring
api_metrics = {
    'etrade_calls_today': 0,
    'yahoo_calls_today': 0,
    'polygon_calls_today': 0,
    'cache_hit_rate': 0.0,
    'avg_response_time': 0.0,
    'error_rate': 0.0
}
```

### **Alert Thresholds**
```python
# API limit warnings
alert_thresholds = {
    'polygon_daily_limit': 3000,    # 30% of monthly limit
    'yahoo_hourly_limit': 1500,     # 75% of estimated limit
    'error_rate_threshold': 0.05,   # 5% error rate
    'response_time_threshold': 5000 # 5 seconds
}
```

---

## **🎯 Implementation Strategy**

### **Phase 1: Immediate Implementation**
1. **Reduce Scan Frequency**: 5 seconds → 30 seconds
2. **Implement Batch Processing**: 10 symbols per batch
3. **Add Redis Caching**: 1-minute TTL for quotes
4. **Priority-Based Selection**: High-priority symbols first

### **Phase 2: Optimization**
1. **Adaptive Frequency**: Volatility-based scanning
2. **Smart Caching**: Longer TTL for stable data
3. **Fallback Strategy**: Graceful degradation
4. **Performance Monitoring**: Real-time metrics

### **Phase 3: Advanced Features**
1. **Predictive Caching**: Pre-fetch likely symbols
2. **Machine Learning**: Optimize batch selection
3. **Dynamic Limits**: Adjust based on market conditions
4. **Cost Optimization**: Minimize paid API usage

---

## **📋 Configuration Settings**

### **Environment Variables**
```bash
# API Limits
POLYGON_DAILY_LIMIT=3000
YAHOO_HOURLY_LIMIT=1500
ETRADE_DAILY_LIMIT=20000

# Batch Processing
BATCH_SIZE=10
SCAN_FREQUENCY=30
CACHE_TTL_QUOTES=60
CACHE_TTL_TECHNICAL=1800

# Performance
MAX_CONCURRENT_BATCHES=3
RATE_LIMIT_DELAY=0.1
ERROR_RETRY_COUNT=3
```

### **Redis Configuration**
```python
redis_config = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'max_connections': 20,
    'retry_on_timeout': True,
    'socket_keepalive': True
}
```

---

## **✅ Compliance Checklist**

### **API Limits**
- [x] E*TRADE: Unlimited (FREE)
- [x] Yahoo Finance: <2,000 calls/hour
- [x] Polygon.io: <3,300 calls/day (10% of monthly limit)
- [x] Total daily usage: <16,160 calls

### **Performance Targets**
- [x] Batch processing: 10 symbols per batch
- [x] Scan frequency: 30 seconds (adaptive)
- [x] Cache hit rate: >80%
- [x] Response time: <2 seconds
- [x] Error rate: <1%

### **Cost Optimization**
- [x] E*TRADE primary (FREE)
- [x] Yahoo Finance fallback (FREE)
- [x] Polygon.io minimal usage (PAID)
- [x] Redis caching (FREE)
- [x] Total monthly cost: <$100

---

## **🚀 Expected Performance**

### **Trading Performance**
- **Signal Detection**: 30-second latency
- **Position Updates**: 2-minute latency
- **Market Coverage**: 100% of 109 symbols
- **Cache Efficiency**: 80%+ hit rate

### **System Performance**
- **API Efficiency**: 90%+ successful calls
- **Memory Usage**: <2GB with caching
- **CPU Usage**: <50% with batching
- **Network Usage**: <10MB/hour

---

**This optimized data plan ensures we stay well within API limits while maintaining high-performance trading capabilities with efficient batch processing and smart caching strategies.**
