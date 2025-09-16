# modules/unified_data_manager.py

"""
Unified Data Manager for ETrade Strategy
Consolidates all data functionality into a single, high-performance manager
Replaces: mega_data_system.py, etrade_first_data_manager.py, hybrid_data_manager.py,
          data_mux.py, enhanced_data_mux.py, optimized_data_mux.py
"""

from __future__ import annotations
import asyncio
import logging
import time
import threading
import json
import os
import hashlib
import tempfile
import shutil
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from cachetools import TTLCache
import pandas as pd
import numpy as np
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from collections import deque

from .config_loader import get_config_value

# Import E*TRADE OAuth integration
try:
    from .prime_etrade_trading import PrimeETradeTrading
    ETRADE_AVAILABLE = True
except ImportError:
    ETRADE_AVAILABLE = False
    logging.warning("E*TRADE trading module not available")

log = logging.getLogger("unified_data_manager")

# ============================================================================
# E*TRADE DATA PROVIDER
# ============================================================================

class ETradeDataProvider:
    """E*TRADE data provider with OAuth integration"""
    
    def __init__(self, etrade_oauth):
        self.etrade_oauth = etrade_oauth
        self.etrade_trader = None
        
        # Initialize E*TRADE trader if OAuth is available
        if etrade_oauth and ETRADE_AVAILABLE:
            try:
                self.etrade_trader = PrimeETradeTrading('prod' if hasattr(etrade_oauth, 'environment') and etrade_oauth.environment == 'prod' else 'demo')
                log.info("E*TRADE data provider initialized with OAuth")
            except Exception as e:
                log.error(f"Failed to initialize E*TRADE trader: {e}")
                self.etrade_trader = None
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote from E*TRADE"""
        try:
            if not self.etrade_trader:
                return None
            
            # Use E*TRADE trader to get quote
            quote_data = await self.etrade_trader.get_quote(symbol)
            if quote_data and not quote_data.get('error'):
                return {
                    'symbol': symbol,
                    'last': quote_data.get('lastPrice', 0),
                    'bid': quote_data.get('bidPrice', 0),
                    'ask': quote_data.get('askPrice', 0),
                    'open': quote_data.get('openPrice', 0),
                    'high': quote_data.get('highPrice', 0),
                    'low': quote_data.get('lowPrice', 0),
                    'volume': quote_data.get('totalVolume', 0),
                    'timestamp': datetime.utcnow().isoformat()
                }
            return None
            
        except Exception as e:
            log.error(f"Error getting E*TRADE quote for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, start_date: datetime, 
                                end_date: datetime, interval: str = "1min") -> Optional[List[Dict[str, Any]]]:
        """Get historical data from E*TRADE"""
        try:
            if not self.etrade_trader:
                return None
            
            # E*TRADE doesn't provide historical data directly
            # This would need to be implemented with a different provider
            log.warning(f"E*TRADE doesn't provide historical data for {symbol}")
            return None
            
        except Exception as e:
            log.error(f"Error getting E*TRADE historical data for {symbol}: {e}")
            return None

class YFProvider:
    """Yahoo Finance data provider (fallback)"""
    
    def __init__(self):
        self.name = "Yahoo Finance"
        log.info("Yahoo Finance provider initialized")
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote from Yahoo Finance"""
        try:
            # Placeholder implementation
            # In production, this would use yfinance or similar
            log.debug(f"Yahoo Finance quote requested for {symbol}")
            return {
                'symbol': symbol,
                'last': 100.0,  # Placeholder
                'bid': 99.95,
                'ask': 100.05,
                'open': 99.50,
                'high': 100.50,
                'low': 99.00,
                'volume': 1000000,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            log.error(f"Error getting Yahoo quote for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, start_date: datetime, 
                                end_date: datetime, interval: str = "1min") -> Optional[List[Dict[str, Any]]]:
        """Get historical data from Yahoo Finance"""
        try:
            # Placeholder implementation
            log.debug(f"Yahoo Finance historical data requested for {symbol}")
            return []
        except Exception as e:
            log.error(f"Error getting Yahoo historical data for {symbol}: {e}")
            return None

class PolygonProvider:
    """Polygon data provider (premium)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.name = "Polygon"
        log.info("Polygon provider initialized")
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote from Polygon"""
        try:
            # Placeholder implementation
            log.debug(f"Polygon quote requested for {symbol}")
            return {
                'symbol': symbol,
                'last': 100.0,  # Placeholder
                'bid': 99.95,
                'ask': 100.05,
                'open': 99.50,
                'high': 100.50,
                'low': 99.00,
                'volume': 1000000,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            log.error(f"Error getting Polygon quote for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, start_date: datetime, 
                                end_date: datetime, interval: str = "1min") -> Optional[List[Dict[str, Any]]]:
        """Get historical data from Polygon"""
        try:
            # Placeholder implementation
            log.debug(f"Polygon historical data requested for {symbol}")
            return []
        except Exception as e:
            log.error(f"Error getting Polygon historical data for {symbol}: {e}")
            return None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_data_processor():
    """Get data processor instance"""
    return None  # Placeholder

def get_data_cache():
    """Get data cache instance"""
    return None  # Placeholder

# ============================================================================
# ENUMS
# ============================================================================

class DataProvider(Enum):
    """Data provider enumeration"""
    ETRADE = "etrade"
    YAHOO = "yahoo"
    POLYGON = "polygon"
    ALPHA_VANTAGE = "alpha_vantage"

class DataQuality(Enum):
    """Data quality enumeration"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class DataType(Enum):
    """Data type enumeration"""
    REAL_TIME = "real_time"
    HISTORICAL = "historical"
    PREMARKET = "premarket"
    POSTMARKET = "postmarket"

class CacheStrategy(Enum):
    """Cache strategy enumeration"""
    TTL = "ttl"
    LRU = "lru"
    LFU = "lfu"
    ADAPTIVE = "adaptive"

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class MarketData:
    """Unified market data structure"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    provider: DataProvider
    quality: DataQuality
    data_type: DataType
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Quote:
    """Real-time quote data"""
    symbol: str
    price: float
    bid: float
    ask: float
    size: int
    timestamp: datetime
    provider: DataProvider
    quality: DataQuality

@dataclass
class DataRequest:
    """Data request specification"""
    symbol: str
    data_type: DataType
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    interval: str = "1min"
    provider_preference: List[DataProvider] = field(default_factory=lambda: [DataProvider.ETRADE, DataProvider.YAHOO])
    cache_ttl: int = 300
    priority: int = 1

@dataclass
class DataResponse:
    """Data response with metadata"""
    data: Union[MarketData, Quote, List[MarketData]]
    provider_used: DataProvider
    quality: DataQuality
    cache_hit: bool
    response_time: float
    error: Optional[str] = None

@dataclass
class ProviderMetrics:
    """Provider performance metrics"""
    provider: DataProvider
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    daily_calls: int = 0
    daily_limit: int = 0
    calls_remaining: int = 0

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0
    hit_rate: float = 0.0

# ============================================================================
# UNIFIED DATA MANAGER
# ============================================================================

class PrimeDataManager:
    """
    Unified Data Manager
    Consolidates all data functionality into a single, high-performance manager
    """
    
    def __init__(self, etrade_oauth: Optional[Any] = None):
        self.etrade_oauth = etrade_oauth
        
        # Initialize providers
        self.providers: Dict[DataProvider, Any] = {}
        self._initialize_providers()
        
        # Initialize async data processor
        self.async_processor = get_data_processor()
        self.data_cache = get_data_cache()
        
        # Caching system
        self.cache_strategy = CacheStrategy.ADAPTIVE
        self.cache = TTLCache(maxsize=10000, ttl=300)
        self.quote_cache = TTLCache(maxsize=1000, ttl=60)
        self.historical_cache = TTLCache(maxsize=5000, ttl=3600)
        
        # Performance tracking
        self.provider_metrics: Dict[DataProvider, ProviderMetrics] = {}
        self.cache_metrics = CacheMetrics()
        self.request_history: deque = deque(maxlen=10000)
        
        # Circuit breaker
        self.circuit_breakers: Dict[DataProvider, bool] = {}
        self.failure_counts: Dict[DataProvider, int] = {}
        self.last_failure: Dict[DataProvider, datetime] = {}
        
        # Configuration
        self.max_retries = get_config_value("DATA_MAX_RETRIES", 3)
        self.timeout = get_config_value("DATA_TIMEOUT", 30)
        self.cache_enabled = get_config_value("DATA_CACHE_ENABLED", True)
        self.fallback_enabled = get_config_value("DATA_FALLBACK_ENABLED", True)
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=16)
        self.lock = threading.RLock()
        
        # Statistics
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.fallback_activations = 0
        
        log.info("Unified Data Manager initialized with all providers")
    
    def _initialize_providers(self):
        """Initialize all data providers"""
        try:
            # ETRADE provider (primary)
            if self.etrade_oauth:
                self.providers[DataProvider.ETRADE] = ETradeDataProvider(self.etrade_oauth)
                self.provider_metrics[DataProvider.ETRADE] = ProviderMetrics(
                    provider=DataProvider.ETRADE,
                    daily_limit=0,  # Unlimited
                    calls_remaining=0
                )
            
            # Yahoo Finance provider (fallback)
            self.providers[DataProvider.YAHOO] = YFProvider()
            self.provider_metrics[DataProvider.YAHOO] = ProviderMetrics(
                provider=DataProvider.YAHOO,
                daily_limit=0,  # Unlimited
                calls_remaining=0
            )
            
            # Polygon provider (premium)
            polygon_key = os.getenv("POLYGON_API_KEY")
            if polygon_key:
                self.providers[DataProvider.POLYGON] = PolygonProvider(polygon_key)
                self.provider_metrics[DataProvider.POLYGON] = ProviderMetrics(
                    provider=DataProvider.POLYGON,
                    daily_limit=1000000,  # 1M calls/month
                    calls_remaining=1000000
                )
            
            # Initialize circuit breakers
            for provider in self.providers:
                self.circuit_breakers[provider] = True
                self.failure_counts[provider] = 0
                self.last_failure[provider] = datetime.min
            
            log.info(f"Initialized {len(self.providers)} data providers")
            
        except Exception as e:
            log.error(f"Error initializing providers: {e}")
    
    # ========================================================================
    # CORE DATA METHODS
    # ========================================================================
    
    async def get_market_data(self, request: DataRequest) -> DataResponse:
        """Get market data with intelligent fallback"""
        try:
            start_time = time.time()
            
            # Check cache first
            if self.cache_enabled:
                cached_data = self._get_from_cache(request)
                if cached_data:
                    self.cache_hits += 1
                    self.cache_metrics.hits += 1
                    return DataResponse(
                        data=cached_data,
                        provider_used=DataProvider.ETRADE,  # Assume ETRADE for cached data
                        quality=DataQuality.EXCELLENT,
                        cache_hit=True,
                        response_time=time.time() - start_time
                    )
            
            # Try providers in order of preference
            for provider in request.provider_preference:
                if provider not in self.providers:
                    continue
                
                if not self.circuit_breakers.get(provider, True):
                    continue
                
                try:
                    data = await self._fetch_from_provider(provider, request)
                    if data:
                        # Cache the result
                        if self.cache_enabled:
                            self._store_in_cache(request, data)
                        
                        # Update metrics
                        self._update_provider_metrics(provider, True, time.time() - start_time)
                        
                        return DataResponse(
                            data=data,
                            provider_used=provider,
                            quality=self._assess_data_quality(data),
                            cache_hit=False,
                            response_time=time.time() - start_time
                        )
                
                except Exception as e:
                    log.warning(f"Provider {provider.value} failed: {e}")
                    self._update_provider_metrics(provider, False, time.time() - start_time)
                    self._handle_provider_failure(provider)
                    continue
            
            # All providers failed
            self.cache_misses += 1
            self.cache_metrics.misses += 1
            
            return DataResponse(
                data=None,
                provider_used=DataProvider.YAHOO,
                quality=DataQuality.POOR,
                cache_hit=False,
                response_time=time.time() - start_time,
                error="All providers failed"
            )
            
        except Exception as e:
            log.error(f"Error getting market data: {e}")
            return DataResponse(
                data=None,
                provider_used=DataProvider.YAHOO,
                quality=DataQuality.POOR,
                cache_hit=False,
                response_time=0.0,
                error=str(e)
            )
    
    async def get_strategy_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive market data for strategy analysis
        
        This method provides all the data that strategies need:
        - Price arrays (prices, volumes, closes, highs, lows, opens)
        - Technical indicators (RSI, MACD, SMA, EMA, Bollinger Bands, ATR)
        - Volume analysis (volume ratio, OBV, AD Line)
        - Pattern recognition (doji, hammer, etc.)
        - Real-time data from E*TRADE
        """
        try:
            # Use E*TRADE for strategy data if available
            if DataProvider.ETRADE in self.providers and self.circuit_breakers[DataProvider.ETRADE]:
                etrade_provider = self.providers[DataProvider.ETRADE]
                if hasattr(etrade_provider, 'etrade_trader') and etrade_provider.etrade_trader:
                    market_data = etrade_provider.etrade_trader.get_market_data_for_strategy(symbol)
                    if market_data:
                        log.debug(f"📊 Retrieved comprehensive market data for {symbol} from E*TRADE")
                        return market_data
            
            # Fallback to basic data structure
            log.warning(f"⚠️ Using fallback data for {symbol} - E*TRADE not available")
            return self._get_basic_strategy_data(symbol)
            
        except Exception as e:
            log.error(f"Error getting strategy market data for {symbol}: {e}")
            return self._get_basic_strategy_data(symbol)
    
    def _get_basic_strategy_data(self, symbol: str) -> Dict[str, Any]:
        """Get basic strategy data as fallback"""
        try:
            return {
                'symbol': symbol,
                'current_price': 100.0,  # Placeholder
                'bid': 99.95,
                'ask': 100.05,
                'open': 99.50,
                'high': 100.50,
                'low': 99.00,
                'volume': 1000000,
                'change': 0.50,
                'change_pct': 0.5,
                'timestamp': datetime.utcnow().isoformat(),
                
                # Price arrays for technical analysis
                'prices': [99.50, 100.50, 99.00, 100.0],  # OHLC
                'volumes': [1000000],
                
                # Basic technical indicators
                'rsi': 50.0,
                'macd': 0.0,
                'sma_20': 100.0,
                'sma_50': 100.0,
                'sma_200': 100.0,
                'atr': 1.0,
                'bollinger_upper': 101.0,
                'bollinger_middle': 100.0,
                'bollinger_lower': 99.0,
                
                # Volume analysis
                'volume_ratio': 1.0,
                'volume_sma': 1000000,
                
                # Market data source
                'data_source': 'FALLBACK',
                'data_quality': 'placeholder'
            }
        except Exception as e:
            log.error(f"Error creating basic strategy data: {e}")
            return {}
    
    async def get_real_time_quote(self, symbol: str) -> DataResponse:
        """Get real-time quote with caching"""
        try:
            # Check quote cache first
            cache_key = f"quote:{symbol}"
            if cache_key in self.quote_cache:
                cached_quote = self.quote_cache[cache_key]
                return DataResponse(
                    data=cached_quote,
                    provider_used=DataProvider.ETRADE,
                    quality=DataQuality.EXCELLENT,
                    cache_hit=True,
                    response_time=0.0
                )
            
            # Try ETRADE first (real-time)
            if DataProvider.ETRADE in self.providers and self.circuit_breakers[DataProvider.ETRADE]:
                try:
                    quote = await self._get_etrade_quote(symbol)
                    if quote:
                        self.quote_cache[cache_key] = quote
                        return DataResponse(
                            data=quote,
                            provider_used=DataProvider.ETRADE,
                            quality=DataQuality.EXCELLENT,
                            cache_hit=False,
                            response_time=0.0
                        )
                except Exception as e:
                    log.warning(f"ETRADE quote failed: {e}")
            
            # Fallback to Yahoo
            if DataProvider.YAHOO in self.providers:
                try:
                    quote = await self._get_yahoo_quote(symbol)
                    if quote:
                        self.quote_cache[cache_key] = quote
                        return DataResponse(
                            data=quote,
                            provider_used=DataProvider.YAHOO,
                            quality=DataQuality.GOOD,
                            cache_hit=False,
                            response_time=0.0
                        )
                except Exception as e:
                    log.warning(f"Yahoo quote failed: {e}")
            
            return DataResponse(
                data=None,
                provider_used=DataProvider.YAHOO,
                quality=DataQuality.POOR,
                cache_hit=False,
                response_time=0.0,
                error="No quote available"
            )
            
        except Exception as e:
            log.error(f"Error getting real-time quote: {e}")
            return DataResponse(
                data=None,
                provider_used=DataProvider.YAHOO,
                quality=DataQuality.POOR,
                cache_hit=False,
                response_time=0.0,
                error=str(e)
            )
    
    async def get_historical_data(self, symbol: str, start_date: datetime, 
                                end_date: datetime, interval: str = "1min") -> DataResponse:
        """Get historical data with intelligent caching"""
        try:
            # Create request
            request = DataRequest(
                symbol=symbol,
                data_type=DataType.HISTORICAL,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                cache_ttl=3600  # 1 hour cache for historical data
            )
            
            return await self.get_market_data(request)
            
        except Exception as e:
            log.error(f"Error getting historical data: {e}")
            return DataResponse(
                data=None,
                provider_used=DataProvider.YAHOO,
                quality=DataQuality.POOR,
                cache_hit=False,
                response_time=0.0,
                error=str(e)
            )
    
    async def get_premarket_data(self, symbols: List[str]) -> Dict[str, DataResponse]:
        """Get premarket data for multiple symbols"""
        try:
            results = {}
            
            # Use Yahoo for premarket data (most reliable)
            if DataProvider.YAHOO in self.providers:
                for symbol in symbols:
                    try:
                        data = await self._get_yahoo_premarket(symbol)
                        results[symbol] = DataResponse(
                            data=data,
                            provider_used=DataProvider.YAHOO,
                            quality=DataQuality.GOOD,
                            cache_hit=False,
                            response_time=0.0
                        )
                    except Exception as e:
                        log.warning(f"Premarket data failed for {symbol}: {e}")
                        results[symbol] = DataResponse(
                            data=None,
                            provider_used=DataProvider.YAHOO,
                            quality=DataQuality.POOR,
                            cache_hit=False,
                            response_time=0.0,
                            error=str(e)
                        )
            
            return results
            
        except Exception as e:
            log.error(f"Error getting premarket data: {e}")
            return {}
    
    # ========================================================================
    # BATCH DATA PROCESSING
    # ========================================================================
    
    async def get_batch_quotes(self, symbols: List[str]) -> Dict[str, DataResponse]:
        """Get batch quotes for multiple symbols efficiently"""
        try:
            results = {}
            
            # Use E*TRADE for batch quotes if available
            if DataProvider.ETRADE in self.providers and self.circuit_breakers[DataProvider.ETRADE]:
                try:
                    batch_quotes = await self._get_etrade_batch_quotes(symbols)
                    for symbol, quote_data in batch_quotes.items():
                        if quote_data:
                            results[symbol] = DataResponse(
                                data=quote_data,
                                provider_used=DataProvider.ETRADE,
                                quality=DataQuality.EXCELLENT,
                                cache_hit=False,
                                response_time=0.0
                            )
                        else:
                            # Fallback to individual quote
                            results[symbol] = await self.get_real_time_quote(symbol)
                except Exception as e:
                    log.warning(f"ETRADE batch quotes failed: {e}")
                    # Fallback to individual quotes
                    for symbol in symbols:
                        results[symbol] = await self.get_real_time_quote(symbol)
            else:
                # Fallback to individual quotes
                for symbol in symbols:
                    results[symbol] = await self.get_real_time_quote(symbol)
            
            return results
            
        except Exception as e:
            log.error(f"Error getting batch quotes: {e}")
            return {}
    
    async def get_volume_profiles(self, symbols: List[str]) -> Dict[str, DataResponse]:
        """Get volume profiles for multiple symbols"""
        try:
            results = {}
            
            # Use E*TRADE for volume profiles if available
            if DataProvider.ETRADE in self.providers and self.circuit_breakers[DataProvider.ETRADE]:
                try:
                    volume_profiles = await self._get_etrade_volume_profiles(symbols)
                    for symbol, profile_data in volume_profiles.items():
                        if profile_data:
                            results[symbol] = DataResponse(
                                data=profile_data,
                                provider_used=DataProvider.ETRADE,
                                quality=DataQuality.EXCELLENT,
                                cache_hit=False,
                                response_time=0.0
                            )
                        else:
                            # Fallback to basic volume data
                            quote_response = await self.get_real_time_quote(symbol)
                            if quote_response.data:
                                results[symbol] = DataResponse(
                                    data={'volume': quote_response.data.volume, 'symbol': symbol},
                                    provider_used=quote_response.provider_used,
                                    quality=DataQuality.GOOD,
                                    cache_hit=False,
                                    response_time=0.0
                                )
                except Exception as e:
                    log.warning(f"ETRADE volume profiles failed: {e}")
                    # Fallback to basic volume data
                    for symbol in symbols:
                        quote_response = await self.get_real_time_quote(symbol)
                        if quote_response.data:
                            results[symbol] = DataResponse(
                                data={'volume': quote_response.data.volume, 'symbol': symbol},
                                provider_used=quote_response.provider_used,
                                quality=DataQuality.GOOD,
                                cache_hit=False,
                                response_time=0.0
                            )
            else:
                # Fallback to basic volume data
                for symbol in symbols:
                    quote_response = await self.get_real_time_quote(symbol)
                    if quote_response.data:
                        results[symbol] = DataResponse(
                            data={'volume': quote_response.data.volume, 'symbol': symbol},
                            provider_used=quote_response.provider_used,
                            quality=DataQuality.GOOD,
                            cache_hit=False,
                            response_time=0.0
                        )
            
            return results
            
        except Exception as e:
            log.error(f"Error getting volume profiles: {e}")
            return {}
    
    async def discover_symbols(self, criteria: Dict[str, Any]) -> List[str]:
        """Discover symbols based on criteria using E*TRADE"""
        try:
            discovered_symbols = []
            
            # Use E*TRADE for symbol discovery if available
            if DataProvider.ETRADE in self.providers and self.circuit_breakers[DataProvider.ETRADE]:
                try:
                    discovered_symbols = await self._discover_etrade_symbols(criteria)
                except Exception as e:
                    log.warning(f"ETRADE symbol discovery failed: {e}")
                    # Fallback to basic symbol list
                    discovered_symbols = self._get_basic_symbol_list(criteria)
            else:
                # Fallback to basic symbol list
                discovered_symbols = self._get_basic_symbol_list(criteria)
            
            return discovered_symbols
            
        except Exception as e:
            log.error(f"Error discovering symbols: {e}")
            return []
    
    async def update_position_data(self, symbols: List[str]) -> Dict[str, DataResponse]:
        """Update data for all open positions"""
        try:
            results = {}
            
            # Get batch quotes for all position symbols
            quote_results = await self.get_batch_quotes(symbols)
            
            # Get volume profiles for all position symbols
            volume_results = await self.get_volume_profiles(symbols)
            
            # Combine data for each symbol
            for symbol in symbols:
                quote_data = quote_results.get(symbol)
                volume_data = volume_results.get(symbol)
                
                if quote_data and quote_data.data:
                    # Combine quote and volume data
                    combined_data = {
                        'symbol': symbol,
                        'price': quote_data.data.last if hasattr(quote_data.data, 'last') else quote_data.data.close,
                        'bid': quote_data.data.bid if hasattr(quote_data.data, 'bid') else 0,
                        'ask': quote_data.data.ask if hasattr(quote_data.data, 'ask') else 0,
                        'volume': quote_data.data.volume,
                        'timestamp': quote_data.data.timestamp,
                        'provider': quote_data.provider_used.value
                    }
                    
                    # Add volume profile data if available
                    if volume_data and volume_data.data:
                        combined_data.update(volume_data.data)
                    
                    results[symbol] = DataResponse(
                        data=combined_data,
                        provider_used=quote_data.provider_used,
                        quality=quote_data.quality,
                        cache_hit=False,
                        response_time=0.0
                    )
                else:
                    results[symbol] = DataResponse(
                        data=None,
                        provider_used=DataProvider.YAHOO,
                        quality=DataQuality.POOR,
                        cache_hit=False,
                        response_time=0.0,
                        error="No data available"
                    )
            
            return results
            
        except Exception as e:
            log.error(f"Error updating position data: {e}")
            return {}
    
    # ========================================================================
    # E*TRADE BATCH PROCESSING METHODS
    # ========================================================================
    
    async def _get_etrade_batch_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get batch quotes from E*TRADE API"""
        try:
            if not self.etrade_oauth or DataProvider.ETRADE not in self.providers:
                return {}
            
            # Use E*TRADE trader for batch quotes
            etrade_provider = self.providers[DataProvider.ETRADE]
            if hasattr(etrade_provider, 'etrade_trader') and etrade_provider.etrade_trader:
                quotes = etrade_provider.etrade_trader.get_quotes(symbols)
                
                # Convert to dictionary format
                batch_quotes = {}
                for quote in quotes:
                    batch_quotes[quote.symbol] = {
                        'symbol': quote.symbol,
                        'last': quote.last_price,
                        'bid': quote.bid,
                        'ask': quote.ask,
                        'open': quote.open,
                        'high': quote.high,
                        'low': quote.low,
                        'volume': quote.volume,
                        'change': quote.change,
                        'change_pct': quote.change_pct,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                
                return batch_quotes
            
            return {}
            
        except Exception as e:
            log.error(f"Error getting E*TRADE batch quotes: {e}")
            return {}
    
    async def _get_etrade_volume_profiles(self, symbols: List[str]) -> Dict[str, Any]:
        """Get volume profiles from E*TRADE API"""
        try:
            if not self.etrade_oauth or DataProvider.ETRADE not in self.providers:
                return {}
            
            # Use E*TRADE trader for volume profiles
            etrade_provider = self.providers[DataProvider.ETRADE]
            if hasattr(etrade_provider, 'etrade_trader') and etrade_provider.etrade_trader:
                quotes = etrade_provider.etrade_trader.get_quotes(symbols)
                
                # Convert to volume profile format
                volume_profiles = {}
                for quote in quotes:
                    volume_profiles[quote.symbol] = {
                        'symbol': quote.symbol,
                        'volume': quote.volume,
                        'avg_volume': quote.volume,  # Placeholder - would need historical data
                        'volume_ratio': 1.0,  # Placeholder
                        'timestamp': datetime.utcnow().isoformat()
                    }
                
                return volume_profiles
            
            return {}
            
        except Exception as e:
            log.error(f"Error getting E*TRADE volume profiles: {e}")
            return {}
    
    async def _discover_etrade_symbols(self, criteria: Dict[str, Any]) -> List[str]:
        """Discover symbols using E*TRADE API"""
        try:
            if not self.etrade_oauth or DataProvider.ETRADE not in self.providers:
                return []
            
            # Use E*TRADE trader for symbol discovery
            etrade_provider = self.providers[DataProvider.ETRADE]
            if hasattr(etrade_provider, 'etrade_trader') and etrade_provider.etrade_trader:
                # Get portfolio symbols as a starting point
                portfolio = etrade_provider.etrade_trader.get_portfolio()
                discovered_symbols = [pos.symbol for pos in portfolio if pos.symbol]
                
                # Add criteria-based filtering
                if 'min_volume' in criteria:
                    # Filter by volume (would need additional API calls)
                    pass
                
                return discovered_symbols
            
            return []
            
        except Exception as e:
            log.error(f"Error discovering E*TRADE symbols: {e}")
            return []
    
    def _get_basic_symbol_list(self, criteria: Dict[str, Any]) -> List[str]:
        """Get basic symbol list as fallback"""
        try:
            # Basic symbol list for fallback
            basic_symbols = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
                'SPY', 'QQQ', 'IWM', 'GLD', 'SLV', 'TLT', 'HYG', 'VTI'
            ]
            
            # Apply basic filtering
            if 'max_symbols' in criteria:
                basic_symbols = basic_symbols[:criteria['max_symbols']]
            
            return basic_symbols
            
        except Exception as e:
            log.error(f"Error getting basic symbol list: {e}")
            return []
    
    async def _get_yahoo_premarket(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get premarket data from Yahoo Finance (placeholder)"""
        try:
            # Placeholder implementation
            return {
                'symbol': symbol,
                'price': 100.0,  # Placeholder
                'volume': 1000000,  # Placeholder
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            log.error(f"Error getting Yahoo premarket data for {symbol}: {e}")
            return None
    
    # ========================================================================
    # PROVIDER METHODS
    # ========================================================================
    
    async def _fetch_from_provider(self, provider: DataProvider, request: DataRequest) -> Optional[Union[MarketData, List[MarketData]]]:
        """Fetch data from specific provider"""
        try:
            if provider == DataProvider.ETRADE:
                return await self._fetch_etrade_data(request)
            elif provider == DataProvider.YAHOO:
                return await self._fetch_yahoo_data(request)
            elif provider == DataProvider.POLYGON:
                return await self._fetch_polygon_data(request)
            else:
                return None
                
        except Exception as e:
            log.error(f"Error fetching from {provider.value}: {e}")
            return None
    
    async def _fetch_etrade_data(self, request: DataRequest) -> Optional[Union[MarketData, List[MarketData]]]:
        """Fetch data from ETRADE"""
        try:
            provider = self.providers[DataProvider.ETRADE]
            
            if request.data_type == DataType.REAL_TIME:
                quote = await provider.get_quote(request.symbol)
                if quote:
                    return MarketData(
                        symbol=request.symbol,
                        timestamp=datetime.utcnow(),
                        open=quote.get('open', 0),
                        high=quote.get('high', 0),
                        low=quote.get('low', 0),
                        close=quote.get('last', 0),
                        volume=quote.get('volume', 0),
                        provider=DataProvider.ETRADE,
                        quality=DataQuality.EXCELLENT,
                        data_type=DataType.REAL_TIME
                    )
            else:
                # Historical data
                data = await provider.get_historical_data(
                    request.symbol,
                    request.start_date,
                    request.end_date,
                    request.interval
                )
                if data:
                    return [MarketData(
                        symbol=request.symbol,
                        timestamp=row['timestamp'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume'],
                        provider=DataProvider.ETRADE,
                        quality=DataQuality.EXCELLENT,
                        data_type=DataType.HISTORICAL
                    ) for row in data]
            
            return None
            
        except Exception as e:
            log.error(f"Error fetching ETRADE data: {e}")
            return None
    
    async def _fetch_yahoo_data(self, request: DataRequest) -> Optional[Union[MarketData, List[MarketData]]]:
        """Fetch data from Yahoo Finance"""
        try:
            provider = self.providers[DataProvider.YAHOO]
            
            if request.data_type == DataType.REAL_TIME:
                quote = await provider.get_quote(request.symbol)
                if quote:
                    return MarketData(
                        symbol=request.symbol,
                        timestamp=datetime.utcnow(),
                        open=quote.get('open', 0),
                        high=quote.get('high', 0),
                        low=quote.get('low', 0),
                        close=quote.get('close', 0),
                        volume=quote.get('volume', 0),
                        provider=DataProvider.YAHOO,
                        quality=DataQuality.GOOD,
                        data_type=DataType.REAL_TIME
                    )
            else:
                # Historical data
                data = await provider.get_historical_data(
                    request.symbol,
                    request.start_date,
                    request.end_date,
                    request.interval
                )
                if data:
                    return [MarketData(
                        symbol=request.symbol,
                        timestamp=row['timestamp'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume'],
                        provider=DataProvider.YAHOO,
                        quality=DataQuality.GOOD,
                        data_type=DataType.HISTORICAL
                    ) for row in data]
            
            return None
            
        except Exception as e:
            log.error(f"Error fetching Yahoo data: {e}")
            return None
    
    async def _fetch_polygon_data(self, request: DataRequest) -> Optional[Union[MarketData, List[MarketData]]]:
        """Fetch data from Polygon"""
        try:
            provider = self.providers[DataProvider.POLYGON]
            
            if request.data_type == DataType.REAL_TIME:
                quote = await provider.get_quote(request.symbol)
                if quote:
                    return MarketData(
                        symbol=request.symbol,
                        timestamp=datetime.utcnow(),
                        open=quote.get('open', 0),
                        high=quote.get('high', 0),
                        low=quote.get('low', 0),
                        close=quote.get('close', 0),
                        volume=quote.get('volume', 0),
                        provider=DataProvider.POLYGON,
                        quality=DataQuality.EXCELLENT,
                        data_type=DataType.REAL_TIME
                    )
            else:
                # Historical data
                data = await provider.get_historical_data(
                    request.symbol,
                    request.start_date,
                    request.end_date,
                    request.interval
                )
                if data:
                    return [MarketData(
                        symbol=request.symbol,
                        timestamp=row['timestamp'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume'],
                        provider=DataProvider.POLYGON,
                        quality=DataQuality.EXCELLENT,
                        data_type=DataType.HISTORICAL
                    ) for row in data]
            
            return None
            
        except Exception as e:
            log.error(f"Error fetching Polygon data: {e}")
            return None
    
    # ========================================================================
    # CACHING SYSTEM
    # ========================================================================
    
    def _get_from_cache(self, request: DataRequest) -> Optional[Any]:
        """Get data from cache"""
        try:
            cache_key = self._generate_cache_key(request)
            
            if request.data_type == DataType.REAL_TIME:
                return self.quote_cache.get(cache_key)
            elif request.data_type == DataType.HISTORICAL:
                return self.historical_cache.get(cache_key)
            else:
                return self.cache.get(cache_key)
                
        except Exception as e:
            log.error(f"Error getting from cache: {e}")
            return None
    
    def _store_in_cache(self, request: DataRequest, data: Any):
        """Store data in cache"""
        try:
            cache_key = self._generate_cache_key(request)
            
            if request.data_type == DataType.REAL_TIME:
                self.quote_cache[cache_key] = data
            elif request.data_type == DataType.HISTORICAL:
                self.historical_cache[cache_key] = data
            else:
                self.cache[cache_key] = data
                
        except Exception as e:
            log.error(f"Error storing in cache: {e}")
    
    def _generate_cache_key(self, request: DataRequest) -> str:
        """Generate cache key for request"""
        try:
            key_parts = [
                request.symbol,
                request.data_type.value,
                request.interval,
                str(request.start_date) if request.start_date else "",
                str(request.end_date) if request.end_date else ""
            ]
            return hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
        except Exception as e:
            log.error(f"Error generating cache key: {e}")
            return f"{request.symbol}:{request.data_type.value}"
    
    # ========================================================================
    # QUALITY ASSESSMENT
    # ========================================================================
    
    def _assess_data_quality(self, data: Any) -> DataQuality:
        """Assess data quality"""
        try:
            if isinstance(data, MarketData):
                # Check for missing values
                if data.close <= 0 or data.volume < 0:
                    return DataQuality.POOR
                
                # Check for reasonable price range
                if data.high < data.low or data.close < data.low or data.close > data.high:
                    return DataQuality.POOR
                
                # Check for stale data
                age = (datetime.utcnow() - data.timestamp).total_seconds()
                if age > 300:  # 5 minutes
                    return DataQuality.FAIR
                
                return DataQuality.EXCELLENT
            
            elif isinstance(data, list) and len(data) > 0:
                # Check historical data quality
                valid_count = sum(1 for item in data if self._assess_data_quality(item) != DataQuality.POOR)
                quality_ratio = valid_count / len(data)
                
                if quality_ratio >= 0.95:
                    return DataQuality.EXCELLENT
                elif quality_ratio >= 0.80:
                    return DataQuality.GOOD
                elif quality_ratio >= 0.60:
                    return DataQuality.FAIR
                else:
                    return DataQuality.POOR
            
            return DataQuality.POOR
            
        except Exception as e:
            log.error(f"Error assessing data quality: {e}")
            return DataQuality.POOR
    
    # ========================================================================
    # METRICS AND MONITORING
    # ========================================================================
    
    def _update_provider_metrics(self, provider: DataProvider, success: bool, response_time: float):
        """Update provider metrics"""
        try:
            metrics = self.provider_metrics[provider]
            metrics.total_requests += 1
            
            if success:
                metrics.successful_requests += 1
                metrics.last_success = datetime.utcnow()
                
                # Update average response time
                if metrics.average_response_time == 0:
                    metrics.average_response_time = response_time
                else:
                    metrics.average_response_time = (metrics.average_response_time + response_time) / 2
            else:
                metrics.failed_requests += 1
                metrics.last_failure = datetime.utcnow()
            
            # Update daily calls
            metrics.daily_calls += 1
            if metrics.daily_limit > 0:
                metrics.calls_remaining = max(0, metrics.daily_limit - metrics.daily_calls)
            
        except Exception as e:
            log.error(f"Error updating provider metrics: {e}")
    
    def _handle_provider_failure(self, provider: DataProvider):
        """Handle provider failure"""
        try:
            self.failure_counts[provider] += 1
            self.last_failure[provider] = datetime.utcnow()
            
            # Circuit breaker logic
            if self.failure_counts[provider] >= 5:  # 5 consecutive failures
                self.circuit_breakers[provider] = False
                log.warning(f"Circuit breaker opened for {provider.value}")
                
                # Schedule circuit breaker reset
                asyncio.create_task(self._reset_circuit_breaker(provider))
            
        except Exception as e:
            log.error(f"Error handling provider failure: {e}")
    
    async def _reset_circuit_breaker(self, provider: DataProvider):
        """Reset circuit breaker after timeout"""
        try:
            await asyncio.sleep(300)  # 5 minutes
            self.circuit_breakers[provider] = True
            self.failure_counts[provider] = 0
            log.info(f"Circuit breaker reset for {provider.value}")
            
        except Exception as e:
            log.error(f"Error resetting circuit breaker: {e}")
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def get_provider_metrics(self) -> Dict[DataProvider, ProviderMetrics]:
        """Get provider performance metrics"""
        return self.provider_metrics.copy()
    
    def get_cache_metrics(self) -> CacheMetrics:
        """Get cache performance metrics"""
        self.cache_metrics.hit_rate = self.cache_hits / max(1, self.cache_hits + self.cache_misses)
        self.cache_metrics.size = len(self.cache)
        self.cache_metrics.max_size = self.cache.maxsize
        return self.cache_metrics
    
    def get_total_requests(self) -> int:
        """Get total requests made"""
        return self.total_requests
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / max(1, total)
    
    def clear_cache(self):
        """Clear all caches"""
        try:
            self.cache.clear()
            self.quote_cache.clear()
            self.historical_cache.clear()
            log.info("All caches cleared")
        except Exception as e:
            log.error(f"Error clearing cache: {e}")
    
    def set_cache_strategy(self, strategy: CacheStrategy):
        """Set cache strategy"""
        self.cache_strategy = strategy
        log.info(f"Cache strategy set to {strategy.value}")
    
    def enable_provider(self, provider: DataProvider):
        """Enable data provider"""
        self.circuit_breakers[provider] = True
        self.failure_counts[provider] = 0
        log.info(f"Provider {provider.value} enabled")
    
    def disable_provider(self, provider: DataProvider):
        """Disable data provider"""
        self.circuit_breakers[provider] = False
        log.info(f"Provider {provider.value} disabled")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            health = {
                "status": "healthy",
                "providers": {},
                "cache": {},
                "metrics": {}
            }
            
            # Check providers
            for provider, metrics in self.provider_metrics.items():
                health["providers"][provider.value] = {
                    "enabled": self.circuit_breakers[provider],
                    "success_rate": metrics.successful_requests / max(1, metrics.total_requests),
                    "average_response_time": metrics.average_response_time,
                    "daily_calls": metrics.daily_calls,
                    "calls_remaining": metrics.calls_remaining
                }
            
            # Check cache
            health["cache"] = {
                "hit_rate": self.get_cache_hit_rate(),
                "size": len(self.cache),
                "max_size": self.cache.maxsize
            }
            
            # Check overall health
            if any(not self.circuit_breakers[provider] for provider in self.providers):
                health["status"] = "degraded"
            
            return health
            
        except Exception as e:
            log.error(f"Error in health check: {e}")
            return {"status": "error", "error": str(e)}
    
    async def shutdown(self):
        """Shutdown the data manager"""
        try:
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            # Clear caches
            self.clear_cache()
            
            log.info("Unified Data Manager shutdown complete")
            
        except Exception as e:
            log.error(f"Error during shutdown: {e}")

# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def get_prime_data_manager(etrade_oauth: Optional[OAuthManager] = None) -> PrimeDataManager:
    """Get prime data manager instance"""
    return PrimeDataManager(etrade_oauth)

def create_data_manager(etrade_oauth: Optional[OAuthManager] = None) -> PrimeDataManager:
    """Create new data manager instance"""
    return PrimeDataManager(etrade_oauth)

log.info("Prime Data Manager loaded successfully")
