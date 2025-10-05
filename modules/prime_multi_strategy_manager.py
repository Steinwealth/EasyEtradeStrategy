# modules/prime_multi_strategy_manager.py

"""
Prime Multi-Strategy Manager
Implements cross-validation system with multiple trading strategies
Provides position size bonuses based on strategy agreement
"""

from __future__ import annotations
import asyncio
import logging
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

# Import unified models
from .prime_models import StrategyMode, PrimeSignal, SignalType, SignalSide, SignalQuality

log = logging.getLogger("prime_multi_strategy_manager")

# ============================================================================
# ENUMS
# ============================================================================

class StrategyType(Enum):
    """Strategy type enumeration"""
    STANDARD = "standard"
    ADVANCED = "advanced"
    QUANTUM = "quantum"
    RSI_POSITIVITY = "rsi_positivity"
    BUYERS_VOLUME_SURGING = "buyers_volume_surging"
    ORB_BREAKOUT = "orb_breakout"
    NEWS_SENTIMENT = "news_sentiment"
    TECHNICAL_CONFIRMATION = "technical_confirmation"

class AgreementLevel(Enum):
    """Strategy agreement level"""
    NONE = "none"
    LOW = "low"          # 1 strategy agrees
    MEDIUM = "medium"    # 2 strategies agree
    HIGH = "high"        # 3 strategies agree
    MAXIMUM = "maximum"  # 4+ strategies agree

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class StrategyResult:
    """Individual strategy analysis result"""
    strategy_type: StrategyType
    symbol: str
    should_trade: bool
    confidence: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size_pct: float = 0.0
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MultiStrategyResult:
    """Multi-strategy analysis result"""
    symbol: str
    strategies: Dict[StrategyType, StrategyResult]
    agreements: List[StrategyType]
    agreement_count: int
    agreement_level: AgreementLevel
    size_bonus: float
    confidence_bonus: float
    should_trade: bool
    final_confidence: float
    final_position_size_pct: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# BASE STRATEGY CLASS
# ============================================================================

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, strategy_type: StrategyType):
        self.strategy_type = strategy_type
        self.enabled = True
        self.weight = 1.0
        
    @abstractmethod
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> StrategyResult:
        """Analyze symbol and return strategy result"""
        pass
    
    def _calculate_confidence(self, score: float, max_score: float = 100.0) -> float:
        """Calculate confidence from score"""
        return min(1.0, max(0.0, score / max_score))

# ============================================================================
# INDIVIDUAL STRATEGIES
# ============================================================================

class StandardStrategy(BaseStrategy):
    """Standard trading strategy - 12% weekly target, 6+ confirmations required"""
    
    def __init__(self):
        super().__init__(StrategyType.STANDARD)
        self.target_return = 0.12  # 12% weekly
        self.risk_level = 0.02  # 2% base risk per trade
        self.position_size = 0.10  # 10% of equity per trade
        self.confidence_threshold = 0.90  # 90% confidence required
        self.required_confirmations = 6  # 6+ confirmations required
        
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> StrategyResult:
        try:
            # Get market data
            prices = market_data.get('prices', [])
            volumes = market_data.get('volumes', [])
            
            if len(prices) < 20:
                return StrategyResult(
                    strategy_type=self.strategy_type,
                    symbol=symbol,
                    should_trade=False,
                    confidence=0.0,
                    entry_price=0.0,
                    reasoning="Insufficient price data"
                )
            
            # Calculate technical confirmations (6+ required)
            confirmations = 0
            confirmation_details = []
            
            # 1. SMA Trend Alignment (SMA 20 > 50 > 200)
            sma_20 = np.mean(prices[-20:])
            sma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else sma_20
            sma_200 = np.mean(prices[-200:]) if len(prices) >= 200 else sma_50
            
            if sma_20 > sma_50 > sma_200:
                confirmations += 1
                confirmation_details.append("SMA trend alignment")
            
            # 2. Price Position (Close > SMA 20)
            current_price = prices[-1]
            if current_price > sma_20:
                confirmations += 1
                confirmation_details.append("Price above SMA 20")
            
            # 3. RSI Positivity (RSI > 55)
            rsi = self._calculate_rsi(prices)
            if rsi > 55:
                confirmations += 1
                confirmation_details.append(f"RSI positivity: {rsi:.1f}")
            
            # 4. MACD Signal (MACD > Signal)
            macd_signal = self._check_macd_signal(prices)
            if macd_signal:
                confirmations += 1
                confirmation_details.append("MACD bullish signal")
            
            # 5. Volume Confirmation
            if volumes:
                current_volume = volumes[-1]
                avg_volume = np.mean(volumes[-20:])
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                if volume_ratio > 1.2:  # 20% above average
                    confirmations += 1
                    confirmation_details.append(f"Volume surge: {volume_ratio:.1f}x")
            
            # 6. Bollinger Position
            bb_position = self._check_bollinger_position(prices)
            if bb_position:
                confirmations += 1
                confirmation_details.append("Bollinger position favorable")
            
            # Determine if should trade (6+ confirmations required)
            should_trade = confirmations >= self.required_confirmations
            
            # Calculate confidence
            confidence = min(1.0, confirmations / 8.0)  # Scale to max 8 confirmations
            
            # Calculate position size
            position_size_pct = min(self.position_size * 100, confidence * 15.0)
            
            # Calculate stops
            entry_price = current_price
            stop_loss = entry_price * (1 - self.risk_level)
            take_profit = entry_price * (1 + self.target_return / 10)  # 1.2% target
            
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=should_trade,
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size_pct=position_size_pct,
                reasoning=f"Standard Strategy: {confirmations}/6 confirmations - {', '.join(confirmation_details)}",
                metadata={
                    'confirmations': confirmations,
                    'required_confirmations': self.required_confirmations,
                    'rsi': rsi,
                    'sma_trend': sma_20 > sma_50 > sma_200,
                    'volume_ratio': volume_ratio if volumes else 1.0
                }
            )
            
        except Exception as e:
            log.error(f"Error in standard strategy for {symbol}: {e}")
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning=f"Error: {str(e)}"
            )

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _check_macd_signal(self, prices: List[float]) -> bool:
        """Check MACD bullish signal"""
        if len(prices) < 26:
            return False
        
        # Calculate EMAs
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        macd_line = ema_12 - ema_26
        macd_signal = self._calculate_ema([macd_line] * len(prices), 9)  # Simplified
        
        return macd_line > macd_signal
    
    def _check_bollinger_position(self, prices: List[float]) -> bool:
        """Check Bollinger Bands position"""
        if len(prices) < 20:
            return False
        
        # Calculate Bollinger Bands
        sma = np.mean(prices[-20:])
        std = np.std(prices[-20:])
        upper_band = sma + (2 * std)
        lower_band = sma - (2 * std)
        
        current_price = prices[-1]
        # Favorable if price is above middle band but not overbought
        return lower_band < current_price < upper_band * 0.98
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return np.mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema

class RSIPositivityStrategy(BaseStrategy):
    """RSI Positivity Strategy - RSI > 55 for buy signals"""
    
    def __init__(self):
        super().__init__(StrategyType.RSI_POSITIVITY)
        self.min_rsi = 55.0
        self.strong_rsi = 70.0
        
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> StrategyResult:
        try:
            prices = market_data.get('prices', [])
            
            if len(prices) < 15:
                return StrategyResult(
                    strategy_type=self.strategy_type,
                    symbol=symbol,
                    should_trade=False,
                    confidence=0.0,
                    entry_price=0.0,
                    reasoning="Insufficient price data for RSI"
                )
            
            # Calculate RSI
            rsi = self._calculate_rsi(prices)
            
            # Determine if should trade
            should_trade = rsi > self.min_rsi
            
            # Calculate confidence based on RSI level
            if rsi > self.strong_rsi:
                confidence = 0.95  # Strong buy
            elif rsi > self.min_rsi:
                confidence = 0.80  # Buy
            else:
                confidence = 0.0
            
            # Calculate position size
            position_size_pct = min(3.0, confidence * 3.0)
            
            # Calculate stops
            entry_price = prices[-1]
            stop_loss = entry_price * (1 - 0.025)  # 2.5% stop loss
            take_profit = entry_price * (1 + 0.05)  # 5% take profit
            
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=should_trade,
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size_pct=position_size_pct,
                reasoning=f"RSI Positivity: {rsi:.1f} ({'Strong Buy' if rsi > self.strong_rsi else 'Buy' if rsi > self.min_rsi else 'No Signal'})",
                metadata={'rsi': rsi, 'min_rsi': self.min_rsi, 'strong_rsi': self.strong_rsi}
            )
            
        except Exception as e:
            log.error(f"Error in RSI positivity strategy for {symbol}: {e}")
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning=f"Error: {str(e)}"
            )
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

class BuyersVolumeSurgingStrategy(BaseStrategy):
    """Enhanced Buyers Volume Surging Strategy - Detects majority buyers and volume surges"""
    
    def __init__(self):
        super().__init__(StrategyType.BUYERS_VOLUME_SURGING)
        self.min_rsi = 60.0  # Increased threshold for stronger momentum
        self.min_volume_ratio = 1.5  # 50% above average volume (increased)
        self.min_volume_spike = 2.0  # 2x previous 5-period average
        self.min_price_volume_correlation = 0.7  # Strong buying pressure
        
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> StrategyResult:
        try:
            prices = market_data.get('prices', [])
            volumes = market_data.get('volumes', [])
            
            if len(prices) < 20 or not volumes or len(volumes) < 20:
                return StrategyResult(
                    strategy_type=self.strategy_type,
                    symbol=symbol,
                    should_trade=False,
                    confidence=0.0,
                    entry_price=0.0,
                    reasoning="Insufficient data for enhanced volume analysis"
                )
            
            # Calculate enhanced metrics
            rsi = self._calculate_rsi(prices)
            volume_ratio = self._calculate_volume_ratio(volumes)
            volume_spike = self._calculate_volume_spike(volumes)
            price_volume_correlation = self._calculate_price_volume_correlation(prices, volumes)
            buying_pressure = self._calculate_buying_pressure(prices, volumes)
            macd_signal = self._check_macd_signal(prices)
            
            # Enhanced detection logic
            volume_surge = volume_ratio > self.min_volume_ratio
            volume_spike_detected = volume_spike > 2.0  # 2x previous 5-period average
            strong_momentum = rsi > 60  # Increased threshold
            buying_dominance = price_volume_correlation > 0.7  # Strong buying pressure
            high_buying_pressure = buying_pressure > 0.7
            momentum_confirmation = macd_signal
            
            # Determine if should trade (multiple confirmations required)
            should_trade = (
                volume_surge and 
                (volume_spike_detected or strong_momentum) and
                (buying_dominance or high_buying_pressure)
            )
            
            # Enhanced confidence scoring (0-145 points)
            confidence_score = 50  # Base score
            
            # Volume surge bonuses
            if volume_ratio > 2.0:
                confidence_score += 20
            elif volume_ratio > 1.5:
                confidence_score += 10
            
            # Price-volume correlation bonus
            if price_volume_correlation > 0.8:
                confidence_score += 15
            elif price_volume_correlation > 0.7:
                confidence_score += 10
            
            # Volume spike bonus
            if volume_spike > 3.0:
                confidence_score += 15
            elif volume_spike > 2.0:
                confidence_score += 10
            
            # RSI momentum bonus
            if rsi > 70:
                confidence_score += 10
            elif rsi > 60:
                confidence_score += 5
            
            # MACD confirmation bonus
            if momentum_confirmation:
                confidence_score += 10
            
            # Buying pressure bonus
            if buying_pressure > 0.8:
                confidence_score += 15
            elif buying_pressure > 0.7:
                confidence_score += 10
            
            # Institutional volume detection (large volume blocks)
            if self._detect_institutional_volume(volumes):
                confidence_score += 10
            
            # Convert to confidence percentage
            confidence = min(1.0, confidence_score / 145.0)
            
            # Enhanced position sizing (up to 6% for high conviction)
            if confidence > 0.8:
                position_size_pct = min(6.0, confidence * 7.5)  # Up to 6%
            elif confidence > 0.6:
                position_size_pct = min(4.0, confidence * 6.0)  # Up to 4%
            else:
                position_size_pct = min(2.0, confidence * 3.0)  # Up to 2%
            
            # Dynamic stops based on volatility
            entry_price = prices[-1]
            volatility = self._calculate_volatility(prices)
            
            # Adjust stops based on volatility
            if volatility > 0.05:  # High volatility
                stop_loss = entry_price * (1 - 0.04)  # 4% stop loss
                take_profit = entry_price * (1 + 0.08)  # 8% take profit
            else:  # Normal volatility
                stop_loss = entry_price * (1 - 0.03)  # 3% stop loss
                take_profit = entry_price * (1 + 0.06)  # 6% take profit
            
            # Enhanced reasoning
            reasoning_parts = []
            if volume_surge:
                reasoning_parts.append(f"Volume surge: {volume_ratio:.1f}x")
            if volume_spike_detected:
                reasoning_parts.append(f"Volume spike: {volume_spike:.1f}x")
            if buying_dominance:
                reasoning_parts.append(f"Buying dominance: {price_volume_correlation:.2f}")
            if high_buying_pressure:
                reasoning_parts.append(f"Buying pressure: {buying_pressure:.1%}")
            if strong_momentum:
                reasoning_parts.append(f"Strong momentum: RSI {rsi:.1f}")
            if momentum_confirmation:
                reasoning_parts.append("MACD bullish")
            if self._detect_institutional_volume(volumes):
                reasoning_parts.append("Institutional volume")
            
            reasoning = f"Enhanced Buyers Volume: {', '.join(reasoning_parts)}"
            
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=should_trade,
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size_pct=position_size_pct,
                reasoning=reasoning,
                metadata={
                    'rsi': rsi,
                    'volume_ratio': volume_ratio,
                    'volume_spike': volume_spike,
                    'price_volume_correlation': price_volume_correlation,
                    'buying_pressure': buying_pressure,
                    'macd_signal': momentum_confirmation,
                    'confidence_score': confidence_score,
                    'volatility': volatility,
                    'institutional_volume': self._detect_institutional_volume(volumes),
                    'current_volume': volumes[-1],
                    'avg_volume': np.mean(volumes[-20:])
                }
            )
            
        except Exception as e:
            log.error(f"Error in buyers volume surging strategy for {symbol}: {e}")
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning=f"Error: {str(e)}"
            )
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_volume_ratio(self, volumes: List[float]) -> float:
        """Calculate volume ratio (current vs 20-day average)"""
        if len(volumes) < 20:
            return 1.0
        
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[-20:])
        return current_volume / avg_volume if avg_volume > 0 else 1.0
    
    def _calculate_volume_spike(self, volumes: List[float]) -> float:
        """Calculate volume spike (current vs 5-period average)"""
        if len(volumes) < 6:
            return 1.0
        
        current_volume = volumes[-1]
        recent_avg = np.mean(volumes[-6:-1])  # Previous 5 periods
        return current_volume / recent_avg if recent_avg > 0 else 1.0
    
    def _calculate_price_volume_correlation(self, prices: List[float], volumes: List[float]) -> float:
        """Calculate price-volume correlation (positive = buying pressure)"""
        if len(prices) < 10 or len(volumes) < 10:
            return 0.0
        
        # Use recent 10 periods
        recent_prices = prices[-10:]
        recent_volumes = volumes[-10:]
        
        # Calculate price changes
        price_changes = [recent_prices[i] - recent_prices[i-1] for i in range(1, len(recent_prices))]
        
        # Calculate volume changes
        volume_changes = [recent_volumes[i] - recent_volumes[i-1] for i in range(1, len(recent_volumes))]
        
        if len(price_changes) < 2 or len(volume_changes) < 2:
            return 0.0
        
        # Calculate correlation
        correlation = np.corrcoef(price_changes, volume_changes)[0, 1]
        return correlation if not np.isnan(correlation) else 0.0
    
    def _calculate_buying_pressure(self, prices: List[float], volumes: List[float]) -> float:
        """Calculate buying pressure index (0-1, higher = more buying)"""
        if len(prices) < 5 or len(volumes) < 5:
            return 0.5
        
        # Recent price and volume data
        recent_prices = prices[-5:]
        recent_volumes = volumes[-5:]
        
        # Calculate price momentum
        price_momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # Calculate volume momentum
        volume_momentum = (recent_volumes[-1] - recent_volumes[0]) / recent_volumes[0] if recent_volumes[0] > 0 else 0
        
        # Calculate buying pressure score
        price_score = max(0, min(1, (price_momentum + 0.05) / 0.1))  # Normalize -5% to +5%
        volume_score = max(0, min(1, (volume_momentum + 0.5) / 1.0))  # Normalize -50% to +50%
        
        # Combine scores (weighted average)
        buying_pressure = (price_score * 0.6) + (volume_score * 0.4)
        
        return max(0.0, min(1.0, buying_pressure))
    
    def _detect_institutional_volume(self, volumes: List[float]) -> bool:
        """Detect potential institutional volume (large volume blocks)"""
        if len(volumes) < 20:
            return False
        
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[-20:])
        volume_std = np.std(volumes[-20:])
        
        # Detect volume > 2 standard deviations above mean
        return current_volume > (avg_volume + 2 * volume_std)
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility"""
        if len(prices) < 20:
            return 0.0
        
        recent_prices = prices[-20:]
        returns = [(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] 
                  for i in range(1, len(recent_prices))]
        
        return np.std(returns) if returns else 0.0
    
    def _check_macd_signal(self, prices: List[float]) -> bool:
        """Check MACD bullish signal"""
        if len(prices) < 26:
            return False
        
        # Calculate EMAs
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        macd_line = ema_12 - ema_26
        macd_signal = self._calculate_ema([macd_line] * len(prices), 9)  # Simplified
        
        return macd_line > macd_signal
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return np.mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema

class ORBBreakoutStrategy(BaseStrategy):
    """Opening Range Breakout Strategy - ORB +0.5 or +1.0 score required"""
    
    def __init__(self):
        super().__init__(StrategyType.ORB_BREAKOUT)
        self.orb_window = 15  # 15-minute opening candle (9:30-9:45 AM ET)
        self.min_orb_score = 0.5  # +0.5 minimum score
        
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> StrategyResult:
        try:
            # Placeholder implementation - would need intraday data for ORB analysis
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning="ORB analysis requires intraday data"
            )
        except Exception as e:
            log.error(f"Error in ORB breakout strategy for {symbol}: {e}")
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning=f"Error: {str(e)}"
            )

class QuantumStrategy(BaseStrategy):
    """Quantum trading strategy - 35% weekly target, 10+ quantum score required"""
    
    def __init__(self):
        super().__init__(StrategyType.QUANTUM)
        self.target_return = 0.35  # 35% weekly
        self.risk_level = 0.10  # 10% base risk per trade
        self.position_size = 0.30  # 30% of equity per trade
        self.confidence_threshold = 0.95  # 95% confidence required
        self.required_score = 10  # 10+ quantum score required
        
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> StrategyResult:
        try:
            # Placeholder implementation - would integrate with ML models
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning="Quantum strategy requires ML model integration"
            )
        except Exception as e:
            log.error(f"Error in quantum strategy for {symbol}: {e}")
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning=f"Error: {str(e)}"
            )

class NewsSentimentStrategy(BaseStrategy):
    """News Sentiment Strategy - VADER sentiment analysis with Bull/Bear awareness"""
    
    def __init__(self, news_manager=None):
        super().__init__(StrategyType.NEWS_SENTIMENT)
        self.min_sentiment_score = 0.3  # 30% sentiment strength threshold
        self.min_confidence = 0.6  # 60% confidence threshold
        self.news_manager = news_manager
        self.sentiment_mapping = self._load_sentiment_mapping()
        
    def _load_sentiment_mapping(self):
        """Load sentiment mapping data for Bull/Bear classification"""
        try:
            import json
            with open("data/watchlist/complete_sentiment_mapping.json", 'r') as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"Could not load sentiment mapping: {e}")
            return {"bull_bear_pairs": {}}
    
    def _get_symbol_context(self, symbol: str):
        """Get sentiment context for a symbol"""
        return self.sentiment_mapping.get("bull_bear_pairs", {}).get(symbol)
    
    def _classify_etf_type(self, symbol: str):
        """Classify symbol as Bull, Bear, or Unknown ETF"""
        context = self._get_symbol_context(symbol)
        if not context:
            return "unknown", ""
        
        # Check if it's a bull ETF (has a bear counterpart)
        bear_etf = context.get("bear_etf")
        if bear_etf and bear_etf != "N/A":
            return "bull", context.get("underlying", "")
        
        # Check if it's a bear ETF (has a bull counterpart)
        bull_etf = context.get("bull_etf")
        if bull_etf and bull_etf != "N/A":
            return "bear", context.get("underlying", "")
        
        # No pair found - treat as bull by default
        return "bull", context.get("underlying", "")
    
    def _analyze_sentiment_alignment(self, symbol: str, sentiment_score: float):
        """Analyze sentiment alignment for Bull/Bear ETFs"""
        etf_type, underlying_asset = self._classify_etf_type(symbol)
        
        # Determine sentiment direction
        if sentiment_score > 0.1:
            sentiment_direction = "positive"
        elif sentiment_score < -0.1:
            sentiment_direction = "negative"
        else:
            sentiment_direction = "neutral"
        
        # Calculate alignment based on ETF type and sentiment
        if etf_type == "bull":
            # Bull ETF: Positive sentiment = aligned, Negative = misaligned
            is_aligned = sentiment_direction == "positive"
            trading_recommendation = "BUY" if is_aligned else "AVOID"
        elif etf_type == "bear":
            # Bear ETF: Negative sentiment = aligned, Positive = misaligned
            is_aligned = sentiment_direction == "negative"
            trading_recommendation = "BUY" if is_aligned else "AVOID"
        else:
            # Unknown ETF: Treat as bull (positive sentiment = aligned)
            is_aligned = sentiment_direction == "positive"
            trading_recommendation = "BUY" if is_aligned else "AVOID"
        
        return {
            'is_aligned': is_aligned,
            'etf_type': etf_type,
            'underlying_asset': underlying_asset,
            'sentiment_direction': sentiment_direction,
            'trading_recommendation': trading_recommendation,
            'reasoning': f"{etf_type.upper()} ETF: {sentiment_direction} sentiment → {'aligned' if is_aligned else 'misaligned'}"
        }
        
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> StrategyResult:
        try:
            # Check if news manager is available
            if not self.news_manager:
                return StrategyResult(
                    strategy_type=self.strategy_type,
                    symbol=symbol,
                    should_trade=False,
                    confidence=0.0,
                    entry_price=0.0,
                    reasoning="News manager not available"
                )
            
            # Analyze news sentiment
            sentiment_result = await self.news_manager.analyze_news_sentiment(symbol, lookback_hours=24)
            
            # Check if we have enough news data
            if sentiment_result.news_count < 3:
                return StrategyResult(
                    strategy_type=self.strategy_type,
                    symbol=symbol,
                    should_trade=False,
                    confidence=0.0,
                    entry_price=0.0,
                    reasoning=f"Insufficient news data ({sentiment_result.news_count} items)"
                )
            
            # Check sentiment confidence
            if sentiment_result.sentiment_confidence < self.min_confidence:
                return StrategyResult(
                    strategy_type=self.strategy_type,
                    symbol=symbol,
                    should_trade=False,
                    confidence=0.0,
                    entry_price=0.0,
                    reasoning=f"Low sentiment confidence ({sentiment_result.sentiment_confidence:.2f})"
                )
            
            # Analyze sentiment alignment with Bull/Bear awareness
            sentiment_score = sentiment_result.overall_sentiment
            alignment = self._analyze_sentiment_alignment(symbol, sentiment_score)
            
            # Determine if we should trade based on alignment
            should_trade = (alignment['is_aligned'] and 
                          abs(sentiment_score) >= self.min_sentiment_score and
                          alignment['trading_recommendation'] == "BUY")
            
            # Calculate confidence with alignment boost
            base_confidence = (abs(sentiment_score) * 
                             sentiment_result.sentiment_confidence * 
                             sentiment_result.news_quality_score)
            
            # Add confidence boost for aligned sentiment
            confidence_boost = 0.0
            if alignment['is_aligned'] and abs(sentiment_score) >= self.min_sentiment_score:
                confidence_boost = 0.2 * abs(sentiment_score)  # 20% boost for aligned sentiment
            
            enhanced_confidence = min(1.0, base_confidence + confidence_boost)
            
            # Get entry price from market data
            entry_price = market_data.get('price', 0.0)
            
            # Enhanced reasoning with Bull/Bear context
            reasoning = f"{alignment['reasoning']} | {alignment['trading_recommendation']} | Confidence: {enhanced_confidence:.2f}"
            
            # Add enhanced news sentiment to market data for risk manager
            market_data['news_sentiment'] = {
                'sentiment_score': sentiment_score,
                'sentiment_direction': alignment['sentiment_direction'],
                'etf_type': alignment['etf_type'],
                'underlying_asset': alignment['underlying_asset'],
                'is_aligned': alignment['is_aligned'],
                'trading_recommendation': alignment['trading_recommendation'],
                'confidence_boost': confidence_boost,
                'enhanced_confidence': enhanced_confidence,
                'confidence': sentiment_result.sentiment_confidence,
                'news_count': sentiment_result.news_count,
                'trading_implications': sentiment_result.trading_implications,
                'breaking_news': sentiment_result.breaking_news,
                'earnings_related': sentiment_result.earnings_related
            }
            
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=should_trade,
                confidence=enhanced_confidence,
                entry_price=entry_price,
                reasoning=reasoning
            )
            
        except Exception as e:
            log.error(f"Error in news sentiment strategy for {symbol}: {e}")
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning=f"Error: {str(e)}"
            )

class TechnicalConfirmationStrategy(BaseStrategy):
    """Technical Confirmation Strategy - Multi-indicator confirmation"""
    
    def __init__(self):
        super().__init__(StrategyType.TECHNICAL_CONFIRMATION)
        self.min_confirmations = 3  # Minimum 3 technical confirmations
        
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> StrategyResult:
        try:
            # Placeholder implementation - would check multiple technical indicators
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning="Technical confirmation requires comprehensive indicator analysis"
            )
        except Exception as e:
            log.error(f"Error in technical confirmation strategy for {symbol}: {e}")
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning=f"Error: {str(e)}"
            )

class AdvancedStrategy(BaseStrategy):
    """Advanced trading strategy - 20% weekly target, 8+ score required"""
    
    def __init__(self):
        super().__init__(StrategyType.ADVANCED)
        self.target_return = 0.20  # 20% weekly
        self.risk_level = 0.05  # 5% base risk per trade
        self.position_size = 0.20  # 20% of equity per trade
        self.confidence_threshold = 0.90  # 90% confidence required
        self.required_score = 8  # 8+ score required
        self.lookback_period = 20  # 20-day lookback period
        self.deviation_threshold = 2.0  # 2 standard deviations for mean reversion
        
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> StrategyResult:
        try:
            prices = market_data.get('prices', [])
            
            if len(prices) < self.lookback_period:
                return StrategyResult(
                    strategy_type=self.strategy_type,
                    symbol=symbol,
                    should_trade=False,
                    confidence=0.0,
                    entry_price=0.0,
                    reasoning="Insufficient price data"
                )
            
            # Calculate moving average and standard deviation
            recent_prices = prices[-self.lookback_period:]
            mean_price = np.mean(recent_prices)
            std_price = np.std(recent_prices)
            
            current_price = prices[-1]
            
            # Calculate z-score
            z_score = (current_price - mean_price) / std_price if std_price > 0 else 0
            
            # Mean reversion signal (price below mean)
            should_trade = abs(z_score) > self.deviation_threshold
            
            # Calculate confidence
            confidence = self._calculate_confidence(abs(z_score) * 25)  # Scale z-score
            
            # Calculate position size
            position_size_pct = min(4.0, confidence * 4.0)  # Max 4% per strategy
            
            # Calculate stops
            entry_price = current_price
            stop_loss = entry_price * (1 - 0.03)  # 3% stop loss
            take_profit = mean_price  # Target mean reversion
            
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=should_trade,
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size_pct=position_size_pct,
                reasoning=f"Z-score: {z_score:.2f}, Mean: ${mean_price:.2f}",
                metadata={
                    'z_score': z_score,
                    'mean_price': mean_price,
                    'std_price': std_price
                }
            )
            
        except Exception as e:
            log.error(f"Error in mean reversion strategy for {symbol}: {e}")
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning=f"Error: {str(e)}"
            )

class BreakoutStrategy(BaseStrategy):
    """Breakout trading strategy"""
    
    def __init__(self):
        super().__init__(StrategyType.BREAKOUT)
        self.lookback_period = 20
        self.breakout_threshold = 0.01  # 1% breakout
        
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> StrategyResult:
        try:
            prices = market_data.get('prices', [])
            volumes = market_data.get('volumes', [])
            
            if len(prices) < self.lookback_period:
                return StrategyResult(
                    strategy_type=self.strategy_type,
                    symbol=symbol,
                    should_trade=False,
                    confidence=0.0,
                    entry_price=0.0,
                    reasoning="Insufficient price data"
                )
            
            # Calculate resistance and support levels
            recent_prices = prices[-self.lookback_period:]
            resistance = max(recent_prices)
            support = min(recent_prices)
            
            current_price = prices[-1]
            
            # Check for breakout
            breakout_up = current_price > resistance * (1 + self.breakout_threshold)
            breakout_down = current_price < support * (1 - self.breakout_threshold)
            
            should_trade = breakout_up or breakout_down
            
            # Volume confirmation
            current_volume = volumes[-1] if volumes else 0
            avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else current_volume
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Calculate confidence
            breakout_strength = abs(current_price - resistance) / resistance if breakout_up else abs(current_price - support) / support
            volume_score = min(50, (volume_ratio - 1) * 100)
            confidence = self._calculate_confidence(breakout_strength * 1000 + volume_score)
            
            # Calculate position size
            position_size_pct = min(6.0, confidence * 6.0)  # Max 6% per strategy
            
            # Calculate stops
            entry_price = current_price
            if breakout_up:
                stop_loss = resistance  # Below resistance
                take_profit = entry_price * (1 + 0.06)  # 6% target
            else:
                stop_loss = support  # Above support
                take_profit = entry_price * (1 - 0.06)  # 6% target
            
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=should_trade,
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size_pct=position_size_pct,
                reasoning=f"Breakout: {'UP' if breakout_up else 'DOWN'}, Volume: {volume_ratio:.1f}x",
                metadata={
                    'breakout_direction': 'UP' if breakout_up else 'DOWN',
                    'resistance': resistance,
                    'support': support,
                    'volume_ratio': volume_ratio
                }
            )
            
        except Exception as e:
            log.error(f"Error in breakout strategy for {symbol}: {e}")
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning=f"Error: {str(e)}"
            )

class VolumeProfileStrategy(BaseStrategy):
    """Volume profile trading strategy"""
    
    def __init__(self):
        super().__init__(StrategyType.VOLUME_PROFILE)
        self.volume_threshold = 1.5  # 50% above average volume
        
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> StrategyResult:
        try:
            prices = market_data.get('prices', [])
            volumes = market_data.get('volumes', [])
            
            if len(volumes) < 20:
                return StrategyResult(
                    strategy_type=self.strategy_type,
                    symbol=symbol,
                    should_trade=False,
                    confidence=0.0,
                    entry_price=0.0,
                    reasoning="Insufficient volume data"
                )
            
            # Calculate volume profile
            current_volume = volumes[-1]
            avg_volume = np.mean(volumes[-20:])
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Price movement with volume
            current_price = prices[-1]
            prev_price = prices[-2] if len(prices) > 1 else current_price
            price_change = (current_price - prev_price) / prev_price if prev_price > 0 else 0
            
            # Volume confirmation signal
            should_trade = (
                volume_ratio > self.volume_threshold and
                abs(price_change) > 0.005  # 0.5% price movement
            )
            
            # Calculate confidence
            volume_score = min(60, (volume_ratio - 1) * 100)
            price_score = min(40, abs(price_change) * 10000)
            confidence = self._calculate_confidence(volume_score + price_score)
            
            # Calculate position size
            position_size_pct = min(3.0, confidence * 3.0)  # Max 3% per strategy
            
            # Calculate stops
            entry_price = current_price
            stop_loss = entry_price * (1 - 0.025)  # 2.5% stop loss
            take_profit = entry_price * (1 + 0.05)  # 5% take profit
            
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=should_trade,
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size_pct=position_size_pct,
                reasoning=f"Volume: {volume_ratio:.1f}x, Price: {price_change:+.2%}",
                metadata={
                    'volume_ratio': volume_ratio,
                    'price_change': price_change,
                    'current_volume': current_volume,
                    'avg_volume': avg_volume
                }
            )
            
        except Exception as e:
            log.error(f"Error in volume profile strategy for {symbol}: {e}")
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning=f"Error: {str(e)}"
            )

class TechnicalIndicatorsStrategy(BaseStrategy):
    """Technical indicators trading strategy"""
    
    def __init__(self):
        super().__init__(StrategyType.TECHNICAL_INDICATORS)
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> StrategyResult:
        try:
            prices = market_data.get('prices', [])
            
            if len(prices) < 30:
                return StrategyResult(
                    strategy_type=self.strategy_type,
                    symbol=symbol,
                    should_trade=False,
                    confidence=0.0,
                    entry_price=0.0,
                    reasoning="Insufficient price data for indicators"
                )
            
            # Calculate RSI
            rsi = self._calculate_rsi(prices, self.rsi_period)
            
            # Calculate MACD
            macd_line, macd_signal, macd_histogram = self._calculate_macd(prices)
            
            # Calculate moving averages
            ma_20 = np.mean(prices[-20:])
            ma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else np.mean(prices)
            
            current_price = prices[-1]
            
            # Technical signal logic
            bullish_signals = 0
            bearish_signals = 0
            
            # RSI signals
            if rsi < 30:  # Oversold
                bullish_signals += 1
            elif rsi > 70:  # Overbought
                bearish_signals += 1
            
            # MACD signals
            if macd_line > macd_signal and macd_histogram > 0:
                bullish_signals += 1
            elif macd_line < macd_signal and macd_histogram < 0:
                bearish_signals += 1
            
            # Moving average signals
            if current_price > ma_20 > ma_50:
                bullish_signals += 1
            elif current_price < ma_20 < ma_50:
                bearish_signals += 1
            
            # Determine if should trade
            should_trade = bullish_signals >= 2 or bearish_signals >= 2
            
            # Calculate confidence
            signal_strength = max(bullish_signals, bearish_signals)
            confidence = self._calculate_confidence(signal_strength * 25)  # 25% per signal
            
            # Calculate position size
            position_size_pct = min(4.0, confidence * 4.0)  # Max 4% per strategy
            
            # Calculate stops
            entry_price = current_price
            stop_loss = entry_price * (1 - 0.03)  # 3% stop loss
            take_profit = entry_price * (1 + 0.06)  # 6% take profit
            
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=should_trade,
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size_pct=position_size_pct,
                reasoning=f"RSI: {rsi:.1f}, MACD: {macd_line:.3f}, Signals: {signal_strength}",
                metadata={
                    'rsi': rsi,
                    'macd_line': macd_line,
                    'macd_signal': macd_signal,
                    'macd_histogram': macd_histogram,
                    'ma_20': ma_20,
                    'ma_50': ma_50,
                    'bullish_signals': bullish_signals,
                    'bearish_signals': bearish_signals
                }
            )
            
        except Exception as e:
            log.error(f"Error in technical indicators strategy for {symbol}: {e}")
            return StrategyResult(
                strategy_type=self.strategy_type,
                symbol=symbol,
                should_trade=False,
                confidence=0.0,
                entry_price=0.0,
                reasoning=f"Error: {str(e)}"
            )
    
    def _calculate_rsi(self, prices: List[float], period: int) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: List[float]) -> Tuple[float, float, float]:
        """Calculate MACD"""
        if len(prices) < self.macd_slow:
            return 0.0, 0.0, 0.0
        
        # Calculate EMAs
        ema_fast = self._calculate_ema(prices, self.macd_fast)
        ema_slow = self._calculate_ema(prices, self.macd_slow)
        
        macd_line = ema_fast - ema_slow
        
        # Calculate MACD signal line (EMA of MACD line)
        macd_values = [ema_fast - ema_slow for _ in range(len(prices))]
        macd_signal = self._calculate_ema(macd_values, self.macd_signal)
        
        macd_histogram = macd_line - macd_signal
        
        return macd_line, macd_signal, macd_histogram
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return np.mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema

# ============================================================================
# MULTI-STRATEGY MANAGER
# ============================================================================

class PrimeMultiStrategyManager:
    """
    Multi-Strategy Manager
    Coordinates multiple trading strategies and provides cross-validation
    """
    
    def __init__(self):
        self.strategies = {
            StrategyType.STANDARD: StandardStrategy(),
            StrategyType.ADVANCED: AdvancedStrategy(),
            StrategyType.QUANTUM: QuantumStrategy(),
            StrategyType.RSI_POSITIVITY: RSIPositivityStrategy(),
            StrategyType.BUYERS_VOLUME_SURGING: BuyersVolumeSurgingStrategy(),
            StrategyType.ORB_BREAKOUT: ORBBreakoutStrategy(),
            StrategyType.NEWS_SENTIMENT: NewsSentimentStrategy(),
            StrategyType.TECHNICAL_CONFIRMATION: TechnicalConfirmationStrategy(),
        }
        
        # Agreement bonuses
        self.agreement_bonuses = {
            AgreementLevel.NONE: 0.0,
            AgreementLevel.LOW: 0.0,
            AgreementLevel.MEDIUM: 0.25,  # +0.25% for 2 strategies
            AgreementLevel.HIGH: 0.50,    # +0.50% for 3 strategies
            AgreementLevel.MAXIMUM: 1.00   # +1.00% for 4+ strategies
        }
        
        # Confidence bonuses
        self.confidence_bonuses = {
            AgreementLevel.NONE: 0.0,
            AgreementLevel.LOW: 0.1,
            AgreementLevel.MEDIUM: 0.2,
            AgreementLevel.HIGH: 0.3,
            AgreementLevel.MAXIMUM: 0.5
        }
        
        # Executor for concurrent strategy execution
        self.executor = ThreadPoolExecutor(max_workers=len(self.strategies))
        
        log.info(f"Multi-Strategy Manager initialized with {len(self.strategies)} strategies")
    
    async def analyze_symbol(self, symbol: str, market_data: Dict[str, Any]) -> MultiStrategyResult:
        """Analyze symbol using all strategies"""
        try:
            # Run all strategies concurrently
            tasks = []
            for strategy_type, strategy in self.strategies.items():
                if strategy.enabled:
                    task = asyncio.create_task(strategy.analyze(symbol, market_data))
                    tasks.append((strategy_type, task))
            
            # Wait for all strategies to complete
            results = {}
            for strategy_type, task in tasks:
                try:
                    result = await task
                    results[strategy_type] = result
                except Exception as e:
                    log.error(f"Strategy {strategy_type.value} failed for {symbol}: {e}")
                    results[strategy_type] = StrategyResult(
                        strategy_type=strategy_type,
                        symbol=symbol,
                        should_trade=False,
                        confidence=0.0,
                        entry_price=0.0,
                        reasoning=f"Strategy failed: {str(e)}"
                    )
            
            # Find agreeing strategies
            agreements = [strategy_type for strategy_type, result in results.items() 
                         if result.should_trade]
            
            agreement_count = len(agreements)
            
            # Determine agreement level
            if agreement_count >= 4:
                agreement_level = AgreementLevel.MAXIMUM
            elif agreement_count >= 3:
                agreement_level = AgreementLevel.HIGH
            elif agreement_count >= 2:
                agreement_level = AgreementLevel.MEDIUM
            elif agreement_count >= 1:
                agreement_level = AgreementLevel.LOW
            else:
                agreement_level = AgreementLevel.NONE
            
            # Calculate bonuses
            size_bonus = self.agreement_bonuses[agreement_level]
            confidence_bonus = self.confidence_bonuses[agreement_level]
            
            # Calculate final metrics
            should_trade = agreement_count >= 2  # Minimum 2 strategies must agree
            
            if should_trade:
                # Calculate weighted average confidence
                agreeing_results = [results[strategy_type] for strategy_type in agreements]
                total_confidence = sum(result.confidence for result in agreeing_results)
                avg_confidence = total_confidence / len(agreeing_results)
                final_confidence = min(1.0, avg_confidence + confidence_bonus)
                
                # Calculate weighted average position size
                total_position_size = sum(result.position_size_pct for result in agreeing_results)
                avg_position_size = total_position_size / len(agreeing_results)
                final_position_size_pct = avg_position_size * (1 + size_bonus)
                
                # Use most confident strategy's entry price and stops
                best_result = max(agreeing_results, key=lambda x: x.confidence)
                entry_price = best_result.entry_price
                stop_loss = best_result.stop_loss
                take_profit = best_result.take_profit
                
                # Combine reasoning
                reasoning_parts = [f"{strategy.value}: {result.reasoning}" 
                                 for strategy, result in results.items() 
                                 if result.should_trade]
                reasoning = " | ".join(reasoning_parts)
                
            else:
                final_confidence = 0.0
                final_position_size_pct = 0.0
                entry_price = 0.0
                stop_loss = None
                take_profit = None
                reasoning = f"Only {agreement_count} strategy(ies) agree (minimum 2 required)"
            
            return MultiStrategyResult(
                symbol=symbol,
                strategies=results,
                agreements=agreements,
                agreement_count=agreement_count,
                agreement_level=agreement_level,
                size_bonus=size_bonus,
                confidence_bonus=confidence_bonus,
                should_trade=should_trade,
                final_confidence=final_confidence,
                final_position_size_pct=final_position_size_pct,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasoning=reasoning,
                metadata={
                    'strategy_count': len(self.strategies),
                    'enabled_strategies': len([s for s in self.strategies.values() if s.enabled]),
                    'analysis_time': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            log.error(f"Error in multi-strategy analysis for {symbol}: {e}")
            return MultiStrategyResult(
                symbol=symbol,
                strategies={},
                agreements=[],
                agreement_count=0,
                agreement_level=AgreementLevel.NONE,
                size_bonus=0.0,
                confidence_bonus=0.0,
                should_trade=False,
                final_confidence=0.0,
                final_position_size_pct=0.0,
                entry_price=0.0,
                reasoning=f"Analysis failed: {str(e)}"
            )
    
    async def analyze_symbols(self, symbols: List[str], market_data: Dict[str, Dict[str, Any]]) -> List[MultiStrategyResult]:
        """Analyze multiple symbols concurrently"""
        try:
            tasks = []
            for symbol in symbols:
                if symbol in market_data:
                    task = asyncio.create_task(self.analyze_symbol(symbol, market_data[symbol]))
                    tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_results = []
            for result in results:
                if isinstance(result, MultiStrategyResult):
                    valid_results.append(result)
                elif isinstance(result, Exception):
                    log.error(f"Symbol analysis failed: {result}")
            
            return valid_results
            
        except Exception as e:
            log.error(f"Error in multi-symbol analysis: {e}")
            return []
    
    def get_strategy_performance(self) -> Dict[str, Any]:
        """Get performance metrics for each strategy"""
        performance = {}
        
        for strategy_type, strategy in self.strategies.items():
            performance[strategy_type.value] = {
                'enabled': strategy.enabled,
                'weight': strategy.weight,
                'type': strategy.strategy_type.value
            }
        
        return performance
    
    def enable_strategy(self, strategy_type: StrategyType, enabled: bool = True):
        """Enable or disable a strategy"""
        if strategy_type in self.strategies:
            self.strategies[strategy_type].enabled = enabled
            log.info(f"Strategy {strategy_type.value} {'enabled' if enabled else 'disabled'}")
    
    def set_strategy_weight(self, strategy_type: StrategyType, weight: float):
        """Set weight for a strategy"""
        if strategy_type in self.strategies:
            self.strategies[strategy_type].weight = weight
            log.info(f"Strategy {strategy_type.value} weight set to {weight}")
    
    async def shutdown(self):
        """Shutdown the multi-strategy manager"""
        try:
            self.executor.shutdown(wait=True)
            log.info("Multi-Strategy Manager shutdown complete")
        except Exception as e:
            log.error(f"Error during shutdown: {e}")

# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def get_multi_strategy_manager() -> PrimeMultiStrategyManager:
    """Get multi-strategy manager instance"""
    return PrimeMultiStrategyManager()

def create_multi_strategy_manager() -> PrimeMultiStrategyManager:
    """Create new multi-strategy manager instance"""
    return PrimeMultiStrategyManager()

log.info("Prime Multi-Strategy Manager loaded successfully")
