# modules/enhanced_premarket_scanner.py

from __future__ import annotations
import os
import time
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

try:
    import yfinance as yf
except Exception:
    yf = None

log = logging.getLogger("enhanced_premarket_scanner")

@dataclass
class ScanResult:
    symbol: str
    price: float
    change_pct: float
    volume_ratio: float
    trend_score: float
    momentum_score: float
    quality_score: float
    confidence: float
    risk_reward: float
    market_regime: str
    should_trade: bool
    reasons: List[str]

class PrimePreMarketScanner:
    """
    Optimized pre-market scanner with:
    - Trend-first filtering (no downturns)
    - Cost-efficient data usage
    - Multi-timeframe analysis
    - Market regime awareness
    - Quality scoring system
    """
    
    def __init__(self):
        # Configuration
        self.max_symbols = int(os.getenv("MAX_SCAN_SYMBOLS", "50"))
        self.min_volume = int(os.getenv("MIN_DAILY_VOLUME", "100000"))
        self.min_price = float(os.getenv("MIN_PRICE", "5.0"))
        self.max_price = float(os.getenv("MAX_PRICE", "500.0"))
        self.cache_duration = int(os.getenv("SCAN_CACHE_DURATION", "14400"))  # 4 hours
        
        # Market regime thresholds
        self.bear_market_threshold = float(os.getenv("BEAR_MARKET_THRESHOLD", "-0.02"))  # SPY -2%
        self.high_volatility_threshold = float(os.getenv("HIGH_VOLATILITY_THRESHOLD", "25.0"))  # VIX 25
        
        # Trend detection thresholds
        self.trend_strength_min = float(os.getenv("TREND_STRENGTH_MIN", "0.6"))
        self.volume_confirmation_min = float(os.getenv("VOLUME_CONFIRMATION_MIN", "1.5"))
        self.momentum_min = float(os.getenv("MOMENTUM_MIN", "0.5"))
        
        # Caching
        self.cache = {}
        self.cache_timestamps = {}
        
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self.cache_timestamps:
            return False
        return (time.time() - self.cache_timestamps[key]) < self.cache_duration
        
    def _cache_data(self, key: str, data: Any) -> None:
        """Cache data with timestamp."""
        self.cache[key] = data
        self.cache_timestamps[key] = time.time()
        
    def _get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data if valid."""
        if self._is_cache_valid(key):
            return self.cache.get(key)
        return None
        
    async def _get_market_regime(self) -> Dict[str, Any]:
        """Determine current market regime using SPY and VIX."""
        cache_key = "market_regime"
        cached = self._get_cached_data(cache_key)
        if cached:
            return cached
            
        try:
            # Get SPY data for trend analysis
            spy = yf.Ticker("SPY")
            spy_data = spy.history(period="5d", interval="1d")
            
            if spy_data.empty:
                return {"regime": "unknown", "trend": 0.0, "volatility": 0.0}
                
            # Calculate trend (5-day change)
            current_price = float(spy_data["Close"].iloc[-1])
            prev_price = float(spy_data["Close"].iloc[-2])
            trend = (current_price - prev_price) / prev_price
            
            # Get VIX for volatility
            try:
                vix = yf.Ticker("^VIX")
                vix_data = vix.history(period="2d", interval="1d")
                volatility = float(vix_data["Close"].iloc[-1]) if not vix_data.empty else 20.0
            except:
                volatility = 20.0  # Default assumption
                
            # Determine regime
            if trend < self.bear_market_threshold:
                regime = "bear"
            elif volatility > self.high_volatility_threshold:
                regime = "volatile"
            elif trend > 0.01:  # 1% up
                regime = "bull"
            else:
                regime = "sideways"
                
            result = {
                "regime": regime,
                "trend": trend,
                "volatility": volatility,
                "spy_price": current_price
            }
            
            self._cache_data(cache_key, result)
            return result
            
        except Exception as e:
            log.error(f"Error getting market regime: {e}")
            return {"regime": "unknown", "trend": 0.0, "volatility": 0.0}
            
    async def _analyze_symbol_trend(self, symbol: str) -> Dict[str, Any]:
        """Analyze symbol trend using multiple timeframes."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get multi-timeframe data
            daily_data = ticker.history(period="30d", interval="1d")
            hourly_data = ticker.history(period="5d", interval="1h")
            
            if daily_data.empty or hourly_data.empty:
                return {"trend_score": 0.0, "momentum_score": 0.0, "volume_ratio": 0.0}
                
            # Daily trend analysis
            daily_close = daily_data["Close"]
            daily_volume = daily_data["Volume"]
            
            # Calculate moving averages
            ma_20 = daily_close.rolling(20).mean()
            ma_50 = daily_close.rolling(50).mean()
            
            current_price = float(daily_close.iloc[-1])
            current_volume = float(daily_volume.iloc[-1])
            avg_volume = float(daily_volume.rolling(20).mean().iloc[-1])
            
            # Trend strength (0-1)
            trend_score = 0.0
            if current_price > ma_20.iloc[-1]:
                trend_score += 0.4
            if ma_20.iloc[-1] > ma_50.iloc[-1]:
                trend_score += 0.3
            if current_price > ma_50.iloc[-1]:
                trend_score += 0.3
                
            # Volume confirmation
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Momentum analysis (RSI, MACD)
            momentum_score = 0.0
            
            # RSI calculation
            delta = daily_close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = float(rsi.iloc[-1])
            
            if 50 <= current_rsi <= 75:  # Bullish but not overbought
                momentum_score += 0.5
                
            # MACD analysis
            ema_12 = daily_close.ewm(span=12).mean()
            ema_26 = daily_close.ewm(span=26).mean()
            macd = ema_12 - ema_26
            macd_signal = macd.ewm(span=9).mean()
            
            if macd.iloc[-1] > macd_signal.iloc[-1]:
                momentum_score += 0.3
                
            # Short-term momentum (4-hour)
            if len(hourly_data) >= 20:
                hourly_close = hourly_data["Close"]
                short_ma = hourly_close.rolling(20).mean()
                if float(hourly_close.iloc[-1]) > float(short_ma.iloc[-1]):
                    momentum_score += 0.2
                    
            return {
                "trend_score": min(trend_score, 1.0),
                "momentum_score": min(momentum_score, 1.0),
                "volume_ratio": volume_ratio,
                "rsi": current_rsi,
                "current_price": current_price,
                "ma_20": float(ma_20.iloc[-1]),
                "ma_50": float(ma_50.iloc[-1])
            }
            
        except Exception as e:
            log.error(f"Error analyzing {symbol} trend: {e}")
            return {"trend_score": 0.0, "momentum_score": 0.0, "volume_ratio": 0.0}
            
    def _calculate_quality_score(self, trend_data: Dict[str, Any], 
                               market_regime: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Calculate overall quality score and reasons."""
        reasons = []
        score = 0.0
        
        # Trend strength (40% weight)
        trend_score = trend_data.get("trend_score", 0.0)
        if trend_score >= self.trend_strength_min:
            score += trend_score * 0.4
            reasons.append(f"Strong trend: {trend_score:.2f}")
        else:
            reasons.append(f"Weak trend: {trend_score:.2f}")
            
        # Volume confirmation (25% weight)
        volume_ratio = trend_data.get("volume_ratio", 0.0)
        if volume_ratio >= self.volume_confirmation_min:
            score += min(volume_ratio / 3.0, 1.0) * 0.25  # Cap at 3x volume
            reasons.append(f"Volume confirmation: {volume_ratio:.1f}x")
        else:
            reasons.append(f"Low volume: {volume_ratio:.1f}x")
            
        # Momentum (20% weight)
        momentum_score = trend_data.get("momentum_score", 0.0)
        if momentum_score >= self.momentum_min:
            score += momentum_score * 0.2
            reasons.append(f"Strong momentum: {momentum_score:.2f}")
        else:
            reasons.append(f"Weak momentum: {momentum_score:.2f}")
            
        # Market regime adjustment (15% weight)
        regime = market_regime.get("regime", "unknown")
        if regime == "bull":
            score += 0.15
            reasons.append("Bull market environment")
        elif regime == "sideways":
            score += 0.1
            reasons.append("Sideways market")
        elif regime == "volatile":
            score += 0.05
            reasons.append("Volatile market")
        else:
            reasons.append("Bear market - avoid")
            
        return min(score, 1.0), reasons
        
    async def _scan_symbol(self, symbol: str, market_regime: Dict[str, Any]) -> Optional[ScanResult]:
        """Scan individual symbol for trading opportunities."""
        try:
            # Get basic quote data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Basic filters
            price = info.get("regularMarketPrice", 0)
            if price < self.min_price or price > self.max_price:
                return None
                
            volume = info.get("regularMarketVolume", 0)
            if volume < self.min_volume:
                return None
                
            # Get trend analysis
            trend_data = await self._analyze_symbol_trend(symbol)
            
            # Calculate quality score
            quality_score, reasons = self._calculate_quality_score(trend_data, market_regime)
            
            # Determine if should trade
            should_trade = (
                quality_score >= 0.7 and  # High quality
                trend_data["trend_score"] >= self.trend_strength_min and
                trend_data["volume_ratio"] >= self.volume_confirmation_min and
                market_regime["regime"] in ["bull", "sideways"]  # No bear market trades
            )
            
            # Calculate confidence (0-100)
            confidence = quality_score * 100
            
            # Calculate risk/reward (simplified)
            current_price = trend_data.get("current_price", price)
            stop_loss = trend_data.get("ma_20", current_price * 0.95)
            risk_reward = (current_price - stop_loss) / current_price
            
            return ScanResult(
                symbol=symbol,
                price=price,
                change_pct=0.0,  # Would need to calculate
                volume_ratio=trend_data.get("volume_ratio", 0.0),
                trend_score=trend_data.get("trend_score", 0.0),
                momentum_score=trend_data.get("momentum_score", 0.0),
                quality_score=quality_score,
                confidence=confidence,
                risk_reward=risk_reward,
                market_regime=market_regime["regime"],
                should_trade=should_trade,
                reasons=reasons
            )
            
        except Exception as e:
            log.error(f"Error scanning {symbol}: {e}")
            return None
            
    async def scan_premarket(self, symbols: List[str]) -> List[ScanResult]:
        """Main pre-market scanning function."""
        log.info(f"Starting pre-market scan of {len(symbols)} symbols")
        
        # Get market regime
        market_regime = await self._get_market_regime()
        log.info(f"Market regime: {market_regime['regime']} (trend: {market_regime['trend']:.2%})")
        
        # Skip scanning in bear markets
        if market_regime["regime"] == "bear":
            log.warning("Bear market detected - skipping pre-market scan")
            return []
            
        # Scan symbols concurrently (batched)
        results = []
        batch_size = 10
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            
            # Create tasks for concurrent execution
            tasks = [self._scan_symbol(symbol, market_regime) for symbol in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter valid results
            for result in batch_results:
                if isinstance(result, ScanResult):
                    results.append(result)
                    
            # Rate limiting
            if i + batch_size < len(symbols):
                await asyncio.sleep(0.5)
                
        # Filter and sort results
        tradeable_results = [r for r in results if r and r.should_trade]
        tradeable_results.sort(key=lambda x: x.quality_score, reverse=True)
        
        log.info(f"Pre-market scan complete: {len(tradeable_results)} tradeable symbols found")
        return tradeable_results[:self.max_symbols]

# Module-level functions
async def scan_premarket_symbols(symbols: List[str]) -> List[ScanResult]:
    """Scan symbols for pre-market opportunities."""
    scanner = EnhancedPreMarketScanner()
    return await scanner.scan_premarket(symbols)

def get_universe_symbols() -> List[str]:
    """Get default universe of symbols to scan."""
    return [
        "SPY", "QQQ", "IWM", "DIA", "TSLA", "NVDA", "AAPL", "AMD", "META", "MSFT", "AMZN",
        "GOOGL", "NFLX", "CRM", "ADBE", "PYPL", "INTC", "CSCO", "ORCL", "IBM",
        "SOXL", "SOXS", "TQQQ", "SQQQ", "UVXY", "LABU", "LABD",
        "XLF", "XLE", "XLC", "XLB", "XLV", "XLK", "XLI", "XLY", "XLP",
        "ARKK", "ARKW", "MARA", "RIOT", "PLTR", "SNOW", "COIN", "SHOP", "CRWD", "SMCI"
    ]
