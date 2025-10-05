# modules/__init__.py
"""
ETrade Strategy Modules Package
Provides all core modules for the ETrade Strategy trading system
"""

# Core modules that actually exist
from .config_loader import ConfigLoader, load_configuration, get_config_value

# Prime system modules
from .prime_data_manager import get_prime_data_manager, PrimeDataManager
from .prime_market_manager import get_prime_market_manager, PrimeMarketManager
from .prime_news_manager import get_prime_news_manager, PrimeNewsManager
from .prime_unified_trade_manager import get_prime_unified_trade_manager, PrimeUnifiedTradeManager
from .prime_models import (
    PrimeSignal, PrimePosition, PrimeTrade, PrimeStopOrder,
    StrategyMode, SignalQuality, SignalType, SignalSide, TradeStatus,
    StopType, TrailingMode, MarketRegime, ConfidenceTier
)

# Production signal generator - THE ONE AND ONLY
from .production_signal_generator import (
    get_enhanced_production_signal_generator, 
    EnhancedProductionSignalGenerator,
    SignalQuality, VolumeSurgeType, ProfitabilityLevel,
    MomentumType, VolumeProfileType, PatternType, StrategyMode
)

# OAuth keep-alive system handled by Cloud Scheduler (see ETradeOAuth/login/keepalive_oauth.py)

# Note: Live trading integration consolidated into prime_trading_manager

__all__ = [
    # Configuration
    'ConfigLoader', 'load_configuration', 'get_config_value',
    
    # Prime system modules
    'get_prime_data_manager', 'PrimeDataManager',
    'get_prime_market_manager', 'PrimeMarketManager',
    'get_prime_news_manager', 'PrimeNewsManager',
    'get_prime_unified_trade_manager', 'PrimeUnifiedTradeManager',
    
    # Prime models
    'PrimeSignal', 'PrimePosition', 'PrimeTrade', 'PrimeStopOrder',
    'StrategyMode', 'SignalQuality', 'SignalType', 'SignalSide', 'TradeStatus',
    'StopType', 'TrailingMode', 'MarketRegime', 'ConfidenceTier',
    
    # Production signal generator - THE ONE AND ONLY
    'get_enhanced_production_signal_generator', 'EnhancedProductionSignalGenerator',
    
    # Note: Live trading integration consolidated into prime_trading_manager
]

# Version information
__version__ = "2.0.0"
__author__ = "ETrade Strategy Team"
__description__ = "ETrade Strategy Trading System Modules"