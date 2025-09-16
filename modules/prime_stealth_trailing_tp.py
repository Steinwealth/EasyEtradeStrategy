#!/usr/bin/env python3
"""
Prime Stealth Trailing Stop & Take Profit System
===============================================

Advanced stealth trailing stop and take profit management system for the Easy ETrade Strategy.
This module provides sophisticated position management with hidden stops, breakeven protection,
and dynamic trailing mechanisms to maximize profits while minimizing losses.

Key Features:
- Stealth trailing stops that adapt to market conditions
- Breakeven protection at +0.5% as requested
- Dynamic take profit targets based on volatility
- Hidden stop management (not visible to market)
- Multi-timeframe trailing logic
- Volume-based trailing adjustments
- Momentum-based trailing activation
- Risk-reward optimization
- Integration with existing Prime Trading Manager

Author: Easy ETrade Strategy Team
Version: 1.0.0
"""

import asyncio
import logging
import time
import math
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict, deque

try:
    from .prime_models import (
        StrategyMode, SignalType, SignalSide, TradeStatus, StopType, TrailingMode,
        MarketRegime, SignalQuality, ConfidenceTier, PrimePosition, PrimeTrade,
        determine_confidence_tier
    )
    from .config_loader import get_config_value
except ImportError:
    from prime_models import (
        StrategyMode, SignalType, SignalSide, TradeStatus, StopType, TrailingMode,
        MarketRegime, SignalQuality, ConfidenceTier, PrimePosition, PrimeTrade,
        determine_confidence_tier
    )
    from config_loader import get_config_value

log = logging.getLogger("prime_stealth_trailing")

# ============================================================================
# ENUMS
# ============================================================================

class StealthMode(Enum):
    """Stealth trailing stop modes"""
    INACTIVE = "inactive"
    BREAKEVEN = "breakeven"
    TRAILING = "trailing"
    EXPLOSIVE = "explosive"
    MOON = "moon"

class TrailingTrigger(Enum):
    """Trailing stop activation triggers"""
    PRICE_BREAKEVEN = "price_breakeven"
    PRICE_PERCENTAGE = "price_percentage"
    VOLUME_SURGE = "volume_surge"
    MOMENTUM_BREAKOUT = "momentum_breakout"
    TIME_BASED = "time_based"

class ExitReason(Enum):
    """Exit reasons for position closure"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"
    BREAKEVEN_PROTECTION = "breakeven_protection"
    TIME_EXIT = "time_exit"
    VOLUME_EXIT = "volume_exit"
    MOMENTUM_EXIT = "momentum_exit"

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class StealthConfig:
    """Stealth trailing stop configuration"""
    # Breakeven protection (OPTIMIZED FOR DEPLOYMENT)
    breakeven_threshold_pct: float = 0.005  # 0.5% activation threshold for faster protection
    breakeven_offset_pct: float = 0.002     # 0.2% offset above breakeven for better protection
    
    # Trailing stop parameters (OPTIMIZED FOR BETTER PROFIT CAPTURE)
    base_trailing_pct: float = 0.006        # 0.6% base trailing distance for more aggressive profit capture
    min_trailing_pct: float = 0.002         # 0.2% minimum trailing for tighter control
    max_trailing_pct: float = 0.04          # 4% maximum trailing for better risk management
    
    # Volume-based protection (ENHANCED SENSITIVITY FOR SELLING SURGES)
    selling_volume_surge_threshold: float = 1.4  # 1.4x average volume for more sensitive selling detection
    volume_stop_tightening_pct: float = 0.8      # 80% stop tightening for better protection
    buyers_volume_surge_threshold: float = 1.3   # 1.3x average volume for buying surge detection
    volume_exit_threshold: float = 2.2           # 2.2x volume for immediate exit on selling surge
    
    # Dynamic adjustments
    volatility_multiplier: float = 1.5      # ATR-based adjustment
    volume_multiplier: float = 1.2          # Volume-based adjustment
    momentum_multiplier: float = 1.3        # Momentum-based adjustment
    
    # Take profit targets
    base_take_profit_pct: float = 0.02      # 2% base take profit
    explosive_take_profit_pct: float = 0.10 # 10% explosive moves
    moon_take_profit_pct: float = 0.25      # 25% moon moves
    
    # High confidence adjustments
    high_confidence_threshold: float = 0.95  # 95% confidence threshold
    ultra_confidence_threshold: float = 0.99 # 99% confidence threshold
    high_confidence_take_profit_multiplier: float = 1.5  # 1.5x take profit for high confidence
    ultra_confidence_take_profit_multiplier: float = 2.0  # 2.0x take profit for ultra confidence
    high_confidence_moon_threshold: float = 0.15  # 15% for moon mode with high confidence
    ultra_confidence_moon_threshold: float = 0.10  # 10% for moon mode with ultra confidence
    
    # Time-based exits
    max_holding_hours: float = 4.0          # 4 hours max holding
    momentum_timeout_minutes: float = 30.0  # 30 min momentum timeout
    
    # Volume thresholds
    volume_surge_threshold: float = 2.0     # 2x average volume
    volume_exit_threshold: float = 0.5      # 0.5x average volume

@dataclass
class PositionState:
    """Current state of a position for stealth management"""
    symbol: str
    entry_price: float
    current_price: float
    quantity: int
    entry_time: datetime
    last_update: datetime
    highest_price: float
    lowest_price: float
    initial_stop_loss: float
    current_stop_loss: float
    take_profit: float
    
    # Optional fields with defaults
    breakeven_achieved: bool = False
    trailing_activated: bool = False
    breakeven_stop: Optional[float] = None
    stealth_mode: StealthMode = StealthMode.INACTIVE
    trailing_distance_pct: float = 0.0
    stealth_offset: float = 0.0
    atr: float = 0.0
    volume_ratio: float = 1.0
    momentum: float = 0.0
    volatility: float = 0.0
    confidence: float = 0.0
    quality_score: float = 0.0
    confidence_tier: Optional[ConfidenceTier] = None
    max_favorable: float = 0.0
    max_adverse: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0

@dataclass
class StealthDecision:
    """Decision from stealth trailing system"""
    action: str  # "HOLD", "TRAIL", "EXIT", "BREAKEVEN"
    new_stop_loss: Optional[float] = None
    new_take_profit: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    stealth_mode: Optional[StealthMode] = None
    reasoning: str = ""
    confidence: float = 1.0

@dataclass
class StealthMetrics:
    """Performance metrics for stealth system"""
    total_positions: int = 0
    breakeven_protected: int = 0
    trailing_activated: int = 0
    explosive_captured: int = 0
    moon_captured: int = 0
    
    # Exit analysis
    stop_loss_exits: int = 0
    take_profit_exits: int = 0
    trailing_exits: int = 0
    breakeven_exits: int = 0
    
    # Performance
    total_pnl: float = 0.0
    avg_pnl_per_trade: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    
    # Stealth effectiveness
    stealth_effectiveness: float = 0.0
    profit_capture_efficiency: float = 0.0

# ============================================================================
# PRIME STEALTH TRAILING SYSTEM
# ============================================================================

class PrimeStealthTrailingTP:
    """
    Prime Stealth Trailing Stop & Take Profit System
    
    Advanced position management with stealth trailing stops, breakeven protection,
    and dynamic take profit targets. Integrates seamlessly with the existing
    Prime Trading Manager and Prime Risk Manager.
    """
    
    def __init__(self, strategy_mode: StrategyMode = StrategyMode.STANDARD):
        self.strategy_mode = strategy_mode
        self.config = self._load_stealth_config()
        
        # Position tracking
        self.active_positions: Dict[str, PositionState] = {}
        self.position_history: deque = deque(maxlen=1000)
        self.stealth_metrics = StealthMetrics()
        
        # Market data cache
        self.market_data_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 60  # 60 seconds
        
        # Performance tracking
        self.daily_stats = {
            'positions_managed': 0,
            'breakeven_activations': 0,
            'trailing_activations': 0,
            'exits_triggered': 0,
            'total_pnl': 0.0
        }
        
        log.info(f"PrimeStealthTrailingTP initialized for {strategy_mode.value} strategy")
    
    def _load_stealth_config(self) -> StealthConfig:
        """Load stealth configuration from settings"""
        return StealthConfig(
            breakeven_threshold_pct=get_config_value("STEALTH_BREAKEVEN_THRESHOLD", 0.005),
            breakeven_offset_pct=get_config_value("STEALTH_BREAKEVEN_OFFSET", 0.001),
            base_trailing_pct=get_config_value("STEALTH_BASE_TRAILING", 0.01),
            min_trailing_pct=get_config_value("STEALTH_MIN_TRAILING", 0.005),
            max_trailing_pct=get_config_value("STEALTH_MAX_TRAILING", 0.05),
            volatility_multiplier=get_config_value("STEALTH_VOLATILITY_MULTIPLIER", 1.5),
            volume_multiplier=get_config_value("STEALTH_VOLUME_MULTIPLIER", 1.2),
            momentum_multiplier=get_config_value("STEALTH_MOMENTUM_MULTIPLIER", 1.3),
            base_take_profit_pct=get_config_value("STEALTH_BASE_TAKE_PROFIT", 0.02),
            explosive_take_profit_pct=get_config_value("STEALTH_EXPLOSIVE_TAKE_PROFIT", 0.10),
            moon_take_profit_pct=get_config_value("STEALTH_MOON_TAKE_PROFIT", 0.25),
            high_confidence_threshold=get_config_value("STEALTH_HIGH_CONFIDENCE_THRESHOLD", 0.95),
            ultra_confidence_threshold=get_config_value("STEALTH_ULTRA_CONFIDENCE_THRESHOLD", 0.99),
            high_confidence_take_profit_multiplier=get_config_value("STEALTH_HIGH_CONFIDENCE_TP_MULTIPLIER", 1.5),
            ultra_confidence_take_profit_multiplier=get_config_value("STEALTH_ULTRA_CONFIDENCE_TP_MULTIPLIER", 2.0),
            high_confidence_moon_threshold=get_config_value("STEALTH_HIGH_CONFIDENCE_MOON_THRESHOLD", 0.15),
            ultra_confidence_moon_threshold=get_config_value("STEALTH_ULTRA_CONFIDENCE_MOON_THRESHOLD", 0.10),
            max_holding_hours=get_config_value("STEALTH_MAX_HOLDING_HOURS", 4.0),
            momentum_timeout_minutes=get_config_value("STEALTH_MOMENTUM_TIMEOUT", 30.0),
            volume_surge_threshold=get_config_value("STEALTH_VOLUME_SURGE_THRESHOLD", 2.0),
            volume_exit_threshold=get_config_value("STEALTH_VOLUME_EXIT_THRESHOLD", 0.5)
        )
    
    async def add_position(self, position: PrimePosition, market_data: Dict[str, Any]) -> bool:
        """
        Add a new position to stealth management
        
        Args:
            position: PrimePosition to manage
            market_data: Current market data for the symbol
            
        Returns:
            bool: True if successfully added, False otherwise
        """
        try:
            symbol = position.symbol
            
            # Check if position already exists
            if symbol in self.active_positions:
                log.warning(f"Position {symbol} already being managed")
                return False
            
            # Get current market data
            current_price = market_data.get('price', position.entry_price)
            atr = market_data.get('atr', 0.0)
            volume_ratio = market_data.get('volume_ratio', 1.0)
            confidence = getattr(position, 'confidence', 0.0)
            quality_score = getattr(position, 'quality_score', 0.0)
            
            # Determine confidence tier
            confidence_tier = determine_confidence_tier(confidence)
            
            # Create position state
            position_state = PositionState(
                symbol=symbol,
                entry_price=position.entry_price,
                current_price=current_price,
                quantity=position.quantity,
                entry_time=position.entry_time,
                last_update=datetime.utcnow(),
                highest_price=current_price,
                lowest_price=current_price,
                initial_stop_loss=position.stop_loss or (current_price * 0.95),  # 5% default
                current_stop_loss=position.stop_loss or (current_price * 0.95),
                take_profit=position.take_profit or (current_price * 1.10),  # 10% default
                atr=atr,
                volume_ratio=volume_ratio,
                momentum=0.0,
                volatility=atr / current_price if current_price > 0 else 0.0,
                confidence=confidence,
                quality_score=quality_score,
                confidence_tier=confidence_tier
            )
            
            # Store position
            self.active_positions[symbol] = position_state
            self.stealth_metrics.total_positions += 1
            self.daily_stats['positions_managed'] += 1
            
            log.info(f"Added position {symbol} to stealth management: "
                    f"Entry=${position.entry_price:.2f}, "
                    f"Stop=${position_state.current_stop_loss:.2f}, "
                    f"Target=${position_state.take_profit:.2f}")
            
            return True
            
        except Exception as e:
            log.error(f"Failed to add position {position.symbol} to stealth management: {e}")
            return False
    
    async def update_position(self, symbol: str, market_data: Dict[str, Any]) -> Optional[StealthDecision]:
        """
        Update position with new market data and return stealth decision
        
        Args:
            symbol: Symbol to update
            market_data: Current market data
            
        Returns:
            StealthDecision: Decision for position management
        """
        try:
            if symbol not in self.active_positions:
                return None
            
            position_state = self.active_positions[symbol]
            
            # Update market data
            current_price = market_data.get('price', position_state.current_price)
            atr = market_data.get('atr', position_state.atr)
            volume_ratio = market_data.get('volume_ratio', position_state.volume_ratio)
            momentum = market_data.get('momentum', 0.0)
            
            # Update position state
            position_state.current_price = current_price
            position_state.atr = atr
            position_state.volume_ratio = volume_ratio
            position_state.momentum = momentum
            position_state.last_update = datetime.utcnow()
            
            # Update price tracking
            if current_price > position_state.highest_price:
                position_state.highest_price = current_price
            if current_price < position_state.lowest_price:
                position_state.lowest_price = current_price
            
            # Calculate PnL
            position_state.unrealized_pnl = (current_price - position_state.entry_price) * position_state.quantity
            position_state.unrealized_pnl_pct = (current_price - position_state.entry_price) / position_state.entry_price
            
            # Update max favorable/adverse
            if position_state.unrealized_pnl > position_state.max_favorable:
                position_state.max_favorable = position_state.unrealized_pnl
            if position_state.unrealized_pnl < position_state.max_adverse:
                position_state.max_adverse = position_state.unrealized_pnl
            
            # Make stealth decision
            decision = await self._make_stealth_decision(position_state, market_data)
            
            # Apply decision
            if decision.action == "TRAIL" and decision.new_stop_loss:
                position_state.current_stop_loss = decision.new_stop_loss
                position_state.trailing_activated = True
                position_state.stealth_mode = decision.stealth_mode or StealthMode.TRAILING
                
            elif decision.action == "BREAKEVEN" and decision.new_stop_loss:
                position_state.breakeven_stop = decision.new_stop_loss
                position_state.current_stop_loss = decision.new_stop_loss
                position_state.breakeven_achieved = True
                position_state.stealth_mode = StealthMode.BREAKEVEN
                
            elif decision.action == "EXIT":
                # Position should be closed
                await self._remove_position(symbol, decision.exit_reason)
            
            return decision
            
        except Exception as e:
            log.error(f"Failed to update position {symbol}: {e}")
            return None
    
    async def _make_stealth_decision(self, position: PositionState, market_data: Dict[str, Any]) -> StealthDecision:
        """
        Make stealth trailing decision for position
        
        This is the core logic that implements the stealth trailing system
        with breakeven protection at +0.5% as requested.
        """
        try:
            current_price = position.current_price
            entry_price = position.entry_price
            pnl_pct = position.unrealized_pnl_pct
            
            # 1. Check for immediate exit conditions
            exit_check = self._check_exit_conditions(position, market_data)
            if exit_check:
                return exit_check
            
            # 2. Check for volume-based protection FIRST (selling volume surges)
            volume_protection = self._apply_volume_protection(position, market_data)
            if volume_protection:
                return volume_protection
            
            # 3. Check for breakeven protection activation (+0.5%)
            if not position.breakeven_achieved and pnl_pct >= self.config.breakeven_threshold_pct:
                return self._activate_breakeven_protection(position)
            
            # 4. Check for trailing stop activation
            if position.breakeven_achieved and not position.trailing_activated:
                trailing_check = self._check_trailing_activation(position, market_data)
                if trailing_check:
                    return trailing_check
            
            # 5. Update existing trailing stop
            if position.trailing_activated:
                return self._update_trailing_stop(position, market_data)
            
            # 6. Check for take profit updates
            take_profit_check = self._check_take_profit_update(position, market_data)
            if take_profit_check:
                return take_profit_check
            
            # 6. Default: Hold position
            return StealthDecision(
                action="HOLD",
                reasoning=f"Position holding: PnL={pnl_pct:.2%}, Mode={position.stealth_mode.value}"
            )
            
        except Exception as e:
            log.error(f"Error making stealth decision for {position.symbol}: {e}")
            return StealthDecision(
                action="HOLD",
                reasoning=f"Error in decision making: {str(e)}"
            )
    
    def _check_exit_conditions(self, position: PositionState, market_data: Dict[str, Any]) -> Optional[StealthDecision]:
        """Check for immediate exit conditions including RSI-based exits"""
        
        # RSI-based exit for losing positions
        if 'rsi' in market_data:
            current_rsi = market_data['rsi']
            if current_rsi < 45 and position.unrealized_pnl_pct < 0:
                return StealthDecision(
                    action="EXIT",
                    reason="RSI below 45 with losing position",
                    new_stop_price=position.current_price,
                    stealth_mode=StealthMode.STOP_LOSS
                )
        """Check for immediate exit conditions"""
        current_price = position.current_price
        
        # Stop loss hit
        if current_price <= position.current_stop_loss:
            return StealthDecision(
                action="EXIT",
                exit_reason=ExitReason.STOP_LOSS,
                reasoning=f"Stop loss triggered: ${current_price:.2f} <= ${position.current_stop_loss:.2f}"
            )
        
        # Take profit hit
        if current_price >= position.take_profit:
            return StealthDecision(
                action="EXIT",
                exit_reason=ExitReason.TAKE_PROFIT,
                reasoning=f"Take profit triggered: ${current_price:.2f} >= ${position.take_profit:.2f}"
            )
        
        # Time-based exit
        holding_hours = (datetime.utcnow() - position.entry_time).total_seconds() / 3600
        if holding_hours >= self.config.max_holding_hours:
            return StealthDecision(
                action="EXIT",
                exit_reason=ExitReason.TIME_EXIT,
                reasoning=f"Maximum holding time reached: {holding_hours:.1f} hours"
            )
        
        # Volume-based exit (low volume)
        if position.volume_ratio < self.config.volume_exit_threshold:
            return StealthDecision(
                action="EXIT",
                exit_reason=ExitReason.VOLUME_EXIT,
                reasoning=f"Volume too low: {position.volume_ratio:.2f}x average"
            )
        
        return None
    
    def _check_volume_surge(self, position: PositionState, market_data: Dict[str, Any]) -> bool:
        """Check for volume surge and determine if it's buying or selling pressure (ENHANCED SENSITIVITY)"""
        volume_ratio = position.volume_ratio
        
        log.debug(f"Volume surge check for {position.symbol}: volume_ratio={volume_ratio:.2f}, threshold={self.config.selling_volume_surge_threshold}")
        
        # Enhanced sensitivity: Check for selling volume surge with lower threshold
        if volume_ratio >= self.config.selling_volume_surge_threshold:
            # Check if price is declining or if volume is extremely high (potential selling pressure)
            price_change = (position.current_price - position.highest_price) / position.highest_price
            log.debug(f"Volume surge check for {position.symbol}: volume_ratio={volume_ratio:.2f}, price_change={price_change:.4f}")
            
            # More sensitive detection: any high volume OR volume with any price decline OR extreme volume
            if (price_change < 0.002 or  # Any price decline (more sensitive)
                volume_ratio >= self.config.volume_exit_threshold or  # Extreme volume
                (volume_ratio >= 1.6 and price_change < 0.01)):  # Moderate volume with slight decline
                log.info(f"Selling volume surge detected for {position.symbol}: volume={volume_ratio:.2f}x, price_change={price_change:.2%}")
                return True
            else:
                log.debug(f"Volume surge but conditions not met: volume={volume_ratio:.2f}x, price_change={price_change:.2%}")
        
        # Additional check for immediate exit on extreme selling volume
        if volume_ratio >= self.config.volume_exit_threshold:
            log.info(f"Extreme selling volume detected for {position.symbol}: volume={volume_ratio:.2f}x (immediate exit threshold)")
            return True
        
        return False
    
    def _check_volume_exit(self, position: PositionState, market_data: Dict[str, Any]) -> Optional[StealthDecision]:
        """Check for volume-based exit conditions"""
        volume_ratio = position.volume_ratio
        
        # Low volume exit
        if volume_ratio < self.config.volume_exit_threshold:
            return StealthDecision(
                action="EXIT",
                exit_reason=ExitReason.VOLUME_EXIT,
                reasoning=f"Volume too low: {volume_ratio:.2f}x average"
            )
        
        return None
    
    def _apply_volume_protection(self, position: PositionState, market_data: Dict[str, Any]) -> Optional[StealthDecision]:
        """Apply volume-based protection by tightening stops during selling volume surges"""
        log.debug(f"Checking volume protection for {position.symbol}: volume_ratio={position.volume_ratio:.2f}")
        
        if not self._check_volume_surge(position, market_data):
            log.debug(f"No volume surge detected for {position.symbol}")
            return None
        
        # Calculate new stop with enhanced tightening (80% tightening for better protection)
        current_stop = position.current_stop_loss
        price_distance = position.current_price - current_stop
        tightened_distance = price_distance * self.config.volume_stop_tightening_pct
        new_stop = position.current_price - tightened_distance
        
        # Additional tightening for extreme volume surges
        if position.volume_ratio >= self.config.volume_exit_threshold:
            # Extra 20% tightening for extreme volume
            extra_tightening = tightened_distance * 0.2
            new_stop = position.current_price - (tightened_distance + extra_tightening)
            log.info(f"Extreme volume detected - applying extra 20% tightening for {position.symbol}")
        
        # Ensure stop doesn't go below breakeven
        breakeven_stop = position.entry_price * (1 + self.config.breakeven_offset_pct)
        new_stop = max(new_stop, breakeven_stop)
        
        log.debug(f"Volume protection calculation for {position.symbol}: "
                 f"current_stop=${current_stop:.2f}, new_stop=${new_stop:.2f}, "
                 f"price_distance=${price_distance:.2f}, tightened_distance=${tightened_distance:.2f}")
        
        # Only move stop if it's tighter (higher for long positions)
        if new_stop > current_stop:
            log.info(f"Volume protection activated for {position.symbol}: "
                    f"Stop tightened from ${current_stop:.2f} to ${new_stop:.2f} "
                    f"(50% tightening during selling volume surge)")
            
            return StealthDecision(
                action="TRAIL",
                new_stop_loss=new_stop,
                stealth_mode=StealthMode.TRAILING,
                reasoning=f"Volume protection: Stop tightened to ${new_stop:.2f} (50% tightening)"
            )
        else:
            log.debug(f"Volume protection not applied for {position.symbol}: new_stop (${new_stop:.2f}) not higher than current_stop (${current_stop:.2f})")
        
        return None
    
    def _activate_breakeven_protection(self, position: PositionState) -> StealthDecision:
        """Activate breakeven protection at +0.5% as requested"""
        entry_price = position.entry_price
        breakeven_stop = entry_price * (1 + self.config.breakeven_offset_pct)
        
        self.stealth_metrics.breakeven_protected += 1
        self.daily_stats['breakeven_activations'] += 1
        
        log.info(f"Breakeven protection activated for {position.symbol}: "
                f"Stop moved to ${breakeven_stop:.2f} (+{self.config.breakeven_offset_pct:.1%})")
        
        return StealthDecision(
            action="BREAKEVEN",
            new_stop_loss=breakeven_stop,
            stealth_mode=StealthMode.BREAKEVEN,
            reasoning=f"Breakeven protection: Stop moved to ${breakeven_stop:.2f} (+{self.config.breakeven_offset_pct:.1%})"
        )
    
    def _check_trailing_activation(self, position: PositionState, market_data: Dict[str, Any]) -> Optional[StealthDecision]:
        """Check if trailing stop should be activated (OPTIMIZED FOR BETTER PROFIT CAPTURE)"""
        pnl_pct = position.unrealized_pnl_pct
        
        # More aggressive trailing activation - activate earlier for better profit capture
        # Activate trailing when breakeven is achieved OR when profit exceeds 0.3%
        if (position.breakeven_achieved and pnl_pct > self.config.breakeven_threshold_pct) or pnl_pct > 0.003:
            return self._activate_trailing_stop(position, market_data)
        
        # Additional activation triggers for better profit capture
        # Activate on strong momentum moves (0.5%+ with positive momentum)
        if pnl_pct > 0.005 and position.momentum > 0.02:
            return self._activate_trailing_stop(position, market_data)
        
        # Activate on volume confirmation (0.4%+ with volume surge)
        if pnl_pct > 0.004 and position.volume_ratio > 1.5:
            return self._activate_trailing_stop(position, market_data)
        
        return None
    
    def _activate_trailing_stop(self, position: PositionState, market_data: Dict[str, Any]) -> StealthDecision:
        """Activate stealth trailing stop"""
        # Calculate dynamic trailing distance
        trailing_pct = self._calculate_trailing_distance(position, market_data)
        
        # Calculate new stop loss
        new_stop_loss = position.highest_price * (1 - trailing_pct)
        
        # Apply stealth offset (make stop less obvious)
        stealth_offset = position.highest_price * (trailing_pct * 0.1)  # 10% of trailing distance
        new_stop_loss -= stealth_offset
        
        # Ensure stop is above breakeven
        breakeven_stop = position.entry_price * (1 + self.config.breakeven_offset_pct)
        new_stop_loss = max(new_stop_loss, breakeven_stop)
        
        self.stealth_metrics.trailing_activated += 1
        self.daily_stats['trailing_activations'] += 1
        
        log.info(f"Stealth trailing activated for {position.symbol}: "
                f"Stop=${new_stop_loss:.2f} (trailing {trailing_pct:.1%})")
        
        return StealthDecision(
            action="TRAIL",
            new_stop_loss=new_stop_loss,
            stealth_mode=StealthMode.TRAILING,
            reasoning=f"Stealth trailing activated: Stop=${new_stop_loss:.2f} (trailing {trailing_pct:.1%})"
        )
    
    def _update_trailing_stop(self, position: PositionState, market_data: Dict[str, Any]) -> StealthDecision:
        """Update existing trailing stop"""
        # Only update if price has moved favorably
        if position.current_price <= position.highest_price:
            return StealthDecision(
                action="HOLD",
                reasoning="Price not at new high, maintaining current stop"
            )
        
        # Calculate new trailing distance
        trailing_pct = self._calculate_trailing_distance(position, market_data)
        
        # Calculate new stop loss
        new_stop_loss = position.highest_price * (1 - trailing_pct)
        
        # Apply stealth offset
        stealth_offset = position.highest_price * (trailing_pct * 0.1)
        new_stop_loss -= stealth_offset
        
        # Ensure stop only moves up
        if new_stop_loss <= position.current_stop_loss:
            return StealthDecision(
                action="HOLD",
                reasoning="New stop not higher than current stop"
            )
        
        # Check for explosive/moon mode with confidence-based thresholds
        pnl_pct = position.unrealized_pnl_pct
        confidence = position.confidence
        
        # Get confidence-adjusted thresholds
        moon_threshold = self._get_confidence_adjusted_threshold(
            self.config.moon_take_profit_pct, 
            confidence, 
            "moon"
        )
        explosive_threshold = self._get_confidence_adjusted_threshold(
            self.config.explosive_take_profit_pct, 
            confidence, 
            "explosive"
        )
        
        if pnl_pct >= moon_threshold:
            position.stealth_mode = StealthMode.MOON
            self.stealth_metrics.moon_captured += 1
            log.info(f"Moon mode activated for {position.symbol} (confidence {confidence:.1%}): {pnl_pct:.1%} >= {moon_threshold:.1%}")
        elif pnl_pct >= explosive_threshold:
            position.stealth_mode = StealthMode.EXPLOSIVE
            self.stealth_metrics.explosive_captured += 1
            log.info(f"Explosive mode activated for {position.symbol} (confidence {confidence:.1%}): {pnl_pct:.1%} >= {explosive_threshold:.1%}")
        
        log.info(f"Stealth trailing updated for {position.symbol}: "
                f"Stop=${new_stop_loss:.2f} (trailing {trailing_pct:.1%})")
        
        return StealthDecision(
            action="TRAIL",
            new_stop_loss=new_stop_loss,
            stealth_mode=position.stealth_mode,
            reasoning=f"Stealth trailing updated: Stop=${new_stop_loss:.2f} (trailing {trailing_pct:.1%})"
        )
    
    def _calculate_trailing_distance(self, position: PositionState, market_data: Dict[str, Any]) -> float:
        """Calculate dynamic trailing distance based on market conditions"""
        # Base trailing distance
        base_trailing = self.config.base_trailing_pct
        
        # Volatility adjustment
        volatility_multiplier = 1.0
        if position.volatility > 0:
            volatility_multiplier = min(2.0, 1.0 + (position.volatility * self.config.volatility_multiplier))
        
        # Volume adjustment
        volume_multiplier = 1.0
        if position.volume_ratio > 1.0:
            volume_multiplier = min(1.5, 1.0 + ((position.volume_ratio - 1.0) * self.config.volume_multiplier))
        
        # Momentum adjustment
        momentum_multiplier = 1.0
        if position.momentum > 0:
            momentum_multiplier = min(1.3, 1.0 + (position.momentum * self.config.momentum_multiplier))
        
        # Calculate final trailing distance
        trailing_pct = base_trailing * volatility_multiplier * volume_multiplier * momentum_multiplier
        
        # Clamp to min/max bounds
        trailing_pct = max(self.config.min_trailing_pct, min(trailing_pct, self.config.max_trailing_pct))
        
        return trailing_pct
    
    def _check_take_profit_update(self, position: PositionState, market_data: Dict[str, Any]) -> Optional[StealthDecision]:
        """Check if take profit should be updated with confidence-based adjustments"""
        pnl_pct = position.unrealized_pnl_pct
        current_take_profit = position.take_profit
        confidence = position.confidence
        
        # Calculate confidence-based thresholds
        explosive_threshold = self._get_confidence_adjusted_threshold(
            self.config.explosive_take_profit_pct, 
            confidence, 
            "explosive"
        )
        moon_threshold = self._get_confidence_adjusted_threshold(
            self.config.moon_take_profit_pct, 
            confidence, 
            "moon"
        )
        
        # Update take profit for explosive moves (confidence-adjusted)
        if pnl_pct >= explosive_threshold:
            # Calculate confidence-based take profit multiplier
            multiplier = self._get_confidence_take_profit_multiplier(confidence)
            new_take_profit_pct = explosive_threshold * multiplier
            new_take_profit = position.entry_price * (1 + new_take_profit_pct)
            
            if new_take_profit > current_take_profit:
                return StealthDecision(
                    action="TRAIL",
                    new_take_profit=new_take_profit,
                    reasoning=f"Take profit updated for explosive move (confidence {confidence:.1%}): ${new_take_profit:.2f} ({new_take_profit_pct:.1%})"
                )
        
        # Update take profit for moon moves (confidence-adjusted)
        if pnl_pct >= moon_threshold:
            # Calculate confidence-based take profit multiplier
            multiplier = self._get_confidence_take_profit_multiplier(confidence)
            new_take_profit_pct = moon_threshold * multiplier
            new_take_profit = position.entry_price * (1 + new_take_profit_pct)
            
            if new_take_profit > current_take_profit:
                return StealthDecision(
                    action="TRAIL",
                    new_take_profit=new_take_profit,
                    reasoning=f"Take profit updated for moon move (confidence {confidence:.1%}): ${new_take_profit:.2f} ({new_take_profit_pct:.1%})"
                )
        
        return None
    
    def _get_confidence_adjusted_threshold(self, base_threshold: float, confidence: float, move_type: str) -> float:
        """Get confidence-adjusted threshold for explosive/moon moves"""
        if confidence >= self.config.ultra_confidence_threshold:
            if move_type == "moon":
                return self.config.ultra_confidence_moon_threshold
            else:
                return base_threshold * 0.8  # Lower threshold for ultra confidence
        elif confidence >= self.config.high_confidence_threshold:
            if move_type == "moon":
                return self.config.high_confidence_moon_threshold
            else:
                return base_threshold * 0.9  # Slightly lower threshold for high confidence
        else:
            return base_threshold
    
    def _get_confidence_take_profit_multiplier(self, confidence: float) -> float:
        """Get confidence-based take profit multiplier"""
        if confidence >= self.config.ultra_confidence_threshold:
            return self.config.ultra_confidence_take_profit_multiplier
        elif confidence >= self.config.high_confidence_threshold:
            return self.config.high_confidence_take_profit_multiplier
        else:
            return 1.0
    
    async def _remove_position(self, symbol: str, exit_reason: ExitReason):
        """Remove position from stealth management"""
        if symbol in self.active_positions:
            position = self.active_positions[symbol]
            
            # Update metrics
            self.stealth_metrics.total_pnl += position.unrealized_pnl
            self.daily_stats['exits_triggered'] += 1
            self.daily_stats['total_pnl'] += position.unrealized_pnl
            
            # Update exit reason metrics
            if exit_reason == ExitReason.STOP_LOSS:
                self.stealth_metrics.stop_loss_exits += 1
            elif exit_reason == ExitReason.TAKE_PROFIT:
                self.stealth_metrics.take_profit_exits += 1
            elif exit_reason == ExitReason.TRAILING_STOP:
                self.stealth_metrics.trailing_exits += 1
            elif exit_reason == ExitReason.BREAKEVEN_PROTECTION:
                self.stealth_metrics.breakeven_exits += 1
            
            # Add to history
            self.position_history.append(position)
            
            # Remove from active positions
            del self.active_positions[symbol]
            
            log.info(f"Removed position {symbol} from stealth management: "
                    f"Exit reason={exit_reason.value}, PnL=${position.unrealized_pnl:.2f}")
    
    def get_position_state(self, symbol: str) -> Optional[PositionState]:
        """Get current state of a position"""
        return self.active_positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, PositionState]:
        """Get all active positions"""
        return self.active_positions.copy()
    
    def get_stealth_metrics(self) -> StealthMetrics:
        """Get stealth system performance metrics"""
        # Calculate additional metrics
        if self.stealth_metrics.total_positions > 0:
            self.stealth_metrics.avg_pnl_per_trade = self.stealth_metrics.total_pnl / self.stealth_metrics.total_positions
            
            total_exits = (self.stealth_metrics.stop_loss_exits + 
                          self.stealth_metrics.take_profit_exits + 
                          self.stealth_metrics.trailing_exits + 
                          self.stealth_metrics.breakeven_exits)
            
            if total_exits > 0:
                winning_exits = (self.stealth_metrics.take_profit_exits + 
                               self.stealth_metrics.trailing_exits + 
                               self.stealth_metrics.breakeven_exits)
                self.stealth_metrics.win_rate = winning_exits / total_exits
        
        return self.stealth_metrics
    
    def get_daily_stats(self) -> Dict[str, Any]:
        """Get daily statistics"""
        return self.daily_stats.copy()
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at start of new trading day)"""
        self.daily_stats = {
            'positions_managed': 0,
            'breakeven_activations': 0,
            'trailing_activations': 0,
            'exits_triggered': 0,
            'total_pnl': 0.0
        }
        log.info("Daily stealth statistics reset")
    
    async def shutdown(self):
        """Shutdown stealth system"""
        # Close all remaining positions
        for symbol in list(self.active_positions.keys()):
            await self._remove_position(symbol, ExitReason.TIME_EXIT)
        
        log.info("PrimeStealthTrailingTP shutdown complete")

# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def get_prime_stealth_trailing(strategy_mode: StrategyMode = StrategyMode.STANDARD) -> PrimeStealthTrailingTP:
    """Get Prime Stealth Trailing instance"""
    return PrimeStealthTrailingTP(strategy_mode)

def create_stealth_trailing(strategy_mode: StrategyMode = StrategyMode.STANDARD) -> PrimeStealthTrailingTP:
    """Create new Prime Stealth Trailing instance"""
    return PrimeStealthTrailingTP(strategy_mode)

# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

async def integrate_with_trading_manager(trading_manager, stealth_system: PrimeStealthTrailingTP):
    """
    Integrate stealth system with Prime Trading Manager
    
    This function shows how to integrate the stealth system with the existing
    trading manager for seamless position management.
    """
    try:
        # Get all active positions from trading manager
        positions = trading_manager.get_positions()
        
        # Add each position to stealth management
        for symbol, position in positions.items():
            # Get current market data (this would come from your data manager)
            market_data = {
                'price': position.current_price,
                'atr': getattr(position, 'atr', 0.0),
                'volume_ratio': getattr(position, 'volume_ratio', 1.0),
                'momentum': getattr(position, 'momentum', 0.0)
            }
            
            # Add to stealth system
            await stealth_system.add_position(position, market_data)
        
        log.info(f"Integrated {len(positions)} positions with stealth system")
        
    except Exception as e:
        log.error(f"Failed to integrate with trading manager: {e}")

# ============================================================================
# TESTING
# ============================================================================

async def test_stealth_system():
    """Test the stealth trailing system"""
    try:
        print("🧪 Testing Prime Stealth Trailing System...")
        
        # Create stealth system
        stealth = PrimeStealthTrailingTP(StrategyMode.STANDARD)
        
        # Create mock position
        from .prime_models import PrimePosition
        position = PrimePosition(
            position_id="TEST_001",
            symbol="AAPL",
            side=SignalSide.BUY,
            quantity=100,
            entry_price=150.0,
            current_price=150.0,
            confidence=0.95,
            quality_score=0.95,
            strategy_mode=StrategyMode.STANDARD,
            reason="Test position"
        )
        
        # Add position
        market_data = {
            'price': 150.0,
            'atr': 2.0,
            'volume_ratio': 1.5,
            'momentum': 0.1
        }
        
        success = await stealth.add_position(position, market_data)
        print(f"✅ Position added: {success}")
        
        # Simulate price movement to trigger breakeven
        market_data['price'] = 150.75  # +0.5%
        decision = await stealth.update_position("AAPL", market_data)
        print(f"✅ Breakeven decision: {decision.action} - {decision.reasoning}")
        
        # Simulate further price movement to trigger trailing
        market_data['price'] = 152.0  # +1.33%
        decision = await stealth.update_position("AAPL", market_data)
        print(f"✅ Trailing decision: {decision.action} - {decision.reasoning}")
        
        # Get metrics
        metrics = stealth.get_stealth_metrics()
        print(f"✅ Metrics: {metrics.breakeven_protected} breakeven, {metrics.trailing_activated} trailing")
        
        print("🎯 Stealth system test completed successfully!")
        
    except Exception as e:
        print(f"❌ Stealth system test failed: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(test_stealth_system())
