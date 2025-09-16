#!/usr/bin/env python3
"""
Prime Symbol Selector
====================

Enhanced symbol selection system that identifies high probability trading setups
by analyzing core and dynamic symbol lists with comprehensive scoring.

Author: Easy ETrade Strategy Team
Version: 1.0.0
"""

import asyncio
import logging
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    from .prime_models import StrategyMode, SignalSide, ConfidenceTier
    from .prime_data_manager import PrimeDataManager, DataRequest, DataProvider
    from .production_signal_generator import EnhancedProductionSignalGenerator
    from .config_loader import get_config_value
except ImportError:
    from prime_models import StrategyMode, SignalSide, ConfidenceTier
    from production_signal_generator import EnhancedProductionSignalGenerator
    from config_loader import get_config_value
    
    # Mock data manager for testing
    class DataProvider:
        ETRADE = "etrade"
        YAHOO = "yahoo"
    
    class DataRequest:
        def __init__(self, symbol, data_type, timeframe, period, provider_preference):
            self.symbol = symbol
            self.data_type = data_type
            self.timeframe = timeframe
            self.period = period
            self.provider_preference = provider_preference
    
    class PrimeDataManager:
        def __init__(self):
            pass
        
        async def get_market_data(self, request):
            class MockResponse:
                def __init__(self):
                    self.data = self.generate_test_data()
            
            return MockResponse()
        
        def generate_test_data(self):
            # Generate test data
            import numpy as np
            from datetime import datetime, timedelta
            
            market_data = []
            base_price = 100.0
            base_volume = 1000000
            
            for i in range(100):
                price_change = np.random.uniform(-0.02, 0.02)
                base_price *= (1 + price_change)
                volume = base_volume * np.random.uniform(0.8, 1.2)
                
                market_data.append({
                    'timestamp': datetime.utcnow() - timedelta(days=100-i),
                    'open': base_price * np.random.uniform(0.998, 1.002),
                    'high': base_price * np.random.uniform(1.001, 1.01),
                    'low': base_price * np.random.uniform(0.99, 0.999),
                    'close': base_price,
                    'volume': int(volume)
                })
            
            return market_data

log = logging.getLogger("prime_symbol_selector")

class SymbolQuality(Enum):
    """Symbol quality levels"""
    EXCELLENT = "excellent"  # 90-100%
    HIGH = "high"           # 80-89%
    GOOD = "good"           # 70-79%
    FAIR = "fair"           # 60-69%
    POOR = "poor"           # <60%

@dataclass
class SymbolScore:
    """Symbol scoring results"""
    symbol: str
    quality_score: float
    confidence_score: float
    volume_score: float
    momentum_score: float
    technical_score: float
    rsi_score: float
    volatility_score: float
    trend_score: float
    overall_score: float
    quality_tier: SymbolQuality
    setup_probability: float
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class SymbolSelectionResult:
    """Symbol selection results"""
    selected_symbols: List[SymbolScore]
    total_analyzed: int
    high_quality_count: int
    average_quality: float
    selection_time: float
    market_conditions: Dict[str, Any]

class PrimeSymbolSelector:
    """
    Enhanced symbol selection system for high probability trading setups
    
    Integrates with Prime Data Manager to analyze core and dynamic symbol lists
    and identify the best trading opportunities based on comprehensive scoring.
    """
    
    def __init__(self, data_manager: PrimeDataManager):
        self.data_manager = data_manager
        self.signal_generator = EnhancedProductionSignalGenerator()
        
        # Core symbol lists
        self.core_symbols = [
            # Major ETFs
            'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VEA', 'VWO', 'AGG', 'TLT', 'GLD',
            # Sector ETFs
            'XLF', 'XLE', 'XLV', 'XLK', 'XLI', 'XLY', 'XLP', 'XLU', 'XLB', 'XLC',
            # Leveraged ETFs
            'TQQQ', 'SQQQ', 'SOXL', 'SOXS', 'LABU', 'LABD', 'UVXY', 'VIXY',
            # Major Tech
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'ADBE', 'CRM',
            # Growth/Momentum
            'PLTR', 'COIN', 'MARA', 'RIOT', 'SMCI', 'RIVN', 'LCID', 'ARKK', 'ARKW',
            # Sector Leaders
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'V', 'MA', 'JNJ', 'PFE', 'UNH'
        ]
        
        # Dynamic symbol list (updated based on performance)
        self.dynamic_symbols = []
        self.symbol_performance = {}
        
        # Configuration
        self.max_symbols = get_config_value("MAX_SYMBOLS", 50)
        self.min_quality_score = get_config_value("MIN_QUALITY_SCORE", 0.7)
        self.min_confidence = get_config_value("MIN_CONFIDENCE", 0.7)
        self.min_volume_ratio = get_config_value("MIN_VOLUME_RATIO", 1.2)
        self.min_rsi = get_config_value("MIN_RSI", 55.0)
        self.max_rsi = get_config_value("MAX_RSI", 80.0)
        
        # Performance tracking
        self.selection_metrics = {
            'total_selections': 0,
            'high_quality_selections': 0,
            'average_quality': 0.0,
            'selection_times': []
        }
        
        log.info("Prime Symbol Selector initialized")
    
    async def select_high_probability_symbols(self, strategy_mode: StrategyMode = StrategyMode.STANDARD) -> SymbolSelectionResult:
        """
        Select high probability trading symbols based on comprehensive analysis
        
        Args:
            strategy_mode: Strategy mode (Standard, Advanced, Quantum)
            
        Returns:
            SymbolSelectionResult with selected symbols and metrics
        """
        start_time = time.time()
        log.info(f"Starting symbol selection for {strategy_mode.value} strategy...")
        
        # Combine core and dynamic symbols
        all_symbols = list(set(self.core_symbols + self.dynamic_symbols))
        
        # Analyze each symbol
        symbol_scores = []
        for symbol in all_symbols[:100]:  # Limit to top 100 for performance
            try:
                score = await self._analyze_symbol(symbol, strategy_mode)
                if score and score.overall_score >= self.min_quality_score:
                    symbol_scores.append(score)
            except Exception as e:
                log.warning(f"Error analyzing symbol {symbol}: {e}")
                continue
        
        # Sort by overall score
        symbol_scores.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Select top symbols
        selected_count = min(self.max_symbols, len(symbol_scores))
        selected_symbols = symbol_scores[:selected_count]
        
        # Calculate metrics
        selection_time = time.time() - start_time
        high_quality_count = sum(1 for s in selected_symbols if s.quality_tier in [SymbolQuality.EXCELLENT, SymbolQuality.HIGH])
        average_quality = np.mean([s.overall_score for s in selected_symbols]) if selected_symbols else 0.0
        
        # Update performance tracking
        self.selection_metrics['total_selections'] += 1
        self.selection_metrics['high_quality_selections'] += high_quality_count
        self.selection_metrics['average_quality'] = average_quality
        self.selection_metrics['selection_times'].append(selection_time)
        
        # Get market conditions
        market_conditions = await self._get_market_conditions()
        
        result = SymbolSelectionResult(
            selected_symbols=selected_symbols,
            total_analyzed=len(all_symbols),
            high_quality_count=high_quality_count,
            average_quality=average_quality,
            selection_time=selection_time,
            market_conditions=market_conditions
        )
        
        log.info(f"Symbol selection completed: {len(selected_symbols)} symbols selected "
                f"(avg quality: {average_quality:.2f}, time: {selection_time:.2f}s)")
        
        return result
    
    async def _analyze_symbol(self, symbol: str, strategy_mode: StrategyMode) -> Optional[SymbolScore]:
        """Analyze individual symbol for trading potential"""
        try:
            # Get market data
            market_data = await self._get_symbol_data(symbol)
            if not market_data:
                return None
            
            # Calculate individual scores
            rsi_score = self._calculate_rsi_score(market_data)
            volume_score = self._calculate_volume_score(market_data)
            momentum_score = self._calculate_momentum_score(market_data)
            technical_score = self._calculate_technical_score(market_data)
            volatility_score = self._calculate_volatility_score(market_data)
            trend_score = self._calculate_trend_score(market_data)
            
            # Calculate overall scores
            quality_score = self._calculate_quality_score(
                rsi_score, volume_score, momentum_score, technical_score, 
                volatility_score, trend_score
            )
            
            confidence_score = self._calculate_confidence_score(
                quality_score, volume_score, momentum_score, market_data
            )
            
            overall_score = (quality_score * 0.4 + confidence_score * 0.6)
            
            # Determine quality tier
            quality_tier = self._determine_quality_tier(overall_score)
            
            # Calculate setup probability
            setup_probability = self._calculate_setup_probability(
                overall_score, rsi_score, volume_score, momentum_score
            )
            
            # Generate reasons and warnings
            reasons, warnings = self._generate_analysis_reasons(
                rsi_score, volume_score, momentum_score, technical_score,
                volatility_score, trend_score, overall_score
            )
            
            return SymbolScore(
                symbol=symbol,
                quality_score=quality_score,
                confidence_score=confidence_score,
                volume_score=volume_score,
                momentum_score=momentum_score,
                technical_score=technical_score,
                rsi_score=rsi_score,
                volatility_score=volatility_score,
                trend_score=trend_score,
                overall_score=overall_score,
                quality_tier=quality_tier,
                setup_probability=setup_probability,
                reasons=reasons,
                warnings=warnings
            )
            
        except Exception as e:
            log.error(f"Error analyzing symbol {symbol}: {e}")
            return None
    
    async def _get_symbol_data(self, symbol: str) -> Optional[List[Dict]]:
        """Get market data for symbol"""
        try:
            request = DataRequest(
                symbol=symbol,
                data_type="historical",
                timeframe="1d",
                period="6mo",
                provider_preference=[DataProvider.ETRADE, DataProvider.YAHOO]
            )
            
            response = await self.data_manager.get_market_data(request)
            if response.data:
                return response.data
            return None
            
        except Exception as e:
            log.warning(f"Failed to get data for {symbol}: {e}")
            return None
    
    def _calculate_rsi_score(self, market_data: List[Dict]) -> float:
        """Calculate RSI-based score"""
        if len(market_data) < 14:
            return 0.0
        
        prices = [candle['close'] for candle in market_data[-20:]]
        rsi = self._calculate_rsi(prices)
        
        # Score based on RSI range (55-80 is optimal for buy signals)
        if rsi < self.min_rsi or rsi > self.max_rsi:
            return 0.0
        elif rsi >= 55 and rsi <= 70:
            return 1.0  # Optimal range
        elif rsi > 70 and rsi <= 80:
            return 0.8  # Good but getting overbought
        else:
            return 0.5  # Acceptable but not optimal
    
    def _calculate_volume_score(self, market_data: List[Dict]) -> float:
        """Calculate volume-based score"""
        if len(market_data) < 20:
            return 0.0
        
        volumes = [candle['volume'] for candle in market_data[-20:]]
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[:-1])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Score based on volume surge (1.2x+ is good for buy signals)
        if volume_ratio >= 2.0:
            return 1.0  # Strong volume surge
        elif volume_ratio >= 1.5:
            return 0.8  # Good volume surge
        elif volume_ratio >= 1.2:
            return 0.6  # Moderate volume increase
        elif volume_ratio >= 1.0:
            return 0.4  # Average volume
        else:
            return 0.2  # Low volume
    
    def _calculate_momentum_score(self, market_data: List[Dict]) -> float:
        """Calculate momentum-based score"""
        if len(market_data) < 20:
            return 0.0
        
        prices = [candle['close'] for candle in market_data[-20:]]
        
        # Calculate price momentum
        price_change_5d = (prices[-1] - prices[-6]) / prices[-6] if len(prices) >= 6 else 0
        price_change_10d = (prices[-1] - prices[-11]) / prices[-11] if len(prices) >= 11 else 0
        
        # Score based on positive momentum
        momentum_score = 0.0
        if price_change_5d > 0.02:  # 2%+ in 5 days
            momentum_score += 0.5
        if price_change_10d > 0.05:  # 5%+ in 10 days
            momentum_score += 0.5
        
        return min(momentum_score, 1.0)
    
    def _calculate_technical_score(self, market_data: List[Dict]) -> float:
        """Calculate technical analysis score"""
        if len(market_data) < 20:
            return 0.0
        
        prices = [candle['close'] for candle in market_data[-20:]]
        current_price = prices[-1]
        
        # Moving averages
        ma_10 = np.mean(prices[-10:])
        ma_20 = np.mean(prices[-20:])
        
        # Score based on moving average alignment
        score = 0.0
        if current_price > ma_10:
            score += 0.3
        if current_price > ma_20:
            score += 0.3
        if ma_10 > ma_20:
            score += 0.4  # Uptrend
        
        return min(score, 1.0)
    
    def _calculate_volatility_score(self, market_data: List[Dict]) -> float:
        """Calculate volatility score"""
        if len(market_data) < 20:
            return 0.0
        
        prices = [candle['close'] for candle in market_data[-20:]]
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility
        
        # Score based on optimal volatility range (15-30%)
        if 0.15 <= volatility <= 0.30:
            return 1.0  # Optimal volatility
        elif 0.10 <= volatility <= 0.40:
            return 0.7  # Acceptable volatility
        elif volatility < 0.10:
            return 0.4  # Too low volatility
        else:
            return 0.2  # Too high volatility
    
    def _calculate_trend_score(self, market_data: List[Dict]) -> float:
        """Calculate trend strength score"""
        if len(market_data) < 20:
            return 0.0
        
        prices = [candle['close'] for candle in market_data[-20:]]
        
        # Linear regression to determine trend
        x = np.arange(len(prices))
        y = np.array(prices)
        slope, _ = np.polyfit(x, y, 1)
        
        # Normalize slope to score
        trend_score = min(max(slope / (prices[-1] * 0.01), 0), 1)  # Normalize by 1% of price
        
        return trend_score
    
    def _calculate_quality_score(self, rsi_score: float, volume_score: float, 
                               momentum_score: float, technical_score: float,
                               volatility_score: float, trend_score: float) -> float:
        """Calculate overall quality score"""
        weights = {
            'rsi': 0.20,
            'volume': 0.20,
            'momentum': 0.15,
            'technical': 0.15,
            'volatility': 0.15,
            'trend': 0.15
        }
        
        quality_score = (
            rsi_score * weights['rsi'] +
            volume_score * weights['volume'] +
            momentum_score * weights['momentum'] +
            technical_score * weights['technical'] +
            volatility_score * weights['volatility'] +
            trend_score * weights['trend']
        )
        
        return min(quality_score, 1.0)
    
    def _calculate_confidence_score(self, quality_score: float, volume_score: float, 
                                  momentum_score: float, market_data: List[Dict]) -> float:
        """Calculate confidence score with volume boost"""
        base_confidence = quality_score
        
        # Volume confidence boost
        volumes = [candle['volume'] for candle in market_data[-10:]]
        if len(volumes) >= 5:
            current_volume = volumes[-1]
            avg_volume = np.mean(volumes[:-1])
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            if volume_ratio >= 1.5:  # Buying volume surge
                base_confidence += 0.1  # 10% confidence boost
            elif volume_ratio >= 2.0:  # Strong buying volume surge
                base_confidence += 0.2  # 20% confidence boost
        
        return min(base_confidence, 1.0)
    
    def _determine_quality_tier(self, overall_score: float) -> SymbolQuality:
        """Determine symbol quality tier"""
        if overall_score >= 0.90:
            return SymbolQuality.EXCELLENT
        elif overall_score >= 0.80:
            return SymbolQuality.HIGH
        elif overall_score >= 0.70:
            return SymbolQuality.GOOD
        elif overall_score >= 0.60:
            return SymbolQuality.FAIR
        else:
            return SymbolQuality.POOR
    
    def _calculate_setup_probability(self, overall_score: float, rsi_score: float, 
                                   volume_score: float, momentum_score: float) -> float:
        """Calculate probability of successful trading setup"""
        # Base probability from overall score
        base_probability = overall_score * 0.8
        
        # Boost for strong indicators
        if rsi_score >= 0.8 and volume_score >= 0.8 and momentum_score >= 0.8:
            base_probability += 0.15  # 15% boost for strong signals
        elif rsi_score >= 0.6 and volume_score >= 0.6 and momentum_score >= 0.6:
            base_probability += 0.05  # 5% boost for good signals
        
        return min(base_probability, 1.0)
    
    def _generate_analysis_reasons(self, rsi_score: float, volume_score: float,
                                 momentum_score: float, technical_score: float,
                                 volatility_score: float, trend_score: float,
                                 overall_score: float) -> Tuple[List[str], List[str]]:
        """Generate analysis reasons and warnings"""
        reasons = []
        warnings = []
        
        # RSI analysis
        if rsi_score >= 0.8:
            reasons.append("RSI in optimal range (55-70)")
        elif rsi_score >= 0.6:
            reasons.append("RSI in acceptable range")
        else:
            warnings.append("RSI outside optimal range")
        
        # Volume analysis
        if volume_score >= 0.8:
            reasons.append("Strong volume surge detected")
        elif volume_score >= 0.6:
            reasons.append("Good volume increase")
        else:
            warnings.append("Low volume activity")
        
        # Momentum analysis
        if momentum_score >= 0.8:
            reasons.append("Strong positive momentum")
        elif momentum_score >= 0.6:
            reasons.append("Good momentum")
        else:
            warnings.append("Weak momentum")
        
        # Technical analysis
        if technical_score >= 0.8:
            reasons.append("Strong technical setup")
        elif technical_score >= 0.6:
            reasons.append("Good technical indicators")
        else:
            warnings.append("Weak technical setup")
        
        # Overall assessment
        if overall_score >= 0.8:
            reasons.append("High probability trading setup")
        elif overall_score >= 0.7:
            reasons.append("Good trading opportunity")
        else:
            warnings.append("Low probability setup")
        
        return reasons, warnings
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
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
    
    async def _get_market_conditions(self) -> Dict[str, Any]:
        """Get current market conditions"""
        try:
            # Get SPY data for market analysis
            spy_data = await self._get_symbol_data('SPY')
            if not spy_data:
                return {'regime': 'unknown', 'volatility': 'unknown'}
            
            # Calculate market regime
            prices = [candle['close'] for candle in spy_data[-20:]]
            price_change = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
            
            if price_change > 0.02:
                regime = 'bull'
            elif price_change < -0.02:
                regime = 'bear'
            else:
                regime = 'sideways'
            
            # Calculate volatility
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            volatility = np.std(returns) * np.sqrt(252)
            
            if volatility > 0.25:
                vol_level = 'high'
            elif volatility > 0.15:
                vol_level = 'medium'
            else:
                vol_level = 'low'
            
            return {
                'regime': regime,
                'volatility': vol_level,
                'spy_change': price_change,
                'volatility_pct': volatility
            }
            
        except Exception as e:
            log.warning(f"Error getting market conditions: {e}")
            return {'regime': 'unknown', 'volatility': 'unknown'}
    
    def get_selection_metrics(self) -> Dict[str, Any]:
        """Get symbol selection performance metrics"""
        return {
            'total_selections': self.selection_metrics['total_selections'],
            'high_quality_selections': self.selection_metrics['high_quality_selections'],
            'average_quality': self.selection_metrics['average_quality'],
            'average_selection_time': np.mean(self.selection_metrics['selection_times']) if self.selection_metrics['selection_times'] else 0.0,
            'selection_success_rate': self.selection_metrics['high_quality_selections'] / max(self.selection_metrics['total_selections'], 1)
        }
