# 📊 Trading Data Directory

This directory contains all data files for the trading system, organized into specialized subdirectories.

## 📁 Directory Structure

### **📋 Watchlist Data (`watchlist/`)**
- **`core_109.csv`** - Core 109 symbols organized by leverage (3x → 2x → 1x)
- **`dynamic_watchlist.csv`** - Dynamic watchlist sorted by market opportunities + sentiment
- **`complete_sentiment_mapping.json`** - Complete sentiment context for all 109 symbols
- **`sentiment_pairs_mapping.json`** - Bull/bear pair sentiment relationships
- **`trading_strategy_mapping.json`** - Complete trading strategy configuration
- **`stock_to_etf_mapping.csv`** - Stock to ETF mapping for leveraged trading
- **`sentiment_integration_strategy.md`** - News sentiment integration strategy documentation
- **`README.md`** - Watchlist documentation

### **📊 Prime Score Data (`score/`)**
- **`symbol_scores.json`** - Main data file containing all trade records and symbol rankings
- **`symbol_scores_backup.json`** - Backup file (updated every 100 trades)
- **`symbol_scores_test.json`** - Test data file with sample trades for demonstration
- **`initialize_prime_scores.py`** - Initialize the Prime Symbol Score system
- **`test_prime_scores.py`** - Test the system functionality without dependencies
- **`review_prime_ranks.py`** - Review rankings
- **`cloud_rank_review.py`** - Cloud data access
- **`prime_rank_dashboard.py`** - Web dashboard
- **`README.md`** - Prime score documentation

### **🧠 Sentiment Analysis Data**
- **`sentiment_history.json`** - Daily sentiment tracking data (30-day retention)
- **`sentiment_summary.json`** - Daily sentiment summaries and reports
- **`news_sentiment_cache.json`** - Cached news sentiment analysis results
- **`sentiment_cache.json`** - Premarket sentiment analysis cache for symbol selection

### **⚙️ System Data (Root)**
- **`holidays_custom.json`** - Custom holiday calendar
- **`state.json`** - System state file

### **🔐 Security & Credentials**
- **E*TRADE Tokens**: Managed by Google Secret Manager (Production & Sandbox)
- **Token Rotation**: Automatic daily updates after expiration
- **No Local Storage**: Sensitive credentials stored securely in cloud

#### **Google Secret Manager Integration**
```
Secret Names:
- etrade-production-oauth-token
- etrade-production-oauth-secret
- etrade-sandbox-oauth-token
- etrade-sandbox-oauth-secret
- etrade-production-expires-at
- etrade-sandbox-expires-at
```

#### **Token Management Process**
1. **Daily Check**: System checks token expiration
2. **Auto-Renewal**: Tokens refreshed before expiration
3. **Secret Update**: New tokens stored in Secret Manager
4. **Application Restart**: System restarts with new tokens
5. **Fallback**: Sandbox tokens used if production fails

## 🎯 Data Structure

### **📋 Watchlist System**

#### **Core List (`core_109.csv`)**
- **109 symbols** organized by leverage priority
- **3x Leverage**: 36 symbols (TQQQ, SQQQ, UPRO, SPXU, etc.)
- **2x Leverage**: 69 symbols (ERX, ERY, TSLL, TSLS, etc.)
- **1x Core**: 4 symbols (BTGD, BITX, UXRP, USD)
- **Static Reference**: Never modified, used as source for dynamic generation

#### **Dynamic Watchlist (`dynamic_watchlist.csv`)**
- **Real-time sorting** of all 109 symbols by market opportunities + sentiment
- **Sorting Criteria**: Volume (35%), Volatility (25%), Momentum (20%), **Sentiment (20%)**, Performance (10%)
- **Update Frequency**: Every 15 minutes during market hours
- **Generation Process**: `scanner.py → premarket_sentiment_analysis.py → build_dynamic_watchlist.py → dynamic_watchlist.csv`

#### **Sentiment Analysis System**
- **Complete Coverage**: 100% sentiment context for all 109 symbols
- **Premarket Analysis**: 7:00 AM ET news sentiment analysis for symbol selection
- **Bull/Bear Prioritization**: Strategic symbol selection based on news sentiment alignment
- **Real-time Tracking**: Hourly sentiment analysis during market hours
- **Bull/Bear Pairs**: Complete sentiment relationships for confidence boosting
- **News Sources**: Polygon, Finnhub, Finviz, Yahoo with weighted scoring

### **🧠 Sentiment Data Structure**

#### **Daily Sentiment Records (`daily_sentiments`)**
```json
{
  "2025-01-27": [
    {
      "symbol": "TQQQ",
      "date": "2025-01-27",
      "sentiment_score": 0.75,
      "confidence": 0.85,
      "news_count": 12,
      "source_breakdown": {"polygon": 8, "finnhub": 3, "finviz": 1},
      "keywords_matched": ["tech", "nasdaq", "growth", "AI"],
      "underlying": "Nasdaq-100",
      "category": "index",
      "leverage": "3x",
      "is_bull": true,
      "is_bear": false,
      "bear_etf": "SQQQ",
      "timestamp": "2025-01-27T15:30:00Z"
    }
  ]
}
```

#### **Sentiment History (`sentiment_history`)**
```json
{
  "TQQQ": [
    {
      "symbol": "TQQQ",
      "date": "2025-01-27",
      "sentiment_score": 0.75,
      "confidence": 0.85,
      "news_count": 12,
      "underlying": "Nasdaq-100",
      "category": "index",
      "leverage": "3x"
    }
  ]
}
```

#### **Daily Sentiment Summary (`sentiment_summary`)**
```json
{
  "2025-01-27": {
    "date": "2025-01-27",
    "total_symbols": 109,
    "positive_sentiment": 45,
    "negative_sentiment": 32,
    "neutral_sentiment": 32,
    "average_sentiment": 0.15,
    "high_confidence_count": 78,
    "top_positive": ["TQQQ", "UPRO", "SOXL", "FAS", "TECL"],
    "top_negative": ["SQQQ", "SPXU", "SOXS", "FAZ", "TECS"],
    "category_breakdown": {
      "index": {"positive": 12, "negative": 8, "neutral": 4},
      "sector": {"positive": 18, "negative": 15, "neutral": 12},
      "stock": {"positive": 15, "negative": 9, "neutral": 16}
    }
  }
}
```

#### **Premarket Sentiment Cache (`sentiment_cache.json`)**
```json
{
  "analysis_time": "2025-01-27T12:00:00Z",
  "lookback_hours": 30,
  "underlying_sentiments": {
    "Nasdaq-100": {
      "underlying": "Nasdaq-100",
      "sentiment_score": 0.75,
      "sentiment_strength": "positive",
      "confidence": 0.85,
      "confidence_level": "high",
      "news_count": 12,
      "trading_implications": "bullish",
      "breaking_news": true,
      "earnings_related": false,
      "high_impact_news": true,
      "analysis_time": "2025-01-27T12:00:00Z",
      "status": "success"
    }
  },
  "recommendations": {
    "prioritize_bull": ["TQQQ", "UPRO", "SOXL", "FAS", "TECL"],
    "prioritize_bear": ["SQQQ", "SPXU", "SOXS", "FAZ", "TECS"],
    "deprioritize_bull": ["TQQQ", "UPRO"],
    "deprioritize_bear": ["SQQQ", "SPXU"],
    "neutral": ["XLF", "XLE", "XLK", "XLV"]
  },
  "summary": {
    "total_underlying_assets": 25,
    "successful_analyses": 23,
    "prioritize_bull_count": 15,
    "prioritize_bear_count": 8,
    "deprioritize_bull_count": 2,
    "deprioritize_bear_count": 1,
    "neutral_count": 4
  }
}
```

### **Individual Trade Records (`symbol_trades`)**
```json
{
  "TQQQ": [
    {
      "symbol": "TQQQ",
      "trade_size": 1000.0,
      "profit_loss": 50.0,
      "prime_score": 5.0,
      "timestamp": "2025-01-27T15:30:00Z",
      "trade_id": "TQQQ_001",
      "strategy_mode": "standard",
      "confidence": 0.95
    }
  ]
}
```

### **Symbol Rankings (`symbol_ranks`)**
```json
{
  "TQQQ": {
    "symbol": "TQQQ",
    "avg_prime_score": 5.0,
    "total_trades": 1,
    "profitable_trades": 1,
    "win_rate": 100.0,
    "total_profit": 50.0,
    "avg_trade_size": 1000.0,
    "last_updated": "2025-01-27T15:30:00Z",
    "recent_prime_scores": [5.0]
  }
}
```

## 🚀 Getting Started

### **1. Initialize the System**
```bash
# Run the initialization script
python3 data/initialize_prime_scores.py
```

### **2. Test the System**
```bash
# Run the test script to verify functionality
python3 data/test_prime_scores.py
```

### **3. View Current Data**
```bash
# View the main data file
cat data/symbol_scores.json

# Pretty print with jq (if installed)
cat data/symbol_scores.json | jq .
```

## 📊 Prime Score Calculation

The Prime Score represents **profit per $100 invested**:

```
Prime Score = (Profit × 100) ÷ Trade Size
```

### **Examples:**
- $50 profit on $1,000 trade = 5.0 prime score
- $25 profit on $500 trade = 5.0 prime score  
- $100 profit on $2,000 trade = 5.0 prime score
- $50 loss on $1,000 trade = -5.0 prime score

## 🏆 Symbol Ranking

Symbols are ranked by their **average prime score** over the last 200 trades:

1. **TQQQ**: +6.25 avg prime score
2. **QQQ**: +6.00 avg prime score  
3. **SPY**: +1.25 avg prime score

## 🔄 Data Flow

### **Trading Data Flow**
1. **Trade Closes** → Prime Score Calculated
2. **Individual Trade** → Added to `symbol_trades[symbol]`
3. **200-Trade Rolling Average** → Calculated for `symbol_ranks[symbol]`
4. **Data Saved** → `symbol_scores.json` updated
5. **Backup Created** → `symbol_scores_backup.json` (every 100 trades)

### **Watchlist Data Flow**
1. **Core List** → `core_109.csv` (static reference)
2. **Premarket Analysis** → `premarket_sentiment_analysis.py` analyzes news sentiment (7:00 AM ET)
3. **Sentiment Cache** → `sentiment_cache.json` stores bull/bear recommendations
4. **Market Scanner** → Identifies opportunities (volume, volatility, momentum, **sentiment**)
5. **Dynamic Generation** → `build_dynamic_watchlist.py` sorts by opportunities + sentiment
6. **Dynamic Watchlist** → `dynamic_watchlist.csv` (updated every 15 minutes)
7. **Trading System** → Uses sentiment-prioritized dynamic watchlist for trading decisions

### **Sentiment Analysis Flow**
1. **News Sources** → Polygon, Finnhub, Finviz, Yahoo
2. **Keyword Matching** → Sentiment keywords for each symbol
3. **Premarket Analysis** → `premarket_sentiment_analysis.py` analyzes underlying assets (7:00 AM ET)
4. **Sentiment Cache** → `sentiment_cache.json` stores bull/bear recommendations
5. **Symbol Selection** → `build_dynamic_watchlist.py` uses sentiment for symbol prioritization
6. **Daily Tracking** → `daily_sentiment_tracker.py` stores sentiment data
7. **History Storage** → `sentiment_history.json` (30-day retention)

## 📈 System Stats

The system tracks:
- **Total Trades**: Number of trades recorded
- **Total Symbols**: Number of unique symbols traded (109 in core list)
- **Sentiment Coverage**: 100% sentiment context for all symbols
- **Dynamic Updates**: Watchlist updated every 15 minutes
- **Sentiment Updates**: Hourly sentiment analysis during market hours
- **Last Updated**: Timestamp of last update
- **Data Files**: Multiple specialized data files

## 🛠️ Maintenance

### **Backup System**
- **Trading Data**: Automatic backups every 100 trades
- **Sentiment Data**: 30-day retention policy
- **Watchlist Data**: Core list backed up, dynamic list regenerated
- **Manual Backup**: `cp symbol_scores.json symbol_scores_backup_YYYYMMDD.json`

### **Data Integrity**
- **JSON Validation**: All JSON files validated on load
- **Error Handling**: Corrupted files automatically fallback to backups
- **Sentiment Validation**: Sentiment data validated against symbol mappings
- **Watchlist Validation**: Dynamic watchlist validated against core list

### **Sentiment System Maintenance**
- **Keyword Updates**: Monitor and update sentiment keywords as needed
- **Source Weighting**: Adjust news source weights based on performance
- **Confidence Calibration**: Calibrate confidence boost factors
- **History Cleanup**: Automatic cleanup of sentiment data older than 30 days

## 🔍 Review Tools

Use the tools in `data/score/` directory to review rankings:

```bash
cd data/score

# Review rankings
python3 review_prime_ranks.py

# Show specific symbol
python3 review_prime_ranks.py --symbol TQQQ

# Export to CSV
python3 review_prime_ranks.py --export-csv

# Web dashboard
python3 prime_rank_dashboard.py
```

## 📋 Notes

### **System Requirements**
- **Core List**: Always maintain core_109.csv as static reference
- **Dynamic Updates**: Dynamic watchlist updates automatically every 15 minutes
- **Sentiment Coverage**: 100% sentiment context coverage for all 109 symbols
- **Real-Time Processing**: Sentiment analysis runs hourly during market hours

### **Performance Considerations**
- **Memory Usage**: Sentiment history retained for 30 days
- **API Limits**: News sentiment analysis respects API rate limits
- **Processing Time**: Dynamic watchlist generation takes ~2-3 seconds
- **Storage**: Sentiment data stored in JSON format for efficiency

### **Data Persistence**
- **Empty State**: Files start empty and are populated as trades are made
- **Real-Time Updates**: Rankings updated after each trade closure
- **Cloud Ready**: Can be synced to Google Cloud Storage
- **Survives Restarts**: Data persists across system restarts

---

**Version**: 3.0  
**Last Updated**: 2025-01-27  
**Author**: Easy ETrade Strategy Team  
**Features**: Complete sentiment analysis, dynamic watchlist generation, 109 symbol coverage
