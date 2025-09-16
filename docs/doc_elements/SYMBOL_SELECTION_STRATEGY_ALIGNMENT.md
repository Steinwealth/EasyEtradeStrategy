# Symbol Selection Strategy Alignment Analysis

## Current Documentation Review

### From docs/Strategy.md:
- **Signal Generation**: Momentum-based entries (RSI, MACD, volume), breakout detection, mean reversion, trend following
- **Risk Management**: ATR-based dynamic stops, position sizing based on available cash and equity
- **Strategy Modes**: Standard (1% weekly, 2% risk), Advanced (10% weekly, 5% risk), Quantum (50% weekly, 10% risk)

### From docs/Data.md:
- **Data Sources**: E*TRADE API (primary), Polygon.io (secondary), Alpha Vantage (historical), Yahoo Finance (fallback)
- **Pre-Market Scanning**: 40 symbols, 6 months daily data, technical indicators (ATR, Historical Volatility, Beta)
- **Cost Strategy**: E*TRADE FREE, Alpha Vantage $50/month, total $149/month

### From docs/SCANNER_ETRADE_OPTIMIZATION.md:
- **Target**: 50 symbols total
- **Distribution**: 20 core + 20 volume movers + 10 volatility opportunities
- **Scoring**: 40% liquidity + 30% volatility + 20% momentum + 10% spread quality
- **Performance**: <5 seconds scan time, <10 ETRADE calls per scan

## Current Implementation Analysis

### build_watchlist.py (Current):
- **Universe**: 38 hardcoded symbols
- **Scoring**: ATR%, Historical Volatility, Beta (weights: 1.0, 1.0, 0.5)
- **Process**: Core symbols + 2-day movers + volatility ranking
- **Output**: Top 40 symbols ranked by volatility

### etrade_optimized_scanner.py (Existing):
- **Universe**: 60+ symbols across ETFs, Tech, Growth, Sectors
- **Scoring**: 40% liquidity + 30% volatility + 20% momentum + 10% spread quality
- **Process**: Core + volume movers + volatility opportunities
- **Output**: Top 50 symbols with ETRADE real-time data

## Alignment Issues Identified

### 1. **Inconsistent Universe Size**
- **Documentation**: 50 symbols target
- **build_watchlist.py**: 40 symbols (MAX_WATCHLIST_SIZE=40)
- **etrade_optimized_scanner.py**: 50 symbols
- **Solution**: Standardize on 50 symbols

### 2. **Different Scoring Systems**
- **Documentation**: 40% liquidity + 30% volatility + 20% momentum + 10% spread
- **build_watchlist.py**: ATR% + Historical Vol + Beta (no liquidity, momentum, or spread)
- **Solution**: Align scoring with documented approach

### 3. **Missing ETRADE Integration**
- **Documentation**: ETRADE real-time data for all operations
- **build_watchlist.py**: Uses Yahoo Finance only
- **Solution**: Integrate ETRADE data manager

### 4. **Inconsistent Symbol Categories**
- **Documentation**: Core (20) + Volume Movers (20) + Volatility (10)
- **build_watchlist.py**: Core + Movers (no clear distribution)
- **Solution**: Implement documented distribution

## Recommended Cohesive Strategy

### 1. **Unified Symbol Selection Rules**

#### **Phase 1: Core Symbols (20 symbols - Always Included)**
```python
CORE_SYMBOLS = [
    # Major ETFs
    "SPY", "QQQ", "IWM", "DIA", "VTI",
    
    # Tech Giants
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
    
    # Leveraged ETFs
    "TQQQ", "SQQQ", "SOXL", "SOXS",
    
    # Sector ETFs
    "XLF", "XLE", "XLK", "XLV", "XLI", "XLY"
]
```

#### **Phase 2: Volume Movers (20 symbols - Highest Volume)**
- **Criteria**: Top 20 symbols by daily volume from extended universe
- **Data Source**: ETRADE real-time volume data
- **Filtering**: Price $5-$1000, volume >100K, spread <0.5%

#### **Phase 3: Volatility Opportunities (10 symbols - Best Volatility)**
- **Criteria**: Top 10 symbols by volatility score from remaining universe
- **Calculation**: ATR% + Historical Volatility + Recent momentum
- **Filtering**: Must pass liquidity and spread quality tests

### 2. **Unified Scoring System**

```python
def calculate_symbol_score(symbol_data):
    """
    Unified scoring system aligned with documentation:
    40% liquidity + 30% volatility + 20% momentum + 10% spread quality
    """
    
    # Liquidity Score (40% weight)
    liquidity_score = calculate_liquidity_score(
        volume=symbol_data.volume,
        avg_volume=symbol_data.avg_volume_20d,
        dollar_volume=symbol_data.price * symbol_data.volume
    )
    
    # Volatility Score (30% weight)
    volatility_score = calculate_volatility_score(
        atr_pct=symbol_data.atr_pct,
        historical_vol=symbol_data.historical_vol,
        recent_vol=symbol_data.recent_volatility
    )
    
    # Momentum Score (20% weight)
    momentum_score = calculate_momentum_score(
        price_momentum_1d=symbol_data.price_change_1d,
        price_momentum_5d=symbol_data.price_change_5d,
        rsi=symbol_data.rsi,
        macd=symbol_data.macd
    )
    
    # Spread Quality Score (10% weight)
    spread_score = calculate_spread_score(
        bid_ask_spread=symbol_data.bid_ask_spread,
        price=symbol_data.price
    )
    
    # Combined score
    overall_score = (
        liquidity_score * 0.4 +
        volatility_score * 0.3 +
        momentum_score * 0.2 +
        spread_score * 0.1
    )
    
    return overall_score
```

### 3. **ETRADE Data Integration**

```python
def scan_with_etrade_data():
    """
    Use ETRADE data manager for all scanning operations
    """
    
    # Get ETRADE real-time quotes for all symbols
    quotes = etrade_data_manager.get_multiple_quotes(universe_symbols)
    
    # Get ETRADE historical data for volatility calculation
    historical_data = etrade_data_manager.get_historical_data(
        symbols, period="6mo", interval="1d"
    )
    
    # Get ETRADE spread data for quality assessment
    spread_data = etrade_data_manager.get_spread_data(symbols)
    
    return process_symbol_data(quotes, historical_data, spread_data)
```

### 4. **Performance Integration**

```python
def apply_performance_filters(symbols, scores):
    """
    Apply performance-based filtering as documented
    """
    
    # Load performance data
    performance_data = load_symbol_performance()
    
    # Filter out poor performers
    filtered_symbols = []
    for symbol, score in zip(symbols, scores):
        
        # Check performance history
        perf = performance_data.get(symbol)
        if perf:
            # Exclude if poor performer
            if (perf.consecutive_losses >= 8 or 
                (perf.win_rate < 0.45 and perf.total_trades >= 10)):
                continue
            
            # Boost high performers
            if perf.win_rate >= 0.60 and perf.avg_return >= 0.02:
                score += 20  # Performance boost
        
        filtered_symbols.append((symbol, score))
    
    return filtered_symbols
```

### 5. **Strategy Mode Alignment**

```python
def get_strategy_requirements(mode):
    """
    Get symbol requirements based on strategy mode
    """
    
    if mode == "standard":
        return {
            "min_confidence": 0.7,
            "max_risk_per_trade": 0.05,
            "target_weekly_return": 0.01,
            "min_quality_score": 60
        }
    elif mode == "advanced":
        return {
            "min_confidence": 0.8,
            "max_risk_per_trade": 0.15,
            "target_weekly_return": 0.10,
            "min_quality_score": 70
        }
    elif mode == "quantum":
        return {
            "min_confidence": 0.9,
            "max_risk_per_trade": 0.25,
            "target_weekly_return": 0.50,
            "min_quality_score": 80
        }
```

## Implementation Plan

### Phase 1: Align build_watchlist.py with Documentation
1. **Update Universe**: Expand to match etrade_optimized_scanner.py
2. **Implement Unified Scoring**: 40% liquidity + 30% volatility + 20% momentum + 10% spread
3. **Add ETRADE Integration**: Use ETRADE data manager for real-time data
4. **Implement Distribution**: 20 core + 20 volume movers + 10 volatility

### Phase 2: Integrate Performance Tracking
1. **Add Performance Filters**: Remove poor performers, boost high performers
2. **Quality Scoring**: Implement strategy-specific quality requirements
3. **Dynamic Updates**: Update core list based on performance

### Phase 3: Strategy Mode Integration
1. **Mode-Specific Requirements**: Different criteria for Standard/Advanced/Quantum
2. **Confidence Thresholds**: Align with documented confidence levels
3. **Risk Alignment**: Ensure symbol selection supports strategy risk parameters

## Expected Results

### **Cohesive Symbol Selection**
- **50 symbols** total (20 core + 20 volume + 10 volatility)
- **ETRADE real-time data** for all operations
- **Unified scoring** system across all components
- **Performance-based filtering** for quality improvement

### **Strategy Alignment**
- **Standard Mode**: Conservative symbols, lower volatility
- **Advanced Mode**: Balanced symbols, moderate volatility
- **Quantum Mode**: High-quality symbols, maximum volatility

### **Performance Benefits**
- **Higher win rates** from performance-based filtering
- **Better risk management** from strategy-aligned selection
- **Real-time accuracy** from ETRADE data integration
- **Cost efficiency** from unified data strategy

This alignment ensures the symbol selection system works cohesively with the documented strategy, using the same data sources, scoring methods, and performance criteria across all components.
