#!/usr/bin/env python3
"""
Prime Unified Trade Manager
==========================

Unified trade management system that integrates:
- Prime Trade Manager for position opening/closing
- Prime Stealth Trailing System for position management
- Risk management and position sizing
- Performance tracking and metrics
- Alert management and notifications

This provides a unified interface to coordinate between the focused
trade manager and stealth trailing system for comprehensive position management.
"""

import os
import asyncio
import logging
import time
import math
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from collections import deque, defaultdict
import numpy as np

try:
    from .prime_models import (
        StrategyMode, SignalType, SignalSide, TradeStatus, StopType, TrailingMode,
        MarketRegime, SignalQuality, ConfidenceTier, PrimePosition, PrimeTrade, PrimeSignal,
        determine_confidence_tier, get_strategy_config
    )
    from .config_loader import get_config_value
    from .prime_stealth_trailing_tp import PrimeStealthTrailingTP, StealthDecision, ExitReason
    from .prime_etrade_trading import PrimeETradeTrading
    from .prime_alert_manager import PrimeAlertManager, TradeAlert
    from .prime_market_manager import get_prime_market_manager, PrimeMarketManager
except ImportError:
    from prime_models import (
        StrategyMode, SignalType, SignalSide, TradeStatus, StopType, TrailingMode,
        MarketRegime, SignalQuality, ConfidenceTier, PrimePosition, PrimeTrade, PrimeSignal,
        determine_confidence_tier, get_strategy_config
    )
    from config_loader import get_config_value
    from prime_stealth_trailing_tp import PrimeStealthTrailingTP, StealthDecision, ExitReason
    from prime_etrade_trading import PrimeETradeTrading
    from prime_alert_manager import PrimeAlertManager, TradeAlert
    from prime_market_manager import get_prime_market_manager, PrimeMarketManager

log = logging.getLogger(__name__)

# ============================================================================
# ENUMS AND DATA STRUCTURES
# ============================================================================

class TradeAction(Enum):
    """Trade actions"""
    OPEN = "open"
    CLOSE = "close"
    HOLD = "hold"
    UPDATE = "update"

# ExitReason is imported from prime_stealth_trailing_tp to avoid duplication

@dataclass
class TradeConfig:
    """Trade management configuration optimized for maximum profitability"""
    # Position sizing (OPTIMIZED FOR HIGHER GAINS)
    max_position_size_pct: float = 0.15  # 15% of capital per position
    min_position_size: int = 1  # Minimum shares
    max_position_size: int = 2000  # Maximum shares
    
    # Risk management (OPTIMIZED FOR BETTER PROTECTION)
    max_drawdown_pct: float = 0.05  # 5% maximum drawdown
    circuit_breaker_threshold: float = 0.03  # 3% circuit breaker
    daily_loss_limit: float = 1000.0  # $1000 max daily loss
    
    # Signal validation (OPTIMIZED FOR HIGHER QUALITY)
    min_confidence: float = 0.3  # Minimum confidence for trades
    min_quality_score: float = 0.6  # Minimum quality score
    min_volume_ratio: float = 1.8  # Minimum volume ratio
    
    # RSI requirements (OPTIMIZED FOR BETTER ENTRIES)
    min_rsi: float = 60.0  # Minimum RSI for entry
    max_rsi: float = 80.0  # Maximum RSI for entry
    
    # Time-based exits (OPTIMIZED FOR LONGER HOLDING)
    max_holding_hours: float = 8.0  # Maximum holding time
    
    # Performance tracking
    performance_update_interval: int = 30  # Update every 30 seconds

@dataclass
class TradeResult:
    """Result of trade management decision"""
    action: TradeAction
    symbol: str
    quantity: Optional[int] = None
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    reasoning: str = ""
    confidence: float = 1.0
    stealth_decision: Optional[StealthDecision] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics for trade management"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    win_rate: float = 0.0
    avg_trade_pnl: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    active_positions: int = 0
    total_volume: float = 0.0
    avg_holding_time: float = 0.0
    
    # Stealth system metrics
    breakeven_protected: int = 0
    trailing_activated: int = 0
    explosive_captured: int = 0
    moon_captured: int = 0
    stealth_effectiveness: float = 0.0

# ============================================================================
# UNIFIED TRADE MANAGER
# ============================================================================

class PrimeUnifiedTradeManager:
    """
    Prime Unified Trade Manager
    
    Unified interface that coordinates between the focused trade manager
    and stealth trailing system for comprehensive position management.
    
    This provides a single entry point for all trading operations while
    maintaining separation of concerns between position opening/closing
    and stealth trailing management.
    """
    
    def __init__(self, strategy_mode: StrategyMode = StrategyMode.STANDARD):
        self.strategy_mode = strategy_mode
        self.config = self._load_trade_config()
        
        # Detect signal_only mode for simulated position tracking
        self.signal_only_mode = os.getenv('SYSTEM_MODE') == 'signal_only'
        log.info(f"🎯 Trade Manager Mode: {'SIGNAL-ONLY (Simulated Positions)' if self.signal_only_mode else 'LIVE TRADING'}")
        
        # Initialize market manager for holiday/weekend checking
        self.market_manager = get_prime_market_manager()
        
        # Initialize E*TRADE trading system
        self.etrade_trading = None
        self._initialize_etrade_trading()
        
        # Initialize stealth trailing system
        self.stealth_system = PrimeStealthTrailingTP(strategy_mode)
        
        # Integration status
        self.stealth_integration_active = True
        log.info("✅ Stealth trailing system integrated with unified trade manager")
        
        # Position tracking
        self.active_positions: Dict[str, PrimePosition] = {}
        self.position_history: deque = deque(maxlen=1000)
        self.trade_history: deque = deque(maxlen=1000)
        
        # Simulated position tracking for Demo Mode validation
        self.simulated_positions: Dict[str, PrimePosition] = {}
        self.simulated_performance = {
            'total_signals': 0,
            'open_positions': 0,
            'closed_positions': 0,
            'total_pnl': 0.0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'avg_return': 0.0,
            'trades': []
        }
        
        # Performance tracking
        self.performance_metrics = PerformanceMetrics()
        self.peak_capital = 10000.0
        self.current_capital = 10000.0
        
        # Risk management
        self.circuit_breaker_active = False
        self.daily_pnl = 0.0
        self.max_daily_loss = self.config.daily_loss_limit
        
        # Unified metrics
        self.unified_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'breakeven_protected': 0,
            'trailing_activated': 0,
            'explosive_captured': 0,
            'moon_captured': 0,
            'active_positions': 0,
            'win_rate': 0.0,
            'stealth_effectiveness': 0.0
        }
        
        # Performance tracking
        self.performance_history = deque(maxlen=1000)
        self.daily_stats = {
            'positions_opened': 0,
            'positions_closed': 0,
            'breakeven_activations': 0,
            'trailing_activations': 0,
            'exits_triggered': 0,
            'total_pnl': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'winning_trades': 0,
            'losing_trades': 0
        }
        
        # Trade history for end-of-day reports
        self.trade_history = []
        
        # Alert system
        self.alert_manager = None
        self.etrade_trading = None
        self._initialize_alert_manager()
        self._initialize_etrade_trading()
        
        log.info(f"🚀 Prime Unified Trade Manager initialized for {strategy_mode.value} strategy")
    
    def _load_trade_config(self) -> TradeConfig:
        """Load trade configuration optimized for maximum profitability"""
        return TradeConfig(
            max_position_size_pct=get_config_value("TRADE_MAX_POSITION_SIZE_PCT", 0.15),
            min_position_size=get_config_value("TRADE_MIN_POSITION_SIZE", 1),
            max_position_size=get_config_value("TRADE_MAX_POSITION_SIZE", 2000),
            max_drawdown_pct=get_config_value("TRADE_MAX_DRAWDOWN_PCT", 0.05),
            circuit_breaker_threshold=get_config_value("TRADE_CIRCUIT_BREAKER_THRESHOLD", 0.03),
            daily_loss_limit=get_config_value("TRADE_DAILY_LOSS_LIMIT", 1000.0),
            min_confidence=get_config_value("TRADE_MIN_CONFIDENCE", 0.3),
            min_quality_score=get_config_value("TRADE_MIN_QUALITY_SCORE", 0.6),
            min_volume_ratio=get_config_value("TRADE_MIN_VOLUME_RATIO", 1.8),
            min_rsi=get_config_value("TRADE_MIN_RSI", 60.0),
            max_rsi=get_config_value("TRADE_MAX_RSI", 80.0),
            max_holding_hours=get_config_value("TRADE_MAX_HOLDING_HOURS", 8.0),
            performance_update_interval=get_config_value("TRADE_PERFORMANCE_UPDATE_INTERVAL", 30)
        )
    
    def _initialize_alert_manager(self):
        """Initialize alert manager for notifications"""
        try:
            self.alert_manager = PrimeAlertManager()
            log.info("Alert manager initialized")
        except ImportError:
            log.warning("Alert manager not available")
            self.alert_manager = None
    
    def _initialize_etrade_trading(self):
        """Initialize E*TRADE trading integration with OAuth"""
        try:
            # Determine environment based on configuration
            etrade_mode = get_config_value('ETRADE_MODE', 'sandbox')
            
            # Initialize E*TRADE trading with environment
            self.etrade_trading = PrimeETradeTrading(environment=etrade_mode)
            
            # Initialize the trading system
            if self.etrade_trading.initialize():
                log.info("✅ E*TRADE trading system initialized successfully")
                
                # Get account summary for verification
                account_summary = self.etrade_trading.get_account_summary()
                if 'error' not in account_summary:
                    log.info(f"✅ E*TRADE account ready: {account_summary['account']['name']}")
                    log.info(f"   Cash available for investment: ${account_summary['balance']['cash_available_for_investment']}")
                    log.info(f"   Cash buying power: ${account_summary['balance']['cash_buying_power']}")
                else:
                    log.warning(f"⚠️ E*TRADE account issue: {account_summary['error']}")
            else:
                log.error("❌ Failed to initialize E*TRADE trading system")
                self.etrade_trading = None
                
        except Exception as e:
            log.error(f"❌ Error initializing E*TRADE trading: {e}")
            self.etrade_trading = None
    
    async def process_signal(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> TradeResult:
        """Process trading signal - simulated in signal_only mode, live otherwise"""
        # CRITICAL: Check market hours before processing any signals
        if not self.market_manager.is_market_open():
            log.warning(f"🚫 Market is closed, rejecting signal for {signal.symbol}")
            return TradeResult(
                action=TradeAction.HOLD, 
                symbol=signal.symbol, 
                reasoning="Market is closed - no trading outside market hours"
            )
        
        # Route to appropriate handler based on mode
        if self.signal_only_mode:
            return await self._process_simulated_signal(signal, market_data)
        else:
            return await self._process_live_signal(signal, market_data)
    
    async def _process_simulated_signal(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> TradeResult:
        """Process signal in SIMULATED mode for Demo validation (no real trades)"""
        try:
            log.info(f"🎯 SIGNAL-ONLY MODE: Processing simulated signal for {signal.symbol}")
            
            # Calculate position size (same logic as live trading)
            quantity, stop_loss, take_profit = await self._calculate_position_parameters(signal, market_data)
            
            if quantity == 0:
                log.warning(f"Position sizing returned 0 shares for {signal.symbol}")
                return TradeResult(action=TradeAction.HOLD, symbol=signal.symbol, reasoning="Position size too small")
            
            # Create simulated position
            position = PrimePosition(
                position_id=f"SIM_{signal.symbol}_{int(time.time())}",
                symbol=signal.symbol,
                side=SignalSide.LONG,
                quantity=quantity,
                entry_price=signal.price,
                current_price=signal.price,
                entry_time=datetime.utcnow(),
                status=TradeStatus.OPEN,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=signal.confidence,
                quality_score=signal.quality,
                strategy_mode=signal.strategy_mode,
                signal_reason=signal.reason,
                metadata={
                    'simulated': True,
                    'mode': 'signal_only',
                    'demo_validation': True,
                    'expected_return': signal.expected_return
                }
            )
            
            # Add to tracking
            self.active_positions[signal.symbol] = position
            self.simulated_positions[signal.symbol] = position
            self.simulated_performance['total_signals'] += 1
            self.simulated_performance['open_positions'] += 1
            
            # Add to stealth trailing system for exit monitoring
            await self.stealth_system.add_position(position, market_data)
            
            # Send SIMULATED entry alert via Telegram
            if self.alert_manager:
                try:
                    await self.alert_manager.send_buy_signal_alert(
                        symbol=signal.symbol,
                        company_name=f"{signal.symbol} ETF",
                        shares=quantity,
                        entry_price=signal.price,
                        total_value=signal.price * quantity,
                        confidence=signal.confidence,
                        expected_return=signal.expected_return,
                        quality_score=signal.quality,
                        strategies_agreeing=signal.reason,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        note="🎯 SIMULATED (Signal-Only Mode) - Position tracked for exit timing validation"
                    )
                    log.info(f"📱 Simulated entry alert sent for {signal.symbol}")
                except Exception as e:
                    log.error(f"Failed to send simulated entry alert: {e}")
            
            log.info(f"✅ Simulated position created and monitored: {signal.symbol}")
            log.info(f"   Entry: ${signal.price:.2f}, Shares: {quantity}, Value: ${signal.price * quantity:.2f}")
            log.info(f"   Stop: ${stop_loss:.2f}, Target: ${take_profit:.2f}")
            log.info(f"   🎯 Stealth trailing will monitor for optimal exit timing")
            
            return TradeResult(
                action=TradeAction.OPEN,
                symbol=signal.symbol,
                quantity=quantity,
                price=signal.price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasoning=f"SIMULATED position opened for validation with {signal.confidence:.1%} confidence"
            )
            
        except Exception as e:
            log.error(f"Failed to process simulated signal for {signal.symbol}: {e}")
            return TradeResult(action=TradeAction.HOLD, symbol=signal.symbol, reasoning=f"Simulated signal error: {str(e)}")
    
    async def _process_live_signal(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> TradeResult:
        """
        Process a trading signal through the unified system
        
        Args:
            signal: Trading signal to process
            market_data: Current market data for the symbol
            
        Returns:
            TradeResult with the recommended action
        """
        try:
            # Check if it's a trading day (weekends, US Bank holidays, Muslim holidays)
            if not self.market_manager.is_trading_day():
                return TradeResult(
                    action=TradeAction.HOLD,
                    symbol=signal.symbol,
                    reasoning="Not a trading day (weekend or holiday)"
                )
            
            # Check if market is open
            if not self.market_manager.is_market_open():
                return TradeResult(
                    action=TradeAction.HOLD,
                    symbol=signal.symbol,
                    reasoning="Market is closed"
                )
            
            # Validate signal
            if not self._validate_signal(signal, market_data):
                return TradeResult(
                    action=TradeAction.HOLD,
                    symbol=signal.symbol,
                    reasoning="Signal validation failed"
                )
            
            # Check if position already exists
            if signal.symbol in self.active_positions:
                return TradeResult(
                    action=TradeAction.HOLD,
                    symbol=signal.symbol,
                    reasoning="Position already exists"
                )
            
            # Check circuit breaker
            if self.circuit_breaker_active:
                return TradeResult(
                    action=TradeAction.HOLD,
                    symbol=signal.symbol,
                    reasoning="Circuit breaker active"
                )
            
            # Calculate position size
            quantity = await self._calculate_position_size(signal, market_data)
            if quantity <= 0:
                return TradeResult(
                    action=TradeAction.HOLD,
                    symbol=signal.symbol,
                    reasoning="Invalid position size calculated"
                )
            
            # Calculate stop loss and take profit
            stop_loss, take_profit = self._calculate_stop_and_target(signal, market_data)
            
            # Create position
            position = PrimePosition(
                position_id=f"{signal.symbol}_{int(time.time())}",
                symbol=signal.symbol,
                side=signal.side,
                quantity=quantity,
                entry_price=signal.price,
                current_price=signal.price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=signal.confidence,
                quality_score=signal.quality_score,
                strategy_mode=self.strategy_mode,
                reason=signal.reason,
                entry_time=datetime.utcnow()
            )
            
            # EXECUTE ACTUAL TRADE WITH E*TRADE OAuth
            if self.etrade_trading and self.etrade_trading.is_authenticated():
                try:
                    log.info(f"🚀 Executing E*TRADE order: {signal.symbol} {quantity} shares @ MARKET")
                    
                    # Place buy order with OAuth authentication
                    order_result = self.etrade_trading.place_order(
                        symbol=signal.symbol,
                        quantity=quantity,
                        side='BUY',
                        order_type='MARKET'
                    )
                    
                    if order_result and 'orderId' in order_result:
                        # Send trade entry alert
                        if self.alert_manager:
                            trade_alert = TradeAlert(
                                symbol=signal.symbol,
                                strategy=signal.strategy_mode.value,
                                action='BUY',
                                price=signal.price,
                                quantity=quantity,
                                confidence=signal.confidence,
                                expected_return=signal.expected_return,
                                stop_loss=stop_loss,
                                take_profit=take_profit,
                                reason=signal.reason
                            )
                            await self.alert_manager.send_trade_entry_alert(trade_alert)
                        
                        # Add to active positions
                        self.active_positions[signal.symbol] = position
                        
                        # Add to stealth system
                        await self.stealth_system.add_position(position, market_data)
                        
                        # Update metrics
                        self.performance_metrics.total_trades += 1
                        self.performance_metrics.active_positions = len(self.active_positions)
                        self.unified_metrics['total_trades'] += 1
                        self.unified_metrics['active_positions'] = len(self.active_positions)
                        self.daily_stats['positions_opened'] += 1
                        
                        log.info(f"✅ TRADE EXECUTED: {signal.symbol} @ ${signal.price:.2f} "
                                f"(Qty: {quantity}, Stop: ${stop_loss:.2f}, Target: ${take_profit:.2f})")
                        
                        return TradeResult(
                            action=TradeAction.OPEN,
                            symbol=signal.symbol,
                            quantity=quantity,
                            price=signal.price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            reasoning=f"Position opened with {signal.confidence:.1%} confidence"
                        )
                    else:
                        log.error(f"❌ Trade execution failed for {signal.symbol}")
                        return TradeResult(action=TradeAction.HOLD, symbol=signal.symbol, reasoning="Trade execution failed")
                        
                except Exception as e:
                    log.error(f"Trade execution error for {signal.symbol}: {e}")
                    return TradeResult(action=TradeAction.HOLD, symbol=signal.symbol, reasoning=f"Execution error: {str(e)}")
            else:
                # Fallback: create position without actual trade execution
                self.active_positions[signal.symbol] = position
                await self.stealth_system.add_position(position, market_data)
                
                # Update metrics
                self.performance_metrics.total_trades += 1
                self.performance_metrics.active_positions = len(self.active_positions)
                self.unified_metrics['total_trades'] += 1
                self.unified_metrics['active_positions'] = len(self.active_positions)
                self.daily_stats['positions_opened'] += 1
                
                log.warning(f"⚠️ Position created without ETrade execution: {signal.symbol}")
                
                return TradeResult(
                    action=TradeAction.OPEN,
                    symbol=signal.symbol,
                    quantity=quantity,
                    price=signal.price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reasoning=f"Position opened (no ETrade execution) with {signal.confidence:.1%} confidence"
                )
            
        except Exception as e:
            log.error(f"Failed to process signal for {signal.symbol}: {e}")
            return TradeResult(
                action=TradeAction.HOLD,
                symbol=signal.symbol,
                reasoning=f"Error processing signal: {str(e)}"
            )
    
    async def update_positions(self, market_data: Dict[str, Any]) -> List[TradeResult]:
        """
        Update all active positions through the unified system - PRIORITY: Stealth Trailing System
        
        This method is called every 60 seconds to update positions and ensure stealth stops
        are properly managed for maximum profit capture and automatic position closure.
        
        Args:
            market_data: Dictionary of symbol -> market data
            
        Returns:
            List of TradeResult with recommended actions
        """
        try:
            # Check if it's a trading day (weekends, US Bank holidays, Muslim holidays)
            if not self.market_manager.is_trading_day():
                log.info("❌ Not a trading day - skipping position updates")
                return []
            
            # Check if market is open
            if not self.market_manager.is_market_open():
                log.info("❌ Market is closed - skipping position updates")
                return []
            
            # PRIORITY: Update positions through stealth system (60-second refresh cycle)
            results = []
            log.info(f"🔄 Updating {len(self.active_positions)} positions through stealth trailing system...")
            
            for symbol, position in self.active_positions.items():
                if symbol in market_data:
                    # PRIORITY 1: Get stealth decision for this position
                    stealth_decision = await self.stealth_system.update_position(symbol, market_data[symbol])
                    
                    # PRIORITY 2: AUTOMATIC POSITION CLOSURE if stealth stop is hit
                    if stealth_decision.action == "EXIT":
                        log.warning(f"🚨 STEALTH TRAILING AUTOMATIC CLOSURE: {symbol} - {stealth_decision.reasoning}")
                        
                        exit_price = market_data[symbol].get('price', position.current_price)
                        is_simulated = position.metadata.get('simulated', False)
                        
                        if self.signal_only_mode or is_simulated:
                            # SIMULATED EXIT: No real trade, but track for validation
                            log.info(f"🎯 SIMULATED EXIT: {symbol} at ${exit_price:.2f} - {stealth_decision.exit_reason}")
                            result = await self._close_simulated_position(symbol, stealth_decision.exit_reason, exit_price)
                            results.append(result)
                        else:
                            # LIVE EXIT: Execute real E*TRADE sell order
                            if self.etrade_trading and self.etrade_trading.is_authenticated():
                                try:
                                    log.info(f"💸 Executing E*TRADE sell order: {symbol} {position.quantity} shares @ MARKET")
                                    sell_order_result = self.etrade_trading.place_order(
                                        symbol=symbol,
                                        quantity=position.quantity,
                                        side='SELL',
                                        order_type='MARKET'
                                    )
                                    
                                    if sell_order_result and 'orderId' in sell_order_result:
                                        log.info(f"✅ E*TRADE sell order executed: {symbol} OrderID: {sell_order_result['orderId']}")
                                    else:
                                        log.error(f"❌ E*TRADE sell order failed: {symbol}")
                                except Exception as e:
                                    log.error(f"❌ E*TRADE sell order error: {symbol} - {e}")
                            
                            # Close position in system
                            result = await self._close_position(symbol, stealth_decision.exit_reason, exit_price)
                            results.append(result)
                        
                    # PRIORITY 3: Update trailing stop for profit capture
                    elif stealth_decision.action == "TRAIL":
                        # Update stop loss to follow price up and capture more gains
                        old_stop = position.stop_loss
                        position.stop_loss = stealth_decision.new_stop_loss
                        log.info(f"📈 STEALTH TRAILING: {symbol} stop moved ${old_stop:.2f} → ${stealth_decision.new_stop_loss:.2f}")
                        results.append(TradeResult(
                            action=TradeAction.UPDATE,
                            symbol=symbol,
                            stop_loss=stealth_decision.new_stop_loss,
                            stealth_decision=stealth_decision,
                            reasoning=f"Stealth trailing: Stop updated to ${stealth_decision.new_stop_loss:.2f}"
                        ))
                    
                    # PRIORITY 4: Breakeven protection activation
                    elif stealth_decision.action == "BREAKEVEN":
                        # Move stop to breakeven to protect profits
                        old_stop = position.stop_loss
                        position.stop_loss = stealth_decision.new_stop_loss
                        log.info(f"🛡️ BREAKEVEN PROTECTION: {symbol} stop moved ${old_stop:.2f} → ${stealth_decision.new_stop_loss:.2f}")
                        results.append(TradeResult(
                            action=TradeAction.UPDATE,
                            symbol=symbol,
                            stop_loss=stealth_decision.new_stop_loss,
                            stealth_decision=stealth_decision,
                            reasoning=f"Breakeven protection: Stop moved to ${stealth_decision.new_stop_loss:.2f}"
                        ))
                    
                    else:
                        # Hold position with current settings
                        results.append(TradeResult(
                            action=TradeAction.HOLD,
                            symbol=symbol,
                            reasoning="Position held - stealth system monitoring"
                        ))
            
            # Update unified metrics
            for result in results:
                if result.action == TradeAction.CLOSE:
                    self.daily_stats['positions_closed'] += 1
                    if result.exit_reason:
                        self._update_exit_metrics(result.exit_reason)
                
                elif result.action == TradeAction.UPDATE:
                    if result.stealth_decision:
                        self._update_stealth_metrics(result.stealth_decision)
            
            # Update unified metrics
            self.unified_metrics['active_positions'] = len(self.active_positions)
            self._calculate_unified_metrics()
            
            return results
            
        except Exception as e:
            log.error(f"Failed to update positions in unified system: {e}")
            return []
    
    def _update_exit_metrics(self, exit_reason: ExitReason):
        """Update metrics based on exit reason"""
        if exit_reason in [ExitReason.TAKE_PROFIT, ExitReason.TRAILING_STOP]:
            self.unified_metrics['winning_trades'] += 1
        else:
            self.unified_metrics['losing_trades'] += 1
    
    def _update_stealth_metrics(self, stealth_decision: StealthDecision):
        """Update stealth metrics based on decision"""
        if stealth_decision.action == "BREAKEVEN":
            self.unified_metrics['breakeven_protected'] += 1
            self.daily_stats['breakeven_activations'] += 1
        elif stealth_decision.action == "TRAIL":
            self.unified_metrics['trailing_activated'] += 1
            self.daily_stats['trailing_activations'] += 1
            if stealth_decision.stealth_mode and stealth_decision.stealth_mode.value == "explosive":
                self.unified_metrics['explosive_captured'] += 1
            elif stealth_decision.stealth_mode and stealth_decision.stealth_mode.value == "moon":
                self.unified_metrics['moon_captured'] += 1
    
    def _calculate_unified_metrics(self):
        """Calculate unified performance metrics"""
        # Get performance metrics from this manager
        trade_metrics = self.get_performance_metrics()
        
        # Get stealth metrics from stealth system
        stealth_metrics = self.stealth_system.get_stealth_metrics()
        
        # Update unified metrics
        self.unified_metrics.update({
            'total_trades': trade_metrics['total_trades'],
            'winning_trades': trade_metrics['winning_trades'],
            'losing_trades': trade_metrics['losing_trades'],
            'total_pnl': trade_metrics['total_pnl'],
            'active_positions': trade_metrics['active_positions'],
            'win_rate': trade_metrics['win_rate']
        })
        
        # Calculate stealth effectiveness
        if self.unified_metrics['total_trades'] > 0:
            protected_trades = self.unified_metrics['breakeven_protected'] + self.unified_metrics['trailing_activated']
            self.unified_metrics['stealth_effectiveness'] = (protected_trades / self.unified_metrics['total_trades']) * 100
        
        # Update daily stats
        self.daily_stats['total_pnl'] = trade_metrics['total_pnl']
        self.daily_stats['best_trade'] = trade_metrics.get('best_trade', 0.0)
        self.daily_stats['worst_trade'] = trade_metrics.get('worst_trade', 0.0)
    
    def get_unified_metrics(self) -> Dict[str, Any]:
        """Get comprehensive unified metrics"""
        # Calculate current metrics
        self._calculate_unified_metrics()
        
        # Get component metrics
        trade_metrics = self.get_performance_metrics()
        stealth_metrics = self.stealth_system.get_stealth_metrics()
        
        return {
            'unified_metrics': self.unified_metrics.copy(),
            'trade_metrics': trade_metrics,
            'stealth_metrics': stealth_metrics,
            'daily_stats': self.daily_stats.copy(),
            'active_positions': self.active_positions,
            'system_status': {
                'trade_manager_active': True,
                'stealth_system_active': True,
                'circuit_breaker_active': self.circuit_breaker_active,
                'total_capital': self.current_capital
            }
        }
    
    def get_active_positions(self) -> Dict[str, PrimePosition]:
        """Get all active positions"""
        return self.active_positions.copy()
    
    def get_position_state(self, symbol: str) -> Optional[Any]:
        """Get detailed position state including stealth information"""
        # Get position from active positions
        position = self.active_positions.get(symbol)
        if not position:
            return None
        
        # Get stealth state
        stealth_state = self.stealth_system.get_position_state(symbol)
        
        return {
            'position': position,
            'stealth_state': stealth_state,
            'unified_status': 'active'
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for reporting"""
        metrics = self.get_unified_metrics()
        
        return {
            'total_trades': metrics['unified_metrics']['total_trades'],
            'winning_trades': metrics['unified_metrics']['winning_trades'],
            'losing_trades': metrics['unified_metrics']['losing_trades'],
            'win_rate': f"{metrics['unified_metrics']['win_rate']:.1f}%",
            'total_pnl': f"${metrics['unified_metrics']['total_pnl']:.2f}",
            'active_positions': metrics['unified_metrics']['active_positions'],
            'breakeven_protected': metrics['unified_metrics']['breakeven_protected'],
            'trailing_activated': metrics['unified_metrics']['trailing_activated'],
            'explosive_captured': metrics['unified_metrics']['explosive_captured'],
            'moon_captured': metrics['unified_metrics']['moon_captured'],
            'stealth_effectiveness': f"{metrics['unified_metrics']['stealth_effectiveness']:.1f}%",
            'current_capital': f"${metrics['trade_metrics']['current_capital']:.2f}",
            'max_drawdown': f"{metrics['trade_metrics']['max_drawdown']:.2%}",
            'daily_pnl': f"${metrics['trade_metrics']['daily_pnl']:.2f}"
        }
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_pnl = 0.0
        self.stealth_system.reset_daily_stats()
        self.daily_stats = {
            'positions_opened': 0,
            'positions_closed': 0,
            'breakeven_activations': 0,
            'trailing_activations': 0,
            'exits_triggered': 0,
            'total_pnl': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0
        }
        log.info("Unified system daily statistics reset")
    
    async def shutdown(self):
        """Shutdown unified system"""
        # Close all remaining positions
        for symbol in list(self.active_positions.keys()):
            await self._close_position(symbol, ExitReason.MANUAL, self.active_positions[symbol].current_price)
        
        # Shutdown stealth system
        await self.stealth_system.shutdown()
        
        log.info("Prime Unified Trade Manager shutdown complete")
    
    def _validate_signal(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> bool:
        """Validate trading signal with enhanced criteria"""
        try:
            # Check confidence threshold
            if signal.confidence < self.config.min_confidence:
                log.debug(f"Signal validation failed: confidence {signal.confidence:.2f} < {self.config.min_confidence:.2f}")
                return False
            
            # Check quality score
            if signal.quality_score < self.config.min_quality_score:
                log.debug(f"Signal validation failed: quality score {signal.quality_score:.2f} < {self.config.min_quality_score:.2f}")
                return False
            
            # Check if position already exists
            if signal.symbol in self.active_positions:
                log.debug(f"Signal validation failed: position already exists for {signal.symbol}")
                return False
            
            # Check RSI requirement
            if 'rsi' in market_data:
                rsi = market_data['rsi']
                if rsi < self.config.min_rsi or rsi > self.config.max_rsi:
                    log.debug(f"Signal validation failed: RSI {rsi:.1f} not in range [{self.config.min_rsi}, {self.config.max_rsi}]")
                    return False
            
            # Check volume requirement
            volume_ratio = market_data.get('volume_ratio', 1.0)
            if volume_ratio < self.config.min_volume_ratio:
                log.debug(f"Signal validation failed: volume ratio {volume_ratio:.2f} < {self.config.min_volume_ratio:.2f}")
                return False
            
            # Check daily loss limit
            if self.daily_pnl < -self.max_daily_loss:
                log.debug(f"Signal validation failed: daily loss limit exceeded: ${self.daily_pnl:.2f}")
                return False
            
            # Check circuit breaker
            if self.circuit_breaker_active:
                log.debug(f"Signal validation failed: circuit breaker active")
                return False
            
            return True
            
        except Exception as e:
            log.error(f"Error validating signal: {e}")
            return False
    
    async def _calculate_position_size(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> int:
        """Calculate position size based on risk parameters and signal quality"""
        try:
            # Base position size calculation
            max_position_value = self.current_capital * self.config.max_position_size_pct
            
            # Calculate shares based on price
            shares = int(max_position_value / signal.price)
            
            # Apply confidence multiplier (higher confidence = larger position)
            confidence_multiplier = min(2.0, signal.confidence * 2.0)
            shares = int(shares * confidence_multiplier)
            
            # Apply quality score multiplier (higher quality = larger position)
            quality_multiplier = min(1.5, signal.quality_score * 1.5)
            shares = int(shares * quality_multiplier)
            
            # Apply volume multiplier (higher volume = larger position)
            volume_ratio = market_data.get('volume_ratio', 1.0)
            volume_multiplier = min(1.3, 1.0 + (volume_ratio - 1.0) * 0.3)
            shares = int(shares * volume_multiplier)
            
            # Ensure within bounds
            shares = max(self.config.min_position_size, min(shares, self.config.max_position_size))
            
            return shares
            
        except Exception as e:
            log.error(f"Error calculating position size: {e}")
            return 0
    
    def _calculate_stop_and_target(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels optimized for profitability"""
        try:
            price = signal.price
            confidence = signal.confidence
            quality_score = signal.quality_score
            
            # Calculate stop loss (optimized for daily move capture)
            base_stop_pct = 0.018  # 1.8% base (optimized for daily moves)
            confidence_adjustment = (1.0 - confidence) * 0.008  # Up to 0.8% tighter
            quality_adjustment = (1.0 - quality_score) * 0.004  # Up to 0.4% tighter
            stop_loss_pct = base_stop_pct + confidence_adjustment + quality_adjustment
            stop_loss = price * (1 - stop_loss_pct)
            
            # Calculate take profit (optimized for daily move capture)
            base_tp_pct = 0.06  # 6% base (optimized for daily moves)
            confidence_multiplier = 1.0 + confidence * 0.8  # Up to 1.8x
            quality_multiplier = 1.0 + quality_score * 0.5  # Up to 1.5x
            take_profit_pct = base_tp_pct * confidence_multiplier * quality_multiplier
            take_profit = price * (1 + take_profit_pct)
            
            return stop_loss, take_profit
            
        except Exception as e:
            log.error(f"Error calculating stop and target: {e}")
            return price * 0.98, price * 1.10  # Default 2% stop, 10% target
    
    async def _close_simulated_position(self, symbol: str, exit_reason: str, exit_price: float) -> Dict[str, Any]:
        """Close simulated position and send validation alert"""
        try:
            position = self.active_positions.get(symbol)
            if not position:
                return {"success": False, "error": "Position not found"}
            
            # Calculate final P&L
            pnl = (exit_price - position.entry_price) * position.quantity
            pnl_pct = ((exit_price - position.entry_price) / position.entry_price) * 100
            holding_seconds = (datetime.utcnow() - position.entry_time).total_seconds()
            holding_minutes = holding_seconds / 60
            
            log.info(f"📊 SIMULATED POSITION CLOSED: {symbol}")
            log.info(f"   Entry: ${position.entry_price:.2f}, Exit: ${exit_price:.2f}")
            log.info(f"   P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
            log.info(f"   Duration: {holding_minutes:.1f} minutes")
            log.info(f"   Exit Reason: {exit_reason}")
            
            # Update simulated performance metrics
            self.simulated_performance['closed_positions'] += 1
            self.simulated_performance['open_positions'] -= 1
            self.simulated_performance['total_pnl'] += pnl
            
            if pnl > 0:
                self.simulated_performance['winning_trades'] += 1
            else:
                self.simulated_performance['losing_trades'] += 1
            
            total_closed = self.simulated_performance['closed_positions']
            self.simulated_performance['win_rate'] = (
                self.simulated_performance['winning_trades'] / total_closed if total_closed > 0 else 0.0
            )
            self.simulated_performance['avg_return'] = (
                (self.simulated_performance['total_pnl'] / (len(self.simulated_performance['trades']) * position.entry_price * position.quantity)) * 100
                if len(self.simulated_performance['trades']) > 0 else 0.0
            )
            
            # Record trade for End-of-Day report
            trade_record = {
                'symbol': symbol,
                'entry_price': position.entry_price,
                'exit_price': exit_price,
                'quantity': position.quantity,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'holding_minutes': holding_minutes,
                'exit_reason': exit_reason,
                'confidence': position.confidence,
                'strategy': position.strategy_mode.value if hasattr(position.strategy_mode, 'value') else str(position.strategy_mode),
                'timestamp': datetime.utcnow().isoformat()
            }
            self.simulated_performance['trades'].append(trade_record)
            
            # Send SIMULATED exit alert via Telegram
            if self.alert_manager:
                try:
                    # Create comprehensive exit alert
                    alert_text = f"""
📉 <b>SELL SIGNAL - {symbol}</b>

📊 <b>SELL</b> - {position.quantity} shares - {symbol} • Exit: ${exit_price:.2f}

<b>Order Status:</b> SIMULATED (Signal-Only Mode)

💼 <b>POSITION CLOSED:</b>
Entry: ${position.entry_price:.2f}
Exit: ${exit_price:.2f}
P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)
Duration: {holding_minutes:.0f} minutes

🎯 <b>EXIT REASON:</b>
{exit_reason}

💎 <b>DEMO VALIDATION:</b>
Simulated Performance: {self.simulated_performance['win_rate']:.0%} win rate
Total Simulated P&L: ${self.simulated_performance['total_pnl']:+.2f}

⏰ Exit Time: {datetime.utcnow().strftime('%H:%M:%S')} UTC

🎯 <b>Signal-Only Mode:</b> This validates the system would have closed this position at ${exit_price:.2f} in Live Mode
                    """
                    
                    await self.alert_manager.send_telegram_alert(alert_text)
                    log.info(f"📱 Simulated exit alert sent for {symbol}")
                except Exception as e:
                    log.error(f"Failed to send simulated exit alert: {e}")
            
            # Remove from active tracking
            if symbol in self.active_positions:
                del self.active_positions[symbol]
            if symbol in self.simulated_positions:
                del self.simulated_positions[symbol]
            
            # Remove from stealth system
            self.stealth_system.remove_position(symbol)
            
            log.info(f"✅ Simulated position closed and performance recorded")
            log.info(f"📊 Demo Mode Stats: {total_closed} trades, {self.simulated_performance['win_rate']:.1%} win rate, ${self.simulated_performance['total_pnl']:+.2f} P&L")
            
            return {
                "success": True,
                "symbol": symbol,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "exit_reason": exit_reason,
                "mode": "simulated"
            }
            
        except Exception as e:
            log.error(f"Failed to close simulated position {symbol}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _close_position(self, symbol: str, exit_reason: ExitReason, exit_price: float) -> TradeResult:
        """Close a position and update metrics"""
        try:
            if symbol not in self.active_positions:
                return TradeResult(
                    action=TradeAction.HOLD,
                    symbol=symbol,
                    reasoning="Position not found"
                )
            
            position = self.active_positions[symbol]
            
            # EXECUTE ACTUAL SELL ORDER
            if self.etrade_trading:
                try:
                    # Place sell order
                    order_result = self.etrade_trading.place_order(
                        symbol=symbol,
                        quantity=position.quantity,
                        side='SELL',
                        order_type='MARKET'
                    )
                    
                    if order_result and 'orderId' in order_result:
                        log.info(f"✅ SELL ORDER EXECUTED: {symbol} @ ${exit_price:.2f}")
                    else:
                        log.error(f"❌ Sell order execution failed for {symbol}")
                        
                except Exception as e:
                    log.error(f"Sell order execution error for {symbol}: {e}")
            
            # Calculate final PnL
            final_pnl = (exit_price - position.entry_price) * position.quantity
            final_pnl_pct = (exit_price - position.entry_price) / position.entry_price
            
            # Update performance metrics
            self.performance_metrics.total_pnl += final_pnl
            self.current_capital += final_pnl
            self.daily_pnl += final_pnl
            
            if final_pnl > 0:
                self.performance_metrics.winning_trades += 1
                self.unified_metrics['winning_trades'] += 1
                self.daily_stats['winning_trades'] += 1
                if final_pnl > self.performance_metrics.best_trade:
                    self.performance_metrics.best_trade = final_pnl
            else:
                self.performance_metrics.losing_trades += 1
                self.unified_metrics['losing_trades'] += 1
                self.daily_stats['losing_trades'] += 1
                if final_pnl < self.performance_metrics.worst_trade:
                    self.performance_metrics.worst_trade = final_pnl
            
            # Update daily PnL
            self.daily_stats['total_pnl'] += final_pnl
            
            # Update drawdown
            if self.current_capital > self.peak_capital:
                self.peak_capital = self.current_capital
                self.performance_metrics.current_drawdown = 0.0
            else:
                self.performance_metrics.current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
                if self.performance_metrics.current_drawdown > self.performance_metrics.max_drawdown:
                    self.performance_metrics.max_drawdown = self.performance_metrics.current_drawdown
            
            # Send trade exit alert
            if self.alert_manager:
                try:
                    trade_alert = TradeAlert(
                        symbol=symbol,
                        strategy=position.strategy_mode.value,
                        action='SELL',
                        price=exit_price,
                        quantity=position.quantity,
                        confidence=position.confidence,
                        expected_return=final_pnl_pct,
                        reason=f"Position closed: {exit_reason.value}",
                        metadata={'entry_price': position.entry_price}
                    )
                    await self.alert_manager.send_trade_exit_alert(trade_alert)
                except Exception as e:
                    log.error(f"Failed to send trade exit alert: {e}")
            
            # Record trade
            trade_record = {
                'symbol': symbol,
                'entry_price': position.entry_price,
                'exit_price': exit_price,
                'quantity': position.quantity,
                'pnl': final_pnl,
                'pnl_pct': final_pnl_pct,
                'exit_reason': exit_reason.value,
                'holding_hours': (datetime.utcnow() - position.entry_time).total_seconds() / 3600,
                'confidence': position.confidence,
                'entry_time': position.entry_time,
                'exit_time': datetime.utcnow()
            }
            self.trade_history.append(trade_record)
            
            # Remove from active positions
            del self.active_positions[symbol]
            self.performance_metrics.active_positions = len(self.active_positions)
            self.unified_metrics['active_positions'] = len(self.active_positions)
            self.daily_stats['positions_closed'] += 1
            
            log.info(f"🔚 Position closed: {symbol} @ ${exit_price:.2f} "
                    f"(PnL: ${final_pnl:.2f}, {final_pnl_pct:.2%}, "
                    f"Reason: {exit_reason.value})")
            
            return TradeResult(
                action=TradeAction.CLOSE,
                symbol=symbol,
                price=exit_price,
                exit_reason=exit_reason,
                reasoning=f"Position closed: {exit_reason.value}"
            )
            
        except Exception as e:
            log.error(f"Failed to close position {symbol}: {e}")
            return TradeResult(
                action=TradeAction.HOLD,
                symbol=symbol,
                reasoning=f"Error closing position: {str(e)}"
            )
    
    async def generate_end_of_day_report(self):
        """Generate and send end-of-day report"""
        try:
            if not self.alert_manager:
                log.warning("Alert manager not available for end-of-day report")
                return
            
            # Calculate daily metrics
            total_trades = self.daily_stats['positions_opened']
            winning_trades = self.daily_stats['winning_trades']
            losing_trades = self.daily_stats['losing_trades']
            win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
            total_pnl = self.daily_stats['total_pnl']
            daily_return = (total_pnl / self.current_capital) * 100 if self.current_capital > 0 else 0.0
            
            # Create performance summary
            from .prime_alert_manager import PerformanceSummary
            summary = PerformanceSummary(
                date=datetime.now(),
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                total_pnl=total_pnl,
                daily_return=daily_return
            )
            
            # Send end-of-day summary
            await self.alert_manager.send_end_of_day_summary(summary)
            
            # Reset daily stats
            self.daily_stats.update({
                'positions_opened': 0,
                'positions_closed': 0,
                'total_pnl': 0.0,
                'winning_trades': 0,
                'losing_trades': 0
            })
            
            log.info("End-of-day report sent successfully")
            
        except Exception as e:
            log.error(f"Failed to generate end-of-day report: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        # Calculate current metrics
        self._calculate_unified_metrics()
        
        return {
            'total_trades': self.performance_metrics.total_trades,
            'winning_trades': self.performance_metrics.winning_trades,
            'losing_trades': self.performance_metrics.losing_trades,
            'win_rate': self.performance_metrics.win_rate,
            'total_pnl': self.performance_metrics.total_pnl,
            'avg_trade_pnl': self.performance_metrics.avg_trade_pnl,
            'best_trade': self.performance_metrics.best_trade,
            'worst_trade': self.performance_metrics.worst_trade,
            'max_drawdown': self.performance_metrics.max_drawdown,
            'current_drawdown': self.performance_metrics.current_drawdown,
            'active_positions': self.performance_metrics.active_positions,
            'current_capital': self.current_capital,
            'daily_pnl': self.daily_pnl,
            'circuit_breaker_active': self.circuit_breaker_active,
            'breakeven_protected': self.performance_metrics.breakeven_protected,
            'trailing_activated': self.performance_metrics.trailing_activated,
            'explosive_captured': self.performance_metrics.explosive_captured,
            'moon_captured': self.performance_metrics.moon_captured,
            'stealth_effectiveness': self.performance_metrics.stealth_effectiveness
        }

# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def get_prime_unified_trade_manager(strategy_mode: StrategyMode = StrategyMode.STANDARD) -> PrimeUnifiedTradeManager:
    """Get Prime Unified Trade Manager instance"""
    return PrimeUnifiedTradeManager(strategy_mode)

def create_unified_trade_manager(strategy_mode: StrategyMode = StrategyMode.STANDARD) -> PrimeUnifiedTradeManager:
    """Create new Prime Unified Trade Manager instance"""
    return PrimeUnifiedTradeManager(strategy_mode)

# ============================================================================
# TESTING
# ============================================================================

async def test_unified_system():
    """Test the unified trade management system"""
    try:
        print("🧪 Testing Prime Unified Trade Management System...")
        
        # Create unified manager
        manager = PrimeUnifiedTradeManager(StrategyMode.STANDARD)
        
        # Create mock signal
        signal = PrimeSignal(
            symbol="AAPL",
            side=SignalSide.BUY,
            price=150.0,
            confidence=0.95,
            quality_score=0.90,
            reason="Test signal"
        )
        
        # Create mock market data
        market_data = {
            'price': 150.0,
            'rsi': 65.0,
            'volume_ratio': 2.0,
            'atr': 2.0,
            'momentum': 0.1
        }
        
        # Process signal
        result = await manager.process_signal(signal, market_data)
        print(f"✅ Signal processed: {result.action} - {result.reasoning}")
        
        # Update positions
        market_data['price'] = 152.0
        results = await manager.update_positions({'AAPL': market_data})
        print(f"✅ Positions updated: {len(results)} results")
        
        # Get unified metrics
        metrics = manager.get_unified_metrics()
        print(f"✅ Unified metrics: {metrics['unified_metrics']['total_trades']} trades")
        
        # Get performance summary
        summary = manager.get_performance_summary()
        print(f"✅ Performance summary: {summary['win_rate']} win rate, {summary['total_pnl']} PnL")
        
        print("🎯 Unified system test completed successfully!")
        
    except Exception as e:
        print(f"❌ Unified system test failed: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(test_unified_system())
