# modules/unified_models.py

"""
Unified Data Models for ETrade Strategy
Consolidates all data structures from across the strategy system
Eliminates redundancy and provides single source of truth
"""

from __future__ import annotations
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
from collections import deque
import numpy as np

log = logging.getLogger("unified_models")

# ============================================================================
# ENUMS
# ============================================================================

class StrategyMode(Enum):
    """Strategy mode enumeration"""
    STANDARD = "standard"
    ADVANCED = "advanced"
    QUANTUM = "quantum"

class SignalType(Enum):
    """Signal type enumeration"""
    ENTRY = "entry"
    EXIT = "exit"

class SignalSide(Enum):
    """Signal side enumeration"""
    LONG = "long"
    SHORT = "short"

class TradeStatus(Enum):
    """Trade status enumeration"""
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    PENDING = "pending"

class StopType(Enum):
    """Stop type enumeration"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"
    BREAK_EVEN = "break_even"
    VOLUME_STOP = "volume_stop"
    TIME_STOP = "time_stop"

class TrailingMode(Enum):
    """Trailing stop modes"""
    BREAK_EVEN = "break_even"
    ATR_TRAILING = "atr_trailing"
    PERCENTAGE_TRAILING = "percentage_trailing"
    MOMENTUM_TRAILING = "momentum_trailing"
    EXPLOSIVE_TRAILING = "explosive_trailing"
    MOON_TRAILING = "moon_trailing"
    VOLUME_TRAILING = "volume_trailing"

class MarketRegime(Enum):
    """Market regime enumeration"""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"

class SignalQuality(Enum):
    """Signal quality enumeration"""
    ULTRA_HIGH = "ultra_high"     # 99%+ confidence
    VERY_HIGH = "very_high"       # 95-98% confidence
    HIGH = "high"                 # 90-94% confidence
    MEDIUM = "medium"             # 80-89% confidence
    LOW = "low"                   # 70-79% confidence

class ConfidenceTier(Enum):
    """Confidence tiers for position sizing"""
    ULTRA = "ultra"          # 99.5%+
    EXTREME = "extreme"      # 99.0-99.4%
    VERY_HIGH = "very_high"  # 97.5-98.9%
    HIGH = "high"           # 95.0-97.4%
    STANDARD = "standard"   # 90.0-94.9%

# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

@dataclass
class TechnicalIndicators:
    """Comprehensive technical indicators"""
    # Price data
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    # Moving averages
    sma_20: float = 0.0
    sma_50: float = 0.0
    sma_200: float = 0.0
    ema_12: float = 0.0
    ema_26: float = 0.0
    
    # Momentum
    rsi: float = 0.0
    rsi_14: float = 0.0
    rsi_21: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_histogram: float = 0.0
    stoch_k: float = 0.0
    stoch_d: float = 0.0
    
    # Volatility
    atr: float = 0.0
    bollinger_upper: float = 0.0
    bollinger_middle: float = 0.0
    bollinger_lower: float = 0.0
    bollinger_width: float = 0.0
    
    # Volume
    obv: float = 0.0
    ad_line: float = 0.0
    volume_sma: float = 0.0
    volume_ratio: float = 0.0
    
    # Patterns
    doji: bool = False
    hammer: bool = False
    engulfing: bool = False
    morning_star: bool = False

@dataclass
class PrimeSignal:
    """Unified signal data structure"""
    symbol: str
    signal_type: SignalType
    side: SignalSide
    confidence: float
    quality: SignalQuality
    price: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Technical data
    indicators: Optional[TechnicalIndicators] = None
    orb_score: float = 0.0
    volume_analysis: Optional[Dict[str, Any]] = None
    
    # Strategy data
    strategy_mode: StrategyMode = StrategyMode.STANDARD
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PrimePosition:
    """Unified position data structure"""
    # Core position data
    position_id: str
    symbol: str
    side: SignalSide
    quantity: int
    entry_price: float
    current_price: float
    entry_time: datetime = field(default_factory=datetime.utcnow)
    status: TradeStatus = TradeStatus.OPEN
    
    # PnL data
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    pnl_pct: float = 0.0
    max_favorable: float = 0.0
    max_adverse: float = 0.0
    
    # Risk management
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    stop_type: StopType = StopType.STOP_LOSS
    trailing_mode: TrailingMode = TrailingMode.BREAK_EVEN
    atr_multiplier: float = 1.8
    
    # Signal data
    confidence: float = 0.0
    quality_score: float = 0.0
    strategy_mode: StrategyMode = StrategyMode.STANDARD
    signal_reason: str = ""
    
    # Performance tracking
    holding_period: float = 0.0
    risk_taken: float = 0.0
    reward_achieved: float = 0.0
    risk_reward_ratio: float = 0.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PrimeTrade:
    """Unified trade execution record"""
    trade_id: str
    position_id: str
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: int
    price: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Execution details
    commission: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    order_id: str = ""
    client_order_id: str = ""
    execution_venue: str = "ETRADE"
    
    # Strategy data
    strategy_mode: StrategyMode = StrategyMode.STANDARD
    confidence: float = 0.0
    quality_score: float = 0.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PrimeStopOrder:
    """Unified stop order data structure"""
    stop_id: str
    position_id: str
    symbol: str
    stop_type: StopType
    stop_price: float
    trigger_price: float
    created_time: datetime = field(default_factory=datetime.utcnow)
    
    # Trailing data
    trailing_mode: Optional[TrailingMode] = None
    trailing_distance: float = 0.0
    max_trailing_distance: float = 0.0
    
    # Status
    is_active: bool = True
    triggered_time: Optional[datetime] = None
    cancelled_time: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# PERFORMANCE METRICS
# ============================================================================

@dataclass
class UnifiedPerformanceMetrics:
    """Unified performance metrics"""
    # Trade statistics
    total_trades: int = 0
    open_trades: int = 0
    closed_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # Performance ratios
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    recovery_factor: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    max_drawdown_duration: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    
    # Return metrics
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    
    # Trade analysis
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    avg_holding_period: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    expectancy: float = 0.0
    kelly_percentage: float = 0.0
    
    # Strategy-specific metrics
    standard_trades: int = 0
    advanced_trades: int = 0
    quantum_trades: int = 0
    standard_win_rate: float = 0.0
    advanced_win_rate: float = 0.0
    quantum_win_rate: float = 0.0

@dataclass
class UnifiedStrategyConfig:
    """Unified strategy configuration"""
    # Strategy mode
    mode: StrategyMode
    target_weekly_return: float
    base_risk_per_trade: float
    max_risk_per_trade: float
    position_size_pct: float
    confidence_threshold: float
    
    # Risk management
    max_open_positions: int = 5
    reserve_cash_pct: float = 20.0
    stop_loss_atr_multiplier: float = 1.8
    take_profit_atr_multiplier: float = 3.0
    
    # Signal requirements
    min_confirmations: int = 6
    min_quality_score: float = 60.0
    min_confidence_score: float = 0.9
    
    # Performance targets
    expected_daily_gain: float = 0.02
    expected_trade_gain_min: float = 0.005
    expected_trade_gain_max: float = 0.08
    expected_win_rate: float = 0.75

# ============================================================================
# STRATEGY CONFIGURATIONS
# ============================================================================

STRATEGY_CONFIGS = {
    StrategyMode.STANDARD: UnifiedStrategyConfig(
        mode=StrategyMode.STANDARD,
        target_weekly_return=0.12,  # 12% weekly
        base_risk_per_trade=0.02,   # 2% base risk
        max_risk_per_trade=0.05,    # 5% max risk
        position_size_pct=10.0,     # 10% position size
        confidence_threshold=0.90,  # 90% confidence
        min_confirmations=6,
        min_quality_score=60.0,
        expected_daily_gain=0.03,   # 3% daily
        expected_trade_gain_min=0.005,  # 0.5% min
        expected_trade_gain_max=0.08,   # 8% max
        expected_win_rate=0.75      # 75% win rate
    ),
    
    StrategyMode.ADVANCED: UnifiedStrategyConfig(
        mode=StrategyMode.ADVANCED,
        target_weekly_return=0.20,  # 20% weekly
        base_risk_per_trade=0.05,   # 5% base risk
        max_risk_per_trade=0.15,    # 15% max risk
        position_size_pct=20.0,     # 20% position size
        confidence_threshold=0.90,  # 90% confidence
        min_confirmations=8,
        min_quality_score=70.0,
        expected_daily_gain=0.04,   # 4% daily
        expected_trade_gain_min=0.01,   # 1% min
        expected_trade_gain_max=0.10,   # 10% max
        expected_win_rate=0.80      # 80% win rate
    ),
    
    StrategyMode.QUANTUM: UnifiedStrategyConfig(
        mode=StrategyMode.QUANTUM,
        target_weekly_return=0.35,  # 35% weekly
        base_risk_per_trade=0.10,   # 10% base risk
        max_risk_per_trade=0.25,    # 25% max risk
        position_size_pct=30.0,     # 30% position size
        confidence_threshold=0.95,  # 95% confidence
        min_confirmations=10,
        min_quality_score=80.0,
        expected_daily_gain=0.06,   # 6% daily
        expected_trade_gain_min=0.02,   # 2% min
        expected_trade_gain_max=0.15,   # 15% max
        expected_win_rate=0.85      # 85% win rate
    )
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_strategy_config(mode: StrategyMode) -> UnifiedStrategyConfig:
    """Get strategy configuration for given mode"""
    return STRATEGY_CONFIGS.get(mode, STRATEGY_CONFIGS[StrategyMode.STANDARD])

def create_position_id(symbol: str, timestamp: datetime = None) -> str:
    """Create unique position ID"""
    if timestamp is None:
        timestamp = datetime.utcnow()
    return f"{symbol}_{int(timestamp.timestamp())}"

def create_trade_id(symbol: str, side: str, timestamp: datetime = None) -> str:
    """Create unique trade ID"""
    if timestamp is None:
        timestamp = datetime.utcnow()
    return f"{symbol}_{side}_{int(timestamp.timestamp())}"

def create_stop_id(position_id: str, stop_type: StopType) -> str:
    """Create unique stop ID"""
    return f"{position_id}_{stop_type.value}_{int(time.time())}"

def calculate_pnl_percentage(entry_price: float, current_price: float, side: SignalSide) -> float:
    """Calculate PnL percentage"""
    if side == SignalSide.LONG:
        return (current_price - entry_price) / entry_price
    else:
        return (entry_price - current_price) / entry_price

def calculate_risk_reward_ratio(entry_price: float, stop_loss: float, take_profit: float, side: SignalSide) -> float:
    """Calculate risk-reward ratio"""
    if side == SignalSide.LONG:
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
    else:
        risk = stop_loss - entry_price
        reward = entry_price - take_profit
    
    if risk <= 0:
        return 0.0
    
    return reward / risk

def determine_signal_quality(confidence: float) -> SignalQuality:
    """Determine signal quality based on confidence"""
    if confidence >= 0.99:
        return SignalQuality.ULTRA_HIGH
    elif confidence >= 0.95:
        return SignalQuality.VERY_HIGH
    elif confidence >= 0.90:
        return SignalQuality.HIGH
    elif confidence >= 0.80:
        return SignalQuality.MEDIUM
    else:
        return SignalQuality.LOW

def determine_confidence_tier(confidence: float) -> ConfidenceTier:
    """Determine confidence tier based on confidence"""
    if confidence >= 0.995:
        return ConfidenceTier.ULTRA
    elif confidence >= 0.99:
        return ConfidenceTier.EXTREME
    elif confidence >= 0.975:
        return ConfidenceTier.VERY_HIGH
    elif confidence >= 0.95:
        return ConfidenceTier.HIGH
    else:
        return ConfidenceTier.STANDARD

# ============================================================================
# MEMORY EFFICIENT VERSIONS
# ============================================================================

class MemoryEfficientPosition:
    """Memory-efficient position using __slots__"""
    __slots__ = [
        'position_id', 'symbol', 'side', 'quantity', 'entry_price', 'current_price',
        'entry_time', 'status', 'unrealized_pnl', 'realized_pnl', 'pnl_pct',
        'stop_loss', 'take_profit', 'confidence', 'quality_score', 'strategy_mode'
    ]
    
    def __init__(self, position_id: str, symbol: str, side: SignalSide, quantity: int, 
                 entry_price: float, current_price: float = None):
        self.position_id = position_id
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.entry_price = entry_price
        self.current_price = current_price or entry_price
        self.entry_time = datetime.utcnow()
        self.status = TradeStatus.OPEN
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0
        self.pnl_pct = 0.0
        self.stop_loss = None
        self.take_profit = None
        self.confidence = 0.0
        self.quality_score = 0.0
        self.strategy_mode = StrategyMode.STANDARD

class MemoryEfficientSignal:
    """Memory-efficient signal using __slots__"""
    __slots__ = [
        'symbol', 'signal_type', 'side', 'confidence', 'quality', 'price', 'timestamp',
        'strategy_mode', 'reason'
    ]
    
    def __init__(self, symbol: str, signal_type: SignalType, side: SignalSide, 
                 confidence: float, price: float):
        self.symbol = symbol
        self.signal_type = signal_type
        self.side = side
        self.confidence = confidence
        self.quality = determine_signal_quality(confidence)
        self.price = price
        self.timestamp = datetime.utcnow()
        self.strategy_mode = StrategyMode.STANDARD
        self.reason = ""

log.info("Unified models loaded successfully")
