# 📋 Watchlist Data Directory

This directory contains all files related to building and maintaining the trading watchlist - the list of symbols that the system will trade. The system now features a comprehensive sentiment analysis integration and dynamic watchlist generation.

## 📁 Files

### **Core Watchlist Files**
- **`core_109.csv`** - **MAIN CORE LIST** - 109 symbols organized by leverage (3x → 2x → 1x)
- **`dynamic_watchlist.csv`** - Dynamic watchlist sorted by opportunities (volume, volatility, sentiment)
- **`stock_to_etf_mapping.csv`** - Stock to ETF mapping for leveraged trading
- **`trading_strategy_mapping.json`** - Complete trading strategy configuration

### **Sentiment Analysis Files**
- **`complete_sentiment_mapping.json`** - Complete sentiment context for all 109 symbols
- **`sentiment_pairs_mapping.json`** - Bull/bear pair sentiment relationships
- **`sentiment_integration_strategy.md`** - Sentiment integration documentation
- **`sentiment_cache.json`** - Premarket sentiment analysis cache (generated daily)

## 🎯 Purpose

The watchlist directory contains:
- **Core Symbol List**: 109 carefully curated symbols organized by leverage
- **Dynamic Watchlist**: Real-time sorted list based on market opportunities
- **Sentiment Analysis**: Complete sentiment context for all symbols
- **Leverage-Based Trading**: Stock-to-ETF mapping for maximum leverage gains
- **Bull/Bear Pairs**: Complete sentiment relationships for confidence boosting

## 🚀 Leverage-Based Trading Strategy

### **Core Concept**
When a BUY signal is generated for a stock (TSLA, NVDA, MSFT, GOOGL, etc.), the system trades the corresponding **highest leverage ETF** instead of the individual stock. This maximizes gains by capturing the stock's movement with 3x leverage.

### **Priority System**
1. **Ultra High Priority**: 3x Index ETFs (TQQQ/SQQQ, UPRO/SPXU, TMF/TMV, etc.) - 36 symbols
2. **High Priority**: 2x ETFs (ERX/ERY, NUGT/DUST, TSLL/TSLS, etc.) - 69 symbols  
3. **Medium Priority**: 1x Core ETFs (BTGD, BITX, UXRP, USD) - 4 symbols
4. **Bull/Bear Pairs**: Complete bull/bear pairs for all major indices and stocks

### **Trading Rules**
- **SPY Signal** → Trade **UPRO** (3x S&P 500) or **SPXL** (3x S&P 500 Alt)
- **QQQ Signal** → Trade **TQQQ** (3x Nasdaq-100)
- **TSLA Signal** → Trade **TSLL** (2x Tesla) or **TQQQ** (3x Nasdaq-100)
- **NVDA Signal** → Trade **NVDL** (2x NVIDIA) or **SOXL** (3x Semiconductors)
- **MSFT Signal** → Trade **MSFU** (2x Microsoft) or **TQQQ** (3x Nasdaq-100)
- **AAPL Signal** → Trade **AAPL** (2x Apple) or **TQQQ** (3x Nasdaq-100)
- **Tech Sector Signal** → Trade **TECL** (3x Technology) or **SOXL** (3x Semiconductors)
- **Financial Signal** → Trade **FAS** (3x Financial)
- **Energy Signal** → Trade **ERX** (2x Energy) or **GUSH** (3x Oil & Gas)
- **Gold Signal** → Trade **UGL** (2x Gold) or **NUGT** (2x Gold Miners)

## 🔄 Dynamic Watchlist Generation

### **Core Concept**
The system uses `core_109.csv` as a static reference and generates a dynamic watchlist (`dynamic_watchlist.csv`) that sorts all 109 symbols by market opportunities in real-time.

### **Dynamic Sorting Criteria**
1. **Volume & Momentum** (35%): High volume activity and unusual volume spikes
2. **Volatility Opportunities** (25%): High volatility and price movement potential
3. **Price Momentum** (20%): Technical momentum and price movement
4. **News Sentiment** (20%): **NEW** - Sentiment-based symbol prioritization
5. **Historical Performance** (10%): Past trading performance and win rates

### **Generation Process**
```
scanner.py → premarket_sentiment_analysis.py → build_dynamic_watchlist.py → dynamic_watchlist.csv → main.py
```

1. **Premarket Analysis** (7:00 AM ET): Analyzes news sentiment for all underlying assets
2. **Sentiment Cache**: Stores bull/bear recommendations based on news sentiment
3. **Scanner** identifies market opportunities
4. **Build Dynamic Watchlist** sorts core_109.csv by opportunities + sentiment
5. **Dynamic Watchlist** provides sentiment-prioritized opportunities to main.py
6. **Main.py** uses sentiment-aligned dynamic list for trading decisions

### **Real-Time Updates**
- **Market Hours**: Updated every 15 minutes during trading
- **Pre-Market**: Updated at 7:00 AM ET
- **After Hours**: Updated at 4:30 PM ET
- **Overnight**: Updated at 6:00 AM ET

## 🧠 News Sentiment Integration for Symbol Selection

### **Premarket News Analysis (7:00 AM ET)**
The system performs comprehensive news sentiment analysis before market open to inform symbol selection:

- **Lookback Period**: 30 hours of news data
- **Analysis Scope**: All underlying assets from core_109.csv
- **Confidence Threshold**: 60% minimum confidence for actionable sentiment
- **Strength Threshold**: 30% minimum sentiment strength to act on

### **Bull/Bear Prioritization Logic**
The system uses sophisticated logic to prioritize symbols based on news sentiment:

#### **Positive News Scenarios**
- **Bull ETFs**: High priority (TQQQ, UPRO, SOXL, FAS, TECL, etc.)
- **Bear ETFs**: Low priority (SQQQ, SPXU, SOXS, FAZ, TECS, etc.)
- **No Pair**: Treated as bull ETF, high priority

#### **Negative News Scenarios**
- **Bull ETFs**: Low priority (avoid sentiment-contradictory positions)
- **Bear ETFs**: High priority (SQQQ, SPXU, SOXS, FAZ, TECS, etc.)
- **No Pair**: Treated as bull ETF, low priority

#### **Neutral News Scenarios**
- **All ETFs**: Medium priority (technical factors dominate)

### **Complete Symbol Coverage**
- **109 symbols** with 100% sentiment context coverage
- **Real-time sentiment tracking** for all symbols
- **Bull/Bear pair relationships** for confidence boosting

### **Sentiment Categories**
- **Index ETFs**: Market sentiment (SPY, QQQ, IWM, DIA)
- **Sector ETFs**: Sector-specific sentiment (Tech, Energy, Financials)
- **Stock ETFs**: Company-specific sentiment (TSLA, NVDA, AAPL, etc.)
- **Commodity ETFs**: Commodity sentiment (Gold, Oil, Natural Gas)
- **Crypto ETFs**: Cryptocurrency sentiment (Bitcoin, Ethereum, XRP)

### **Confidence Boosting Logic**
```python
# Bull ETFs: Positive news = Positive boost
# Bear ETFs: Positive news = Negative boost (inverse)
boost = sentiment_score * leverage_factor
# 3x leverage: 40% boost factor
# 2x leverage: 30% boost factor  
# 1x leverage: 20% boost factor
```

### **Daily Sentiment Process**
1. **Morning Setup** (7:00 AM ET): Initialize sentiment tracking
2. **Hourly Updates** (8:00 AM - 4:00 PM ET): Analyze news sentiment
3. **Daily Summary** (4:00 PM ET): Generate sentiment reports
4. **Confidence Boosting**: Apply sentiment-based confidence adjustments

### **Sentiment System Architecture**
```
News Sources → Prime News Manager → Daily Sentiment Tracker → Trading System
     ↓              ↓                      ↓                    ↓
  Polygon      Sentiment Analysis    Symbol Context      Confidence Boost
  Finnhub      Keyword Matching      Bull/Bear Pairs     Position Sizing
  Finviz       Confidence Scoring    Category Mapping    Risk Management
  Yahoo        Source Weighting      History Tracking    Signal Filtering
```

### **Key Components**
- **`complete_sentiment_mapping.json`**: Complete context for all 109 symbols
- **`daily_sentiment_tracker.py`**: Real-time sentiment analysis and tracking
- **`prime_news_manager.py`**: News sentiment analysis engine
- **`premarket_sentiment_analysis.py`**: Premarket news analysis for symbol selection
- **`build_dynamic_watchlist.py`**: Dynamic watchlist generation with sentiment
- **`sentiment_cache.json`**: Daily premarket analysis results

### **Sentiment Cache Structure**
The `sentiment_cache.json` file contains daily premarket analysis results:

```json
{
  "analysis_time": "2025-01-27T12:00:00Z",
  "lookback_hours": 30,
  "underlying_sentiments": {
    "Nasdaq-100": {
      "sentiment_score": 0.75,
      "sentiment_strength": "positive",
      "confidence": 0.85,
      "news_count": 12,
      "trading_implications": "bullish"
    }
  },
  "recommendations": {
    "prioritize_bull": ["TQQQ", "UPRO", "SOXL"],
    "prioritize_bear": ["SQQQ", "SPXU", "SOXS"],
    "neutral": ["XLF", "XLE", "XLK"]
  }
}
```

## 📊 File Formats

### **CSV Format**
```csv
symbol,weight,bias,source
TQQQ,1.0,0.1,core
SPY,0.9,0.05,hybrid
QQQ,0.95,0.08,hybrid
```

### **Symbol Lists**
- **Symbol**: Trading symbol (e.g., TQQQ, SPY, QQQ)
- **Weight**: Trading weight/priority (0.0 to 1.0)
- **Bias**: Bias adjustment factor
- **Source**: Source of the symbol (core, hybrid, etc.)

## 🔄 Watchlist Management

### **Adding Symbols**
1. Edit the appropriate CSV file
2. Add symbol with weight and bias
3. Restart trading system to load new symbols

### **Removing Symbols**
1. Remove symbol from CSV file
2. Restart trading system to update watchlist

### **Updating Weights**
1. Modify weight values in CSV
2. Restart trading system to apply changes

## 📈 Integration

The watchlist system integrates with:
- **Trading Engine**: Loads dynamic watchlist for trading decisions
- **Prime Score System**: Tracks performance of watchlist symbols
- **Sentiment Analysis**: Provides confidence boosting based on news sentiment
- **Dynamic Watchlist**: Real-time sorting by market opportunities
- **Position Sizing**: Uses weights and sentiment for position calculations
- **Risk Management**: Applies sentiment-based risk adjustments

## 🛠️ Maintenance

### **Regular Updates**
- Review symbol performance monthly
- Update core_109.csv with new high-performing symbols
- Monitor sentiment analysis accuracy
- Adjust dynamic watchlist parameters

### **Sentiment System Maintenance**
- Monitor sentiment keyword effectiveness
- Update sentiment categories as needed
- Review bull/bear pair relationships
- Calibrate confidence boost factors

### **Backup Strategy**
- Keep backup copies of all watchlist files
- Version control for watchlist changes
- Document changes and rationale
- Backup sentiment history data

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

### **Configuration**
- **Update Frequency**: Configurable via environment variables
- **Confidence Threshold**: Default 0.6 for sentiment confidence
- **Boost Factors**: 3x (40%), 2x (30%), 1x (20%) leverage multipliers
- **Retention**: 30-day sentiment history retention

---

**Version**: 3.0  
**Last Updated**: 2025-01-27  
**Author**: Easy ETrade Strategy Team  
**Features**: Complete sentiment analysis, dynamic watchlist generation, 109 symbol coverage
