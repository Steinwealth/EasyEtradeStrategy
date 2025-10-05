#!/usr/bin/env python3
"""
Dynamic Watchlist Builder
========================

Sorts the entire core_109.csv list by trading opportunities:
- Volume movers (highest volume and momentum)
- Volatility opportunities (best volatility setups)
- News confluence (future enhancement)
- Performance-based prioritization

The core_109.csv remains the static reference, this creates a dynamic
sorted list of the best opportunities from that core list.

Author: Easy ETrade Strategy Team
Version: 2.0.0
"""

import os
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

try:
    import yfinance as yf
except Exception:
    yf = None

# Configuration
CORE_LIST_PATH = os.getenv("CORE_LIST_PATH", "data/watchlist/core_109.csv")
DYNAMIC_OUTPUT_PATH = os.getenv("DYNAMIC_OUTPUT_PATH", "data/watchlist/dynamic_watchlist.csv")
PERFORMANCE_LOG = os.getenv("SYMBOL_PERFORMANCE_LOG", "data/symbol_performance.json")
VOLUME_MOMENTUM_CACHE_PATH = os.getenv("VOLUME_MOMENTUM_CACHE_PATH", "data/volume_momentum_cache.json")

# Enhanced scoring weights for opportunity ranking with sentiment and volume momentum
VOLUME_WEIGHT = 0.30      # Volume and momentum (reduced from 0.35)
VOLATILITY_WEIGHT = 0.25  # Volatility opportunities (same)
MOMENTUM_WEIGHT = 0.20    # Price momentum and technicals (same)
SENTIMENT_WEIGHT = 0.15   # News sentiment alignment (reduced from 0.20)
VOLUME_MOMENTUM_WEIGHT = 0.10  # NEW: Top 10 volume momentum leaders

# Performance thresholds
MIN_TRADES_FOR_EVALUATION = 5
POOR_PERFORMER_CONSECUTIVE_LOSSES = 8
POOR_PERFORMER_WIN_RATE = 0.45
HIGH_PERFORMER_WIN_RATE = 0.60
HIGH_PERFORMER_AVG_RETURN = 0.02

# Yahoo Finance pacing
YF_SLEEP = float(os.getenv("YAHOO_MIN_INTERVAL", "0.2"))

# Sentiment analysis configuration
SENTIMENT_LOOKBACK_HOURS = 30  # Analyze news from last 30 hours
SENTIMENT_CONFIDENCE_THRESHOLD = 0.3  # Minimum confidence for sentiment (reduced for better coverage)
SENTIMENT_STRENGTH_THRESHOLD = 0.2  # Minimum sentiment strength to act on (reduced for better coverage)

def load_performance_data() -> Dict[str, Any]:
    """Load performance data for symbol prioritization."""
    try:
        if os.path.exists(PERFORMANCE_LOG):
            with open(PERFORMANCE_LOG, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {'symbols': {}}

def get_performance_boost(symbol: str, performance_data: Dict[str, Any]) -> float:
    """Get performance-based score boost for a symbol."""
    symbol_data = performance_data.get('symbols', {}).get(symbol, {})
    
    if not symbol_data:
        return 0.0
    
    total_trades = symbol_data.get('total_trades', 0)
    if total_trades < MIN_TRADES_FOR_EVALUATION:
        return 0.0
    
    consecutive_losses = symbol_data.get('consecutive_losses', 0)
    profitable_trades = symbol_data.get('profitable_trades', 0)
    total_pnl = symbol_data.get('total_pnl', 0)
    
    win_rate = profitable_trades / total_trades
    avg_return = total_pnl / total_trades
    
    # Poor performer penalty
    if (consecutive_losses >= POOR_PERFORMER_CONSECUTIVE_LOSSES or 
        (win_rate < POOR_PERFORMER_WIN_RATE and total_trades >= 10)):
        return -20.0
    
    # High performer boost
    if win_rate >= HIGH_PERFORMER_WIN_RATE and avg_return >= HIGH_PERFORMER_AVG_RETURN:
        return 20.0
    
    return 0.0

def load_core_symbols() -> List[str]:
    """Load all symbols from core_109.csv."""
    try:
        if os.path.exists(CORE_LIST_PATH):
            df = pd.read_csv(CORE_LIST_PATH)
            symbol_col = "symbol" if "symbol" in df.columns else df.columns[0]
            symbols = df[symbol_col].dropna().astype(str).str.upper().tolist()
            return symbols
    except Exception as e:
        print(f"Error loading core symbols: {e}")
    
    # Fallback to essential symbols
    return ["SPY", "QQQ", "IWM", "DIA", "TQQQ", "SQQQ", "UPRO", "SPXU"]

def load_sentiment_mapping() -> Dict[str, Any]:
    """Load sentiment mapping data."""
    try:
        with open("data/watchlist/complete_sentiment_mapping.json", 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading sentiment mapping: {e}")
        return {"bull_bear_pairs": {}}

def load_volume_momentum_leaders() -> List[Dict[str, Any]]:
    """Load top 10 volume momentum leaders from cache"""
    try:
        if os.path.exists(VOLUME_MOMENTUM_CACHE_PATH):
            with open(VOLUME_MOMENTUM_CACHE_PATH, 'r') as f:
                cache_data = json.load(f)
                momentum_leaders = cache_data.get('momentum_leaders', [])
                print(f"📊 Loaded {len(momentum_leaders)} volume momentum leaders")
                return momentum_leaders
        else:
            print("⚠️ Volume momentum cache not found, will scan for momentum leaders")
            return []
    except Exception as e:
        print(f"❌ Error loading volume momentum leaders: {e}")
        return []

def load_market_movers() -> List[Dict[str, Any]]:
    """Load explosive market movers from cache."""
    try:
        market_movers_path = os.getenv("MARKET_MOVERS_CACHE_PATH", "data/market_movers_cache.json")
        if os.path.exists(market_movers_path):
            with open(market_movers_path, 'r') as f:
                cache_data = json.load(f)
                market_movers = cache_data.get('market_movers', [])
                print(f"🚀 Loaded {len(market_movers)} explosive market movers")
                return market_movers
        else:
            print("⚠️ Market movers cache not found, run market_movers_scanner.py first")
            return []
    except Exception as e:
        print(f"❌ Error loading market movers: {e}")
        return []

def load_breakout_candidates() -> List[Dict[str, Any]]:
    """Load proactive breakout candidates from cache."""
    try:
        breakout_cache_path = os.getenv("BREAKOUT_CACHE_PATH", "data/breakout_candidates_cache.json")
        if os.path.exists(breakout_cache_path):
            with open(breakout_cache_path, 'r') as f:
                cache_data = json.load(f)
                breakout_candidates = cache_data.get('breakout_candidates', [])
                print(f"🎯 Loaded {len(breakout_candidates)} proactive breakout candidates")
                return breakout_candidates
        else:
            print("⚠️ Breakout candidates cache not found, run proactive_breakout_scanner.py first")
            return []
    except Exception as e:
        print(f"❌ Error loading breakout candidates: {e}")
        return []

def get_symbol_sentiment_context(symbol: str, sentiment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get sentiment context for a symbol."""
    return sentiment_data.get("bull_bear_pairs", {}).get(symbol)

def is_bull_etf(symbol: str, sentiment_data: Dict[str, Any]) -> bool:
    """Check if symbol is a bull ETF."""
    context = get_symbol_sentiment_context(symbol, sentiment_data)
    if context:
        bear_etf = context.get("bear_etf")
        return bear_etf is not None and bear_etf != "N/A"
    return False

def is_bear_etf(symbol: str, sentiment_data: Dict[str, Any]) -> bool:
    """Check if symbol is a bear ETF."""
    context = get_symbol_sentiment_context(symbol, sentiment_data)
    if context:
        bull_etf = context.get("bull_etf")
        return bull_etf is not None and bull_etf != "N/A"
    return False

def get_underlying_asset(symbol: str, sentiment_data: Dict[str, Any]) -> str:
    """Get underlying asset for a symbol."""
    context = get_symbol_sentiment_context(symbol, sentiment_data)
    if context:
        return context.get("underlying", "")
    return ""

# Global news manager instance to avoid repeated initialization
_news_manager = None

def get_news_manager():
    """Get or create news manager instance"""
    global _news_manager
    if _news_manager is None:
        try:
            from modules.prime_news_manager import get_prime_news_manager
            _news_manager = get_prime_news_manager()
        except Exception as e:
            print(f"Warning: Could not load news manager: {e}")
            _news_manager = None
    return _news_manager

def analyze_news_sentiment_for_underlying(underlying: str) -> Tuple[float, float, int]:
    """
    Analyze news sentiment for an underlying asset.
    
    Returns:
        (sentiment_score, confidence, news_count)
        sentiment_score: -1.0 to +1.0 (negative to positive)
        confidence: 0.0 to 1.0 (reliability)
        news_count: Number of news items analyzed
    """
    try:
        # First try to load from sentiment cache
        sentiment_cache_path = os.getenv("SENTIMENT_CACHE_PATH", "data/sentiment_cache.json")
        if os.path.exists(sentiment_cache_path):
            try:
                with open(sentiment_cache_path, 'r') as f:
                    cache_data = json.load(f)
                    underlying_sentiments = cache_data.get('underlying_sentiments', {})
                    if underlying in underlying_sentiments:
                        sentiment_info = underlying_sentiments[underlying]
                        if sentiment_info.get('status') == 'success':
                            return (
                                sentiment_info.get('sentiment_score', 0.0),
                                sentiment_info.get('confidence', 0.0),
                                sentiment_info.get('news_count', 0)
                            )
            except Exception as e:
                print(f"Error loading sentiment cache: {e}")
        
        # Fallback to real-time analysis
        import asyncio
        
        # Get shared news manager instance
        news_manager = get_news_manager()
        
        if not news_manager:
            # News manager not available, skip sentiment analysis
            return 0.0, 0.0, 0
        
        # Run async sentiment analysis
        async def _analyze():
            return await news_manager.analyze_news_sentiment(
                symbol=underlying,
                lookback_hours=SENTIMENT_LOOKBACK_HOURS
            )
        
        # Execute async function
        sentiment_result = asyncio.run(_analyze())
        
        if sentiment_result and sentiment_result.news_count > 0:
            return (
                sentiment_result.overall_sentiment,
                sentiment_result.sentiment_confidence,
                sentiment_result.news_count
            )
        else:
            return 0.0, 0.0, 0
            
    except Exception as e:
        print(f"Error analyzing news sentiment for {underlying}: {e}")
        return 0.0, 0.0, 0

def calculate_sentiment_score(symbol: str, sentiment_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate sentiment-based score for symbol selection.
    
    Logic:
    - Positive news + Bull ETF = High score (prioritize)
    - Negative news + Bear ETF = High score (prioritize)
    - Positive news + Bear ETF = Low score (deprioritize)
    - Negative news + Bull ETF = Low score (deprioritize)
    - No pair available = Treat as Bull ETF
    """
    try:
        # Get symbol context
        context = get_symbol_sentiment_context(symbol, sentiment_data)
        if not context:
            return 0.0, {}
        
        # Get underlying asset
        underlying = context.get("underlying", "")
        if not underlying:
            return 0.0, {}
        
        # Analyze news sentiment for underlying
        sentiment_score, confidence, news_count = analyze_news_sentiment_for_underlying(underlying)
        
        # Check if we have enough confidence (reduced thresholds for better coverage)
        if confidence < SENTIMENT_CONFIDENCE_THRESHOLD or news_count < 1:
            return 0.0, {
                "sentiment_score": sentiment_score,
                "confidence": confidence,
                "news_count": news_count,
                "reason": "insufficient_confidence_or_news"
            }
        
        # Determine if symbol is bull or bear
        is_bull = is_bull_etf(symbol, sentiment_data)
        is_bear = is_bear_etf(symbol, sentiment_data)
        
        # Calculate alignment score
        if is_bull:
            # Bull ETF: Positive sentiment = High score, Negative = Low score
            if sentiment_score > SENTIMENT_STRENGTH_THRESHOLD:
                alignment_score = 100.0  # Strong positive alignment
                reason = "positive_news_bull_etf"
            elif sentiment_score < -SENTIMENT_STRENGTH_THRESHOLD:
                alignment_score = 0.0  # Strong negative alignment (bad for bull)
                reason = "negative_news_bull_etf"
            else:
                alignment_score = 50.0  # Neutral
                reason = "neutral_news_bull_etf"
                
        elif is_bear:
            # Bear ETF: Negative sentiment = High score, Positive = Low score
            if sentiment_score < -SENTIMENT_STRENGTH_THRESHOLD:
                alignment_score = 100.0  # Strong negative alignment (good for bear)
                reason = "negative_news_bear_etf"
            elif sentiment_score > SENTIMENT_STRENGTH_THRESHOLD:
                alignment_score = 0.0  # Strong positive alignment (bad for bear)
                reason = "positive_news_bear_etf"
            else:
                alignment_score = 50.0  # Neutral
                reason = "neutral_news_bear_etf"
        else:
            # No pair available - treat as bull ETF
            if sentiment_score > SENTIMENT_STRENGTH_THRESHOLD:
                alignment_score = 80.0  # Good for bull (assumed)
                reason = "positive_news_no_pair"
            elif sentiment_score < -SENTIMENT_STRENGTH_THRESHOLD:
                alignment_score = 20.0  # Bad for bull (assumed)
                reason = "negative_news_no_pair"
            else:
                alignment_score = 50.0  # Neutral
                reason = "neutral_news_no_pair"
        
        return alignment_score, {
            "sentiment_score": sentiment_score,
            "confidence": confidence,
            "news_count": news_count,
            "is_bull": is_bull,
            "is_bear": is_bear,
            "underlying": underlying,
            "reason": reason
        }
        
    except Exception as e:
        print(f"Error calculating sentiment score for {symbol}: {e}")
        return 0.0, {}

def calculate_volume_score(symbol: str) -> Tuple[float, Dict[str, Any]]:
    """Calculate volume and momentum score (40% weight)."""
    if yf is None:
        return 0.0, {}
    
    try:
        df = yf.Ticker(symbol).history(period="5d", interval="1d", auto_adjust=False)
        if df is None or df.empty or len(df) < 2:
            return 0.0, {}
        
        close = df["Close"]
        volume = df["Volume"]
        
        # Recent volume metrics
        last_volume = int(volume.iloc[-1])
        avg_volume_5d = int(volume.mean())
        volume_ratio = last_volume / avg_volume_5d if avg_volume_5d > 0 else 1.0
        
        # Price momentum
        price_change_1d = float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100)
        price_change_2d = float((close.iloc[-1] - close.iloc[-3]) / close.iloc[-3] * 100)
        
        # Volume trend score (0-50)
        volume_trend_score = min(50.0, max(0.0, (volume_ratio - 1) * 25 + 25))
        
        # Momentum score (0-50) - FIXED: Only positive momentum gets high scores
        momentum_score = min(50.0, max(0.0, price_change_1d * 2 + price_change_2d))
        
        total_score = volume_trend_score + momentum_score
        
        return total_score, {
            "volume_ratio": volume_ratio,
            "price_change_1d": price_change_1d,
            "price_change_2d": price_change_2d,
            "last_volume": last_volume,
            "avg_volume_5d": avg_volume_5d
        }
        
    except Exception:
        return 0.0, {}

def calculate_volatility_score(symbol: str) -> Tuple[float, Dict[str, Any]]:
    """Calculate volatility opportunity score (30% weight)."""
    if yf is None:
        return 0.0, {}
    
    try:
        df = yf.Ticker(symbol).history(period="20d", interval="1d", auto_adjust=False)
        if df is None or df.empty or len(df) < 10:
            return 0.0, {}
        
        close = df["Close"]
        high, low = df["High"], df["Low"]
        
        # ATR calculation
        hl = (high - low)
        atr = hl.rolling(14, min_periods=1).mean()
        atr_pct = float((atr.iloc[-1] / close.iloc[-1]) * 100.0)
        
        # Historical volatility
        rets_log = np.log(close / close.shift(1)).dropna()
        historical_vol = float(np.std(rets_log, ddof=1) * np.sqrt(252) * 100.0)
        recent_vol = float(np.std(rets_log.tail(5), ddof=1) * np.sqrt(252) * 100.0)
        
        # Volatility ratio (recent vs historical)
        vol_ratio = recent_vol / historical_vol if historical_vol > 0 else 1.0
        
        # ATR score (0-40)
        atr_score = min(40.0, max(0.0, atr_pct * 2))
        
        # Volatility ratio score (0-30)
        vol_ratio_score = min(30.0, max(0.0, (vol_ratio - 1) * 30))
        
        # Historical volatility score (0-30)
        hv_score = min(30.0, max(0.0, historical_vol * 0.3))
        
        total_score = atr_score + vol_ratio_score + hv_score
        
        return total_score, {
            "atr_pct": atr_pct,
            "historical_vol": historical_vol,
            "recent_vol": recent_vol,
            "vol_ratio": vol_ratio
        }
        
    except Exception:
        return 0.0, {}

def calculate_momentum_score(symbol: str) -> Tuple[float, Dict[str, Any]]:
    """Calculate momentum and technical score (20% weight)."""
    if yf is None:
        return 0.0, {}
    
    try:
        df = yf.Ticker(symbol).history(period="30d", interval="1d", auto_adjust=False)
        if df is None or df.empty or len(df) < 20:
            return 0.0, {}
        
        close = df["Close"]
        
        # Price momentum
        price_change_1d = float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100)
        price_change_5d = float((close.iloc[-1] - close.iloc[-6]) / close.iloc[-6] * 100)
        price_change_10d = float((close.iloc[-1] - close.iloc[-11]) / close.iloc[-11] * 100)
        
        # RSI calculation
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])
        
        # Simple MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        current_macd = float(macd.iloc[-1])
        
        # Momentum score (0-50) - FIXED: Only positive momentum gets high scores
        # For Bull ETFs: Positive momentum = good, negative = bad
        # For Bear ETFs: Negative momentum = good, positive = bad
        # Since we're looking for buying opportunities, prioritize positive momentum
        momentum_1d = min(20.0, max(0.0, price_change_1d * 2))  # Removed abs() - only positive gets high score
        momentum_5d = min(20.0, max(0.0, price_change_5d * 1.5))  # Removed abs() - only positive gets high score
        momentum_10d = min(10.0, max(0.0, price_change_10d))  # Removed abs() - only positive gets high score
        
        # RSI momentum (0-30)
        rsi_score = 0.0
        if 30 <= current_rsi <= 70:  # Good momentum range
            rsi_score = 30.0
        elif 20 <= current_rsi <= 80:  # Acceptable range
            rsi_score = 15.0
        
        # MACD momentum (0-20)
        macd_score = min(20.0, max(0.0, abs(current_macd) * 1000))
        
        total_score = momentum_1d + momentum_5d + momentum_10d + rsi_score + macd_score
        
        return total_score, {
            "price_change_1d": price_change_1d,
            "price_change_5d": price_change_5d,
            "price_change_10d": price_change_10d,
            "rsi": current_rsi,
            "macd": current_macd
        }
        
    except Exception:
        return 0.0, {}

def calculate_opportunity_score(symbol: str, performance_data: Dict[str, Any], sentiment_data: Dict[str, Any], volume_momentum_leaders: List[Dict[str, Any]] = None) -> Tuple[float, Dict[str, Any]]:
    """Calculate overall opportunity score for a symbol with sentiment and volume momentum integration."""
    # Get component scores
    volume_score, volume_details = calculate_volume_score(symbol)
    volatility_score, volatility_details = calculate_volatility_score(symbol)
    momentum_score, momentum_details = calculate_momentum_score(symbol)
    sentiment_score, sentiment_details = calculate_sentiment_score(symbol, sentiment_data)
    performance_boost = get_performance_boost(symbol, performance_data)
    
    # Calculate volume momentum score (10% weight)
    volume_momentum_score = 0.0
    volume_momentum_details = {}
    if volume_momentum_leaders:
        for leader in volume_momentum_leaders:
            if leader['symbol'] == symbol:
                volume_momentum_score = leader.get('volume_score', 0.0)
                volume_momentum_details = {
                    'volume_momentum': leader.get('volume_momentum', 0.0),
                    'buyer_ratio': leader.get('buyer_ratio', 0.0),
                    'volume_surge_detected': leader.get('volume_surge_analysis', {}).get('volume_surge_detected', False),
                    'avg_volume': leader.get('avg_volume', 0.0)
                }
                break
    
    # Calculate weighted score with volume momentum
    opportunity_score = (
        volume_score * VOLUME_WEIGHT +
        volatility_score * VOLATILITY_WEIGHT +
        momentum_score * MOMENTUM_WEIGHT +
        sentiment_score * SENTIMENT_WEIGHT +
        volume_momentum_score * VOLUME_MOMENTUM_WEIGHT +
        performance_boost
    )
    
    # Combine all details
    all_details = {
        "volume_score": volume_score,
        "volatility_score": volatility_score,
        "momentum_score": momentum_score,
        "sentiment_score": sentiment_score,
        "volume_momentum_score": volume_momentum_score,
        "performance_boost": performance_boost,
        "volume_details": volume_details,
        "volatility_details": volatility_details,
        "momentum_details": momentum_details,
        "sentiment_details": sentiment_details,
        "volume_momentum_details": volume_momentum_details
    }
    
    return opportunity_score, all_details

def build_dynamic_watchlist():
    """Build the dynamic watchlist by sorting core_109.csv by opportunities with sentiment and volume momentum."""
    print("🚀 Building Enhanced Dynamic Watchlist with News Sentiment + Volume Momentum...")
    print("📊 Sorting core_109.csv by trading opportunities + sentiment alignment + volume momentum")
    
    # Load performance data
    performance_data = load_performance_data()
    print(f"📈 Performance data: {len(performance_data.get('symbols', {}))} symbols tracked")
    
    # Load sentiment mapping
    sentiment_data = load_sentiment_mapping()
    print(f"🧠 Sentiment mapping: {len(sentiment_data.get('bull_bear_pairs', {}))} symbols mapped")
    
    # Load volume momentum leaders
    volume_momentum_leaders = load_volume_momentum_leaders()
    print(f"📊 Volume momentum leaders: {len(volume_momentum_leaders)} high-volume tickers")
    
    # Load explosive market movers
    market_movers = load_market_movers()
    print(f"🚀 Market movers loaded: {len(market_movers)} explosive tickers")
    
    # Load all core symbols
    core_symbols = load_core_symbols()
    print(f"🎯 Core symbols loaded: {len(core_symbols)}")
    
    # Combine core symbols with market movers for comprehensive analysis
    all_symbols = list(set(core_symbols + [mover['symbol'] for mover in market_movers]))
    print(f"🎯 Total symbols to analyze: {len(all_symbols)} (core + market movers)")
    
    # Calculate opportunity scores for all symbols
    print("🧮 Calculating opportunity scores with sentiment integration...")
    scored_symbols = []
    
    for i, symbol in enumerate(all_symbols):
        score, details = calculate_opportunity_score(symbol, performance_data, sentiment_data, volume_momentum_leaders)
        
        # Add market mover boost if this symbol is an explosive mover
        market_mover_boost = 0.0
        for mover in market_movers:
            if mover['symbol'] == symbol:
                # Boost score based on explosive movement
                market_mover_boost = min(mover.get('explosive_score', 0) * 0.1, 20.0)  # Max 20 point boost
                details['market_mover_boost'] = market_mover_boost
                details['market_mover_details'] = {
                    'price_change_pct': mover.get('price_change_pct', 0),
                    'volume_ratio': mover.get('volume_ratio', 0),
                    'explosive_score': mover.get('explosive_score', 0),
                    'is_gainer': mover.get('is_gainer', False)
                }
                break
        
        # Apply market mover boost to total score
        enhanced_score = score + market_mover_boost
        scored_symbols.append((symbol, enhanced_score, details))
        
        if (i + 1) % 20 == 0:
            print(f"   Scored {i + 1}/{len(all_symbols)} symbols...")
        
        time.sleep(YF_SLEEP)
    
    # Sort by opportunity score (highest first)
    scored_symbols.sort(key=lambda x: x[1], reverse=True)
    
    # Create final dynamic watchlist
    dynamic_symbols = [symbol for symbol, score, details in scored_symbols]
    
    # Save results
    os.makedirs(os.path.dirname(DYNAMIC_OUTPUT_PATH), exist_ok=True)
    pd.DataFrame({"symbol": dynamic_symbols}).to_csv(DYNAMIC_OUTPUT_PATH, index=False)
    
    # Print results
    print(f"\n✅ Enhanced dynamic watchlist built successfully!")
    print(f"📊 Sorted {len(dynamic_symbols)} symbols by opportunity score + sentiment")
    
    print(f"\n🏆 Top 15 opportunities with sentiment + volume momentum + market movers:")
    for i, (symbol, score, details) in enumerate(scored_symbols[:15]):
        vol_score = details.get('volume_score', 0)
        vol_vol = details.get('volatility_score', 0)
        mom_score = details.get('momentum_score', 0)
        sent_score = details.get('sentiment_score', 0)
        vol_mom_score = details.get('volume_momentum_score', 0)
        perf_boost = details.get('performance_boost', 0)
        market_mover_boost = details.get('market_mover_boost', 0)
        
        # Check if this symbol is a volume momentum leader
        is_volume_leader = any(leader['symbol'] == symbol for leader in volume_momentum_leaders)
        volume_leader_indicator = "🔥" if is_volume_leader else "  "
        
        # Check if this symbol is a market mover
        market_mover_details = details.get('market_mover_details', {})
        is_market_mover = bool(market_mover_details)
        market_mover_indicator = "🚀" if is_market_mover else "  "
        
        # Get sentiment reason
        sent_details = details.get('sentiment_details', {})
        sent_reason = sent_details.get('reason', 'no_sentiment')
        
        # Format market mover info
        mover_info = ""
        if is_market_mover:
            price_change = market_mover_details.get('price_change_pct', 0)
            direction = "📈" if market_mover_details.get('is_gainer', False) else "📉"
            mover_info = f" {direction}{price_change:+.1f}%"
        
        print(f"{i+1:2d}. {symbol:6s} Score: {score:6.1f} (Vol: {vol_score:5.1f}, Vol: {vol_vol:5.1f}, Mom: {mom_score:5.1f}, Sent: {sent_score:5.1f}, VolMom: {vol_mom_score:5.1f}, Perf: {perf_boost:+4.1f}, Mov: {market_mover_boost:4.1f}) [{sent_reason}]{mover_info} {volume_leader_indicator}{market_mover_indicator}")
    
    # Print sentiment summary
    print(f"\n📰 Sentiment Analysis Summary:")
    sentiment_aligned = [s for s, sc, d in scored_symbols if d.get('sentiment_score', 0) > 70]
    sentiment_contradictory = [s for s, sc, d in scored_symbols if d.get('sentiment_score', 0) < 30]
    sentiment_neutral = [s for s, sc, d in scored_symbols if 30 <= d.get('sentiment_score', 0) <= 70]
    
    print(f"   🟢 Sentiment Aligned: {len(sentiment_aligned)} symbols")
    print(f"   🔴 Sentiment Contradictory: {len(sentiment_contradictory)} symbols")
    print(f"   ⚪ Sentiment Neutral: {len(sentiment_neutral)} symbols")
    
    # Print volume momentum summary
    print(f"\n📊 Volume Momentum Analysis Summary:")
    volume_leaders_in_top = [s for s, sc, d in scored_symbols[:20] if any(leader['symbol'] == s for leader in volume_momentum_leaders)]
    high_volume_momentum = [s for s, sc, d in scored_symbols if d.get('volume_momentum_score', 0) > 0.5]
    
    print(f"   🔥 Volume Leaders in Top 20: {len(volume_leaders_in_top)} symbols")
    print(f"   📈 High Volume Momentum: {len(high_volume_momentum)} symbols")
    print(f"   🎯 Total Volume Leaders: {len(volume_momentum_leaders)} symbols")
    
    # Print market movers summary
    print(f"\n🚀 Market Movers Analysis Summary:")
    market_movers_in_top = [s for s, sc, d in scored_symbols[:20] if d.get('market_mover_details')]
    explosive_gainers = [s for s, sc, d in scored_symbols if d.get('market_mover_details', {}).get('is_gainer', False)]
    
    print(f"   🚀 Market Movers in Top 20: {len(market_movers_in_top)} symbols")
    print(f"   📈 Explosive Gainers: {len(explosive_gainers)} symbols")
    print(f"   🎯 Total Market Movers: {len(market_movers)} symbols")
    
    # Show top market movers details
    if market_movers_in_top:
        print(f"\n🎯 Top Market Movers in Dynamic List:")
        for symbol in market_movers_in_top[:5]:
            for s, sc, d in scored_symbols:
                if s == symbol and d.get('market_mover_details'):
                    details = d['market_mover_details']
                    direction = "📈" if details.get('is_gainer', False) else "📉"
                    print(f"   {symbol:6s} {direction} {details.get('price_change_pct', 0):+6.2f}% "
                          f"(Vol: {details.get('volume_ratio', 0):.1f}x, Score: {details.get('explosive_score', 0):.1f})")
                    break
    
    print(f"\n💾 Saved to: {DYNAMIC_OUTPUT_PATH}")
    print(f"⏰ Generated at: {datetime.now().isoformat()}Z")

if __name__ == "__main__":
    build_dynamic_watchlist()