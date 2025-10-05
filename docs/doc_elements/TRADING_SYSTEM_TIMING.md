# Trading System Timing Configuration ⏰

## Complete Timing Overview

### 1. **Daily Watchlist Building** (7:00 AM ET)
- **Frequency**: Once per day
- **Trigger**: Cloud Scheduler at 7:00 AM ET (1 hour before market open)
- **Process**: `build_dynamic_watchlist.py` analyzes ~118 symbols from `core_109.csv`
- **Output**: `data/watchlist/dynamic_watchlist.csv` with daily opportunities
- **Mid-day Initialization**: ✅ **System automatically builds watchlist if missing/stale**

### 2. **Symbol Selector Updates** (Every 1 Hour)
- **Frequency**: Every 1 hour (3600 seconds)
- **Process**: `prime_symbol_selector.py` analyzes daily watchlist with fresh market data
- **Analysis**: RSI, volume, momentum, technical, volatility, trend scoring
- **Output**: Top 50 highest probability symbols
- **Adaptation**: Bear/Bull ETF detection with market regime alignment

### 3. **Multi-Strategy Manager** (Every 2 Minutes)
- **Frequency**: Every 2 minutes (120 seconds)
- **Process**: `prime_multi_strategy_manager.py` screens selected symbols
- **Strategies**: All 8 strategies (Standard, Advanced, Quantum + 5 specialized)
- **Validation**: Cross-validation with agreement levels
- **Output**: Only symbols passing multi-strategy validation proceed

### 4. **Production Signal Generator** (Every 2 Minutes)
- **Frequency**: Every 2 minutes (120 seconds)
- **Process**: `production_signal_generator.py` provides final confirmation
- **Analysis**: Enhanced profitability analysis, quality validation
- **Output**: High-confidence BUY signals
- **Thresholds**: Strategy-specific confidence requirements

### 5. **Position Monitoring** (Every 60 Seconds)
- **Frequency**: Every 60 seconds (1 minute)
- **Process**: `prime_stealth_trailing_tp.py` monitors open positions
- **Analysis**: Stop-loss, take-profit, trailing stop management
- **Output**: SELL/EXIT signals when conditions are met

## Timing Flow Diagram

```
7:00 AM ET: Daily Watchlist Built (Once)
    ↓
Every 1 Hour: Symbol Selector Updates (Fresh Analysis)
    ↓
Every 2 Minutes: Multi-Strategy Manager (Screening)
    ↓
Every 2 Minutes: Production Signal Generator (Final Confirmation)
    ↓
Every 60 Seconds: Position Monitoring (Exit Management)
```

## Key Features

### ✅ **Mid-Day Initialization Support**
- System checks if watchlist was built today
- If missing/stale, automatically builds watchlist on startup
- No manual intervention required

### ✅ **Fresh Analysis Every Hour**
- Symbol selector reloads daily watchlist
- Performs fresh market analysis
- Updates top 50 symbols based on current conditions
- Adapts to changing market regimes

### ✅ **High-Frequency Signal Generation**
- Multi-strategy manager runs every 2 minutes
- Production signal generator runs every 2 minutes
- Ensures no opportunities are missed
- Real-time market adaptation

### ✅ **Continuous Position Management**
- Position monitoring every 60 seconds
- Stealth trailing stop management
- Real-time exit signal generation
- Risk management optimization

## API Usage Optimization

### **Daily API Calls** (ETrade 10,000 limit):
- **Watchlist Building**: ~1,200 calls (once daily)
- **Symbol Selector**: ~1,200 calls (every hour × 6.5 hours)
- **Multi-Strategy + Signal Gen**: ~975 calls (every 2 minutes × 6.5 hours)
- **Position Monitoring**: ~390 calls (every 60 seconds × 6.5 hours)
- **Total**: ~3,765 calls/day (37.7% of limit)

### **Efficient Batching**:
- Symbol selector analyzes in batches
- Multi-strategy manager processes selected symbols only
- Production signal generator focuses on validated symbols
- Position monitoring only checks open positions

## System Benefits

### 🎯 **Optimal Timing**
- **Daily**: Fresh watchlist based on overnight news/data
- **Hourly**: Updated symbol selection with current market conditions
- **2-Minute**: High-frequency signal generation for opportunities
- **60-Second**: Real-time position management

### 📊 **Quality Focus**
- Only analyzes highest probability symbols
- Multi-strategy validation reduces false signals
- Production signal generator ensures profitability
- Continuous adaptation to market conditions

### ⚡ **Performance**
- Parallel processing for all operations
- Efficient API usage with batching
- Real-time market adaptation
- Comprehensive logging and monitoring

This timing configuration ensures the system captures the best trading opportunities while maintaining optimal performance and API usage efficiency.
