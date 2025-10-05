#!/usr/bin/env python3
"""
Prime Risk Manager
=================

Comprehensive risk management system implementing the 10 core principles
for the Easy ETrade Strategy. This module handles all risk management
decisions for opening new positions.

Key Features:
- Multi-layer risk framework with 10 core principles
- Dynamic position sizing with confidence-based scaling
- Trade ownership isolation (only manages Easy ETrade Strategy positions)
- Capital allocation with 80/20 rule and dynamic scaling
- Drawdown protection with Safe Mode activation
- News sentiment integration for trade filtering
- Auto-close engine with multiple exit triggers
- End-of-day reporting and P&L tracking
- Capital compounding with risk-weighted allocation
- Re-entry logic with confidence gating
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

from .prime_models import (
    StrategyMode, SignalType, SignalSide, TradeStatus, StopType, TrailingMode,
    MarketRegime, SignalQuality, ConfidenceTier, PrimeSignal, PrimePosition,
    PrimeTrade, get_strategy_config
)
from .config_loader import get_config_value

log = logging.getLogger("prime_risk_manager")

# ============================================================================
# ENUMS
# ============================================================================

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class PositionSizingMethod(Enum):
    """Position sizing method enumeration"""
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    ATR_BASED = "atr_based"
    KELLY = "kelly"
    CONFIDENCE_BASED = "confidence_based"
    DYNAMIC = "dynamic"

class TradeOwnership(Enum):
    """Trade ownership enumeration"""
    EASY_ETRADE_STRATEGY = "EES"
    MANUAL = "MANUAL"
    OTHER_SYSTEM = "OTHER"
    UNKNOWN = "UNKNOWN"

class SafeModeReason(Enum):
    """Safe mode activation reasons"""
    DRAWDOWN_EXCEEDED = "drawdown_exceeded"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    MARGIN_CALL = "margin_call"
    SYSTEM_ERROR = "system_error"
    MANUAL_OVERRIDE = "manual_override"

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class RiskParameters:
    """Dynamic risk parameters"""
    # Core risk limits
    max_risk_per_trade_pct: float = 10.0
    cash_reserve_pct: float = 20.0
    trading_cash_pct: float = 80.0
    max_drawdown_pct: float = 10.0
    max_daily_loss_pct: float = 5.0
    
    # Position limits
    max_concurrent_positions: int = 20  # Max open positions at once
    max_positions_per_strategy: int = 5  # Max positions per strategy
    max_daily_trades: int = 200  # Daily trade limit (can close and reopen)
    
    # Confidence thresholds
    ultra_high_confidence_threshold: float = 0.995
    high_confidence_threshold: float = 0.95
    medium_confidence_threshold: float = 0.90
    
    # Confidence multipliers
    ultra_high_confidence_multiplier: float = 1.5
    high_confidence_multiplier: float = 1.2
    medium_confidence_multiplier: float = 1.0
    
    # Position sizing
    min_position_value: float = 50.0
    base_position_size_pct: float = 10.0  # 10% base position size
    max_position_size_pct: float = 35.0   # 35% max position size (after boosting)
    
    # Transaction costs
    transaction_cost_pct: float = 0.5
    
    # Stop management
    stop_loss_atr_multiplier: float = 1.5
    take_profit_atr_multiplier: float = 2.0

@dataclass
class AccountMetrics:
    """Account metrics for risk assessment"""
    available_cash: float
    total_account_value: float
    cash_reserve: float
    trading_cash: float
    margin_available: Optional[float] = None
    buying_power: Optional[float] = None
    current_drawdown_pct: float = 0.0
    daily_pnl_pct: float = 0.0
    total_open_positions: int = 0
    strategy_positions: int = 0
    manual_positions: int = 0
    prime_system_position_value: float = 0.0  # Value of positions opened by Prime system only

@dataclass
class PositionRisk:
    """Position risk assessment"""
    symbol: str
    quantity: int
    entry_price: float
    position_value: float
    risk_amount: float
    risk_percentage: float
    confidence: float
    confidence_multiplier: float
    atr: float
    stop_loss_price: float
    take_profit_price: float
    transaction_cost: float
    net_position_value: float
    risk_reward_ratio: float
    position_ownership: TradeOwnership = TradeOwnership.EASY_ETRADE_STRATEGY

@dataclass
class RiskDecision:
    """Risk management decision"""
    approved: bool
    reason: str
    risk_level: RiskLevel
    position_size: Optional[PositionRisk] = None
    safe_mode_triggered: bool = False
    safe_mode_reason: Optional[SafeModeReason] = None
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class MarketConditions:
    """Market conditions for risk adjustment"""
    volatility: float = 0.0
    trend_strength: float = 0.0
    volume_ratio: float = 0.0
    market_regime: MarketRegime = MarketRegime.SIDEWAYS
    vix_level: float = 0.0
    sector_rotation: Dict[str, float] = field(default_factory=dict)

# ============================================================================
# PRIME RISK MANAGER
# ============================================================================

class PrimeRiskManager:
    """
    Prime Risk Manager implementing comprehensive risk management
    for the Easy ETrade Strategy with 10 core principles.
    """
    
    def __init__(self, strategy_mode: StrategyMode = StrategyMode.STANDARD):
        self.strategy_mode = strategy_mode
        self.config = get_strategy_config(strategy_mode)
        self.risk_params = self._load_risk_parameters()
        
        # E*TRADE integration for real account data
        self.etrade_trading = None
        self._initialize_etrade_trading()
        
        # Risk tracking
        self.current_positions: Dict[str, UnifiedPosition] = {}
        self.strategy_positions: Dict[str, UnifiedPosition] = {}
        self.manual_positions: Dict[str, UnifiedPosition] = {}
        self.position_history: deque = deque(maxlen=1000)
        
        # Performance tracking
        self.daily_pnl: float = 0.0
        self.total_pnl: float = 0.0
        self.consecutive_losses: int = 0
        self.consecutive_wins: int = 0
        self.win_streak_multiplier: float = 1.0
        
        # Safe mode
        self.safe_mode_active: bool = False
        self.safe_mode_reason: Optional[SafeModeReason] = None
        self.safe_mode_activated_at: Optional[datetime] = None
        
        # Account metrics
        self.account_metrics: Optional[AccountMetrics] = None
        
        # Market conditions
        self.market_conditions: Optional[MarketConditions] = None
        
        log.info(f"PrimeRiskManager initialized for {strategy_mode.value} strategy")
    
    def _initialize_etrade_trading(self):
        """Initialize E*TRADE trading integration for real account data"""
        try:
            from .prime_etrade_trading import PrimeETradeTrading
            
            # Determine environment based on configuration
            etrade_mode = get_config_value('ETRADE_MODE', 'sandbox')
            
            # Initialize E*TRADE trading with environment
            self.etrade_trading = PrimeETradeTrading(environment=etrade_mode)
            
            # Initialize the trading system
            if self.etrade_trading.initialize():
                log.info("✅ Risk Manager E*TRADE integration successful")
                
                # Get account summary for verification
                account_summary = self.etrade_trading.get_account_summary()
                if 'error' not in account_summary:
                    log.info(f"✅ Risk Manager connected to E*TRADE account: {account_summary['account']['name']}")
                    log.info(f"   Cash available for investment: ${account_summary['balance']['cash_available_for_investment']}")
                    log.info(f"   Cash buying power: ${account_summary['balance']['cash_buying_power']}")
                else:
                    log.warning(f"⚠️ Risk Manager E*TRADE account issue: {account_summary['error']}")
            else:
                log.error("❌ Risk Manager E*TRADE integration failed")
                self.etrade_trading = None
                
        except Exception as e:
            log.error(f"❌ Risk Manager E*TRADE integration error: {e}")
            self.etrade_trading = None
    
    def _load_risk_parameters(self) -> RiskParameters:
        """Load risk parameters from configuration"""
        return RiskParameters(
            max_risk_per_trade_pct=get_config_value("MAX_SINGLE_POSITION_RISK_PCT", 35.0),
            cash_reserve_pct=get_config_value("CASH_RESERVE_PCT", 20.0),
            trading_cash_pct=get_config_value("TRADING_CASH_PCT", 80.0),
            max_drawdown_pct=get_config_value("MAX_DRAWDOWN_PCT", 10.0),
            max_daily_loss_pct=get_config_value("MAX_DAILY_LOSS_PCT", 5.0),
            max_concurrent_positions=get_config_value("MAX_OPEN_POSITIONS", 20),
            max_positions_per_strategy=get_config_value("MAX_POSITIONS_PER_STRATEGY", 5),
            ultra_high_confidence_threshold=get_config_value("ULTRA_HIGH_CONFIDENCE_THRESHOLD", 0.95),
            high_confidence_threshold=get_config_value("HIGH_CONFIDENCE_THRESHOLD", 0.90),
            medium_confidence_threshold=get_config_value("MEDIUM_CONFIDENCE_THRESHOLD", 0.85),
            ultra_high_confidence_multiplier=get_config_value("ULTRA_HIGH_CONFIDENCE_MULTIPLIER", 2.5),
            high_confidence_multiplier=get_config_value("HIGH_CONFIDENCE_MULTIPLIER", 2.0),
            medium_confidence_multiplier=get_config_value("MEDIUM_CONFIDENCE_MULTIPLIER", 1.0),
            min_position_value=get_config_value("MIN_POSITION_VALUE", 50.0),
            base_position_size_pct=get_config_value("BASE_POSITION_SIZE_PCT", 10.0),
            max_position_size_pct=get_config_value("MAX_POSITION_SIZE_PCT", 35.0),
            transaction_cost_pct=get_config_value("TRANSACTION_COST_PCT", 0.5),
            stop_loss_atr_multiplier=get_config_value("STOP_LOSS_ATR_MULTIPLIER", 1.5),
            take_profit_atr_multiplier=get_config_value("TAKE_PROFIT_ATR_MULTIPLIER", 2.0)
        )
    
    async def assess_position_risk(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> RiskDecision:
        """
        Comprehensive risk assessment for opening a new position.
        Implements all 10 core risk management principles.
        """
        try:
            log.info(f"Assessing risk for {signal.symbol} position")
            
            # 1. Check Safe Mode status
            if self.safe_mode_active:
                return RiskDecision(
                    approved=False,
                    reason=f"Safe mode active: {self.safe_mode_reason.value if self.safe_mode_reason else 'unknown'}",
                    risk_level=RiskLevel.HIGH,
                    safe_mode_triggered=True,
                    safe_mode_reason=self.safe_mode_reason
                )
            
            # 2. Load current account metrics
            await self._update_account_metrics()
            if not self.account_metrics:
                return RiskDecision(
                    approved=False,
                    reason="Unable to load account metrics",
                    risk_level=RiskLevel.HIGH
                )
            
            # 3. Check drawdown protection (Principle 7)
            drawdown_check = self._check_drawdown_protection()
            if not drawdown_check["approved"]:
                await self._activate_safe_mode(SafeModeReason.DRAWDOWN_EXCEEDED)
                return RiskDecision(
                    approved=False,
                    reason=drawdown_check["reason"],
                    risk_level=RiskLevel.HIGH,
                    safe_mode_triggered=True,
                    safe_mode_reason=SafeModeReason.DRAWDOWN_EXCEEDED
                )
            
            # 4. Check daily loss limits
            daily_loss_check = self._check_daily_loss_limits()
            if not daily_loss_check["approved"]:
                await self._activate_safe_mode(SafeModeReason.DAILY_LOSS_LIMIT)
                return RiskDecision(
                    approved=False,
                    reason=daily_loss_check["reason"],
                    risk_level=RiskLevel.HIGH,
                    safe_mode_triggered=True,
                    safe_mode_reason=SafeModeReason.DAILY_LOSS_LIMIT
                )
            
            # 5. Check position limits (Principle 7)
            position_limit_check = self._check_position_limits()
            if not position_limit_check["approved"]:
                return RiskDecision(
                    approved=False,
                    reason=position_limit_check["reason"],
                    risk_level=RiskLevel.MEDIUM
                )
            
            # 6. Check news sentiment filtering (Principle 5)
            sentiment_check = self._check_news_sentiment(signal, market_data)
            if not sentiment_check["approved"]:
                return RiskDecision(
                    approved=False,
                    reason=sentiment_check["reason"],
                    risk_level=RiskLevel.MEDIUM
                )
            
            # 7. Calculate dynamic position sizing (Principle 4)
            position_sizing = await self._calculate_position_sizing(signal, market_data)
            if not position_sizing["approved"]:
                return RiskDecision(
                    approved=False,
                    reason=position_sizing["reason"],
                    risk_level=RiskLevel.LOW
                )
            
            # 8. Check minimum position validation - PORTFOLIO-AWARE minimum
            # For concurrent positions, use a proportional minimum based on portfolio allocation
            if not self.account_metrics:
                return RiskDecision(
                    approved=False,
                    reason="No account metrics available for minimum position validation",
                    risk_level=RiskLevel.HIGH
                )
            
            available_capital = self.account_metrics.available_cash
            num_concurrent_positions = market_data.get("num_concurrent_positions", 1)
            portfolio_aware_minimum = (available_capital * 0.80) / max(1, num_concurrent_positions) * 0.05  # 5% of fair share
            effective_minimum = min(self.risk_params.min_position_value, portfolio_aware_minimum)
            
            if position_sizing["position_risk"].net_position_value < effective_minimum:
                return RiskDecision(
                    approved=False,
                    reason=f"Position size too small: ${position_sizing['position_risk'].net_position_value:.2f} < ${effective_minimum:.2f} (portfolio-aware minimum)",
                    risk_level=RiskLevel.LOW,
                    recommendations=["Wait for account growth", "Consider micro-position sizing", "Reduce concurrent positions"]
                )
            
            # 9. Final risk assessment
            final_risk_assessment = self._final_risk_assessment(position_sizing["position_risk"])
            
            # 10. Create approved risk decision
            return RiskDecision(
                approved=True,
                reason="Position approved after comprehensive risk assessment",
                risk_level=final_risk_assessment["risk_level"],
                position_size=position_sizing["position_risk"],
                warnings=final_risk_assessment["warnings"],
                recommendations=final_risk_assessment["recommendations"]
            )
            
        except Exception as e:
            log.error(f"Risk assessment failed for {signal.symbol}: {e}")
            return RiskDecision(
                approved=False,
                reason=f"Risk assessment error: {str(e)}",
                risk_level=RiskLevel.HIGH
            )
    
    async def _update_account_metrics(self):
        """Update account metrics from REAL E*TRADE API"""
        try:
            if not self.etrade_trading:
                log.error("E*TRADE trading not available for account metrics")
                return
            
            # Get REAL account balance from E*TRADE
            balance = self.etrade_trading.get_account_balance()
            if not balance:
                log.error("Failed to get account balance from E*TRADE")
                return
            
            # Get current positions from E*TRADE
            portfolio = self.etrade_trading.get_portfolio()
            
            # Calculate REAL metrics from E*TRADE data
            available_cash = balance.cash_available_for_investment or 0.0
            total_value = balance.account_value or available_cash
            cash_reserve = total_value * (self.risk_params.cash_reserve_pct / 100.0)
            trading_cash = total_value * (self.risk_params.trading_cash_pct / 100.0)
            
            # Count strategy positions vs manual positions
            strategy_positions = len([p for p in portfolio if p.symbol in self.strategy_positions])
            manual_positions = len(portfolio) - strategy_positions
            
            # Calculate drawdown from peak capital
            current_drawdown_pct = 0.0
            if hasattr(self, 'peak_capital') and self.peak_capital > 0:
                current_drawdown_pct = max(0.0, (self.peak_capital - total_value) / self.peak_capital)
            
            self.account_metrics = AccountMetrics(
                available_cash=available_cash,
                total_account_value=total_value,
                cash_reserve=cash_reserve,
                trading_cash=trading_cash,
                margin_available=balance.cash_buying_power,
                buying_power=balance.cash_buying_power,
                current_drawdown_pct=current_drawdown_pct,
                daily_pnl_pct=self.daily_pnl / total_value if total_value > 0 else 0.0,
                total_open_positions=len(portfolio),
                strategy_positions=strategy_positions,
                manual_positions=manual_positions
            )
            
            log.info(f"✅ REAL account metrics updated from E*TRADE: ${available_cash:.2f} available cash, ${total_value:.2f} total value")
            
        except Exception as e:
            log.error(f"Failed to update account metrics from E*TRADE: {e}")
    
    def _check_drawdown_protection(self) -> Dict[str, Any]:
        """Check drawdown protection (Principle 7)"""
        if not self.account_metrics:
            return {"approved": False, "reason": "No account metrics available"}
        
        current_drawdown = self.account_metrics.current_drawdown_pct
        max_drawdown = self.risk_params.max_drawdown_pct
        
        if current_drawdown >= max_drawdown:
            return {
                "approved": False,
                "reason": f"Drawdown limit exceeded: {current_drawdown:.2f}% >= {max_drawdown}%"
            }
        
        return {"approved": True}
    
    def _check_daily_loss_limits(self) -> Dict[str, Any]:
        """Check daily loss limits"""
        if not self.account_metrics:
            return {"approved": False, "reason": "No account metrics available"}
        
        daily_pnl = self.account_metrics.daily_pnl_pct
        max_daily_loss = self.risk_params.max_daily_loss_pct
        
        if daily_pnl <= -max_daily_loss:
            return {
                "approved": False,
                "reason": f"Daily loss limit exceeded: {daily_pnl:.2f}% <= -{max_daily_loss}%"
            }
        
        return {"approved": True}
    
    def _check_position_limits(self) -> Dict[str, Any]:
        """Check position limits (Principle 7)"""
        if not self.account_metrics:
            return {"approved": False, "reason": "No account metrics available"}
        
        current_positions = self.account_metrics.strategy_positions
        max_positions = self.risk_params.max_concurrent_positions
        
        if current_positions >= max_positions:
            return {
                "approved": False,
                "reason": f"Position limit reached: {current_positions}/{max_positions}"
            }
        
        # Check portfolio risk limits
        max_portfolio_risk_pct = get_config_value("MAX_PORTFOLIO_RISK_PCT", 80.0)
        total_account_value = self.account_metrics.total_account_value
        trading_cash = self.account_metrics.trading_cash
        
        # Calculate current portfolio risk percentage
        current_portfolio_risk_pct = (trading_cash / total_account_value) * 100.0
        
        if current_portfolio_risk_pct >= max_portfolio_risk_pct:
            return {
                "approved": False,
                "reason": f"Portfolio risk limit reached: {current_portfolio_risk_pct:.1f}% >= {max_portfolio_risk_pct}%"
            }
        
        return {"approved": True}
    
    def _check_news_sentiment(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check news sentiment filtering (Principle 5)"""
        try:
            # Get news sentiment from market data
            news_sentiment = market_data.get("news_sentiment", {})
            sentiment_score = news_sentiment.get("sentiment_score", 0.0)
            sentiment_direction = news_sentiment.get("direction", "neutral")
            
            # Check for divergent sentiment
            if signal.side == SignalSide.BUY and sentiment_direction == "negative":
                return {
                    "approved": False,
                    "reason": f"Negative news sentiment ({sentiment_score:.2f}) conflicts with buy signal"
                }
            elif signal.side == SignalSide.SELL and sentiment_direction == "positive":
                return {
                    "approved": False,
                    "reason": f"Positive news sentiment ({sentiment_score:.2f}) conflicts with sell signal"
                }
            
            return {"approved": True}
            
        except Exception as e:
            log.warning(f"News sentiment check failed: {e}")
            return {"approved": True}  # Allow trade if sentiment check fails
    
    async def _calculate_position_sizing(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate position sizing with boosting factors and 80/20 rule
        Implements position splitting from 80% trading capital with confidence-based scaling,
        profit-based scaling, strategy agreement bonuses, and win streak boosting
        """
        try:
            if not self.account_metrics:
                return {"approved": False, "reason": "No account metrics not available"}
            
            # Get market data
            current_price = market_data.get("price", 0.0)
            atr = market_data.get("atr", 0.0)
            volume = market_data.get("volume", 0)
            num_concurrent_positions = market_data.get("num_concurrent_positions", 1)
            
            if current_price <= 0:
                return {"approved": False, "reason": "Invalid current price"}
            
            # CRITICAL: Use PRIME SYSTEM PORTFOLIO VALUE for position sizing calculations
            # This includes available cash + current PRIME SYSTEM positions only
            # This ensures consistent position sizing regardless of how many PRIME positions are already open
            # NOTE: We ignore positions from other systems/manual trading
            prime_system_portfolio_value = self.account_metrics.available_cash + self.account_metrics.prime_system_position_value
            available_capital = self.account_metrics.available_cash  # Keep for cash availability checks
            
            log.debug(f"Position sizing calculation:")
            log.debug(f"  Available cash: ${self.account_metrics.available_cash:.2f}")
            log.debug(f"  Prime system positions value: ${self.account_metrics.prime_system_position_value:.2f}")
            log.debug(f"  Prime system portfolio value: ${prime_system_portfolio_value:.2f}")
            log.debug(f"  Concurrent positions: {num_concurrent_positions}")
            log.debug(f"  Note: Ignoring non-Prime system positions")
            
            # 1. Calculate base position value using PORTFOLIO-AWARE sizing
            # For concurrent positions, distribute 80% of available cash proportionally
            try:
                # Handle string values with comments
                base_position_size_str = str(self.risk_params.base_position_size_pct).split('#')[0].strip()
                base_position_size_pct = float(base_position_size_str)
                
                # PRIME SYSTEM PORTFOLIO VALUE: Use 80% of PRIME SYSTEM PORTFOLIO VALUE for trading, divided by concurrent positions
                trading_cash_80_percent = prime_system_portfolio_value * 0.80  # 80% of PRIME SYSTEM PORTFOLIO VALUE
                
                # Each position gets its fair share of the 80% trading cash
                fair_share_per_position = trading_cash_80_percent / max(1, num_concurrent_positions)
                
                # MAXIMIZE UTILIZATION: Use a much larger percentage of fair share to utilize more cash
                # For 10 concurrent positions, we want each position to use more of its fair share
                if num_concurrent_positions <= 5:
                    utilization_pct = 0.90  # Use 90% of fair share for 5 or fewer positions
                elif num_concurrent_positions <= 10:
                    utilization_pct = 0.80  # Use 80% of fair share for 6-10 positions
                else:
                    utilization_pct = 0.70  # Use 70% of fair share for 11+ positions
                
                # Calculate base position value using the utilization percentage
                base_position_value = fair_share_per_position * utilization_pct
                
            except (TypeError, ValueError) as e:
                log.error(f"Error in base position size calculation: {e}, value: {self.risk_params.base_position_size_pct}")
                # Use default value with full utilization
                trading_cash_80_percent = prime_system_portfolio_value * 0.80
                fair_share_per_position = trading_cash_80_percent / max(1, num_concurrent_positions)
                
                # Apply same utilization logic as above
                if num_concurrent_positions <= 5:
                    utilization_pct = 0.90
                elif num_concurrent_positions <= 10:
                    utilization_pct = 0.80
                else:
                    utilization_pct = 0.70
                
                base_position_value = fair_share_per_position * utilization_pct
            
            # 3. Apply confidence multiplier for position sizing
            confidence_multiplier = self._get_confidence_multiplier(signal.confidence)
            
            # 4. Apply strategy agreement bonus for position sizing
            agreement_bonus = self._get_strategy_agreement_bonus(signal, market_data)
            
            # 5. Apply profit-based scaling multiplier
            profit_scaling_multiplier = self._get_profit_scaling_multiplier()
            
            # 6. Apply win streak multiplier
            win_streak_multiplier = self._get_win_streak_multiplier()
            
            # 7. Apply all multipliers to calculate position value
            position_value = (
                base_position_value * 
                confidence_multiplier * 
                (1 + agreement_bonus) * 
                profit_scaling_multiplier * 
                win_streak_multiplier
            )
            
            # 8. Apply maximum position size limit (35% of PRIME SYSTEM PORTFOLIO VALUE)
            try:
                # Handle string values with comments
                max_position_size_str = str(self.risk_params.max_position_size_pct).split('#')[0].strip()
                max_position_size_pct = float(max_position_size_str)
                max_position_value = prime_system_portfolio_value * (max_position_size_pct / 100.0)
                position_value = min(position_value, max_position_value)
            except (TypeError, ValueError) as e:
                log.error(f"Error in max position size calculation: {e}, value: {self.risk_params.max_position_size_pct}")
                # Use default value
                max_position_value = prime_system_portfolio_value * 0.35  # 35% default
                position_value = min(position_value, max_position_value)
            
            # 9. PORTFOLIO-AWARE CONFIDENCE SCALING: Distribute 80% cash based on confidence weights
            # Instead of capping each position equally, scale based on confidence and agreement
            
            # Calculate confidence weights for all positions (this is a simplified approach)
            # In a real system, we'd need to know all concurrent positions to calculate proper weights
            # For now, we'll use the current position's confidence as a proxy
            
            # Calculate the confidence weight (0.5 to 1.5 range based on confidence and agreement)
            confidence_weight = 0.5  # Base weight
            confidence_weight += (signal.confidence - 0.85) * 2.0  # Confidence contribution (0.85-0.99 range)
            confidence_weight += agreement_bonus * 0.3  # Agreement contribution
            
            # Normalize weight to reasonable range (0.7 to 1.3)
            confidence_weight = max(0.7, min(1.3, confidence_weight))
            
            # Apply portfolio-aware scaling: use confidence weight to determine position size
            # within the fair share allocation
            max_fair_share = trading_cash_80_percent / max(1, num_concurrent_positions)
            confidence_scaled_allocation = max_fair_share * confidence_weight
            
            # Use the confidence-scaled allocation instead of the raw position value
            position_value = min(position_value, confidence_scaled_allocation)
            
            # 10. CRITICAL: Check if we have enough available cash to open this position
            # If not enough cash, reduce position size to available cash or reject
            if position_value > available_capital:
                if available_capital < 50.0:  # Minimum $50 position
                    log.warning(f"Insufficient cash for position: ${position_value:.2f} > ${available_capital:.2f}")
                    return PositionRisk(
                        position_value=0.0,
                        quantity=0.0,
                        risk_percentage=0.0,
                        confidence_multiplier=confidence_multiplier,
                        agreement_bonus=agreement_bonus,
                        risk_level=RiskLevel.HIGH,
                        reasoning="Insufficient available cash for position"
                    )
                else:
                    # Reduce position size to available cash
                    position_value = available_capital
                    log.info(f"Reduced position size to available cash: ${position_value:.2f}")
            
            log.debug(f"Final position sizing:")
            log.debug(f"  Base position value: ${base_position_value:.2f}")
            log.debug(f"  Confidence multiplier: {confidence_multiplier:.2f}x")
            log.debug(f"  Agreement bonus: +{agreement_bonus:.0%}")
            log.debug(f"  Final position value: ${position_value:.2f}")
            
            # Calculate quantity with proper decimal formatting and minimum shares
            raw_quantity = position_value / current_price
            
            # Ensure minimum 0.10 shares and round to 2 decimal places
            if raw_quantity < 0.10:
                quantity = 0.10  # Minimum share amount
            else:
                quantity = round(raw_quantity, 2)  # Round to 2 decimal places
            
            if quantity <= 0:
                return {"approved": False, "reason": "Position size too small after calculations"}
            
            # Calculate transaction cost
            transaction_cost = position_value * (self.risk_params.transaction_cost_pct / 100.0)
            net_position_value = position_value - transaction_cost
            
            # Calculate risk metrics using PRIME SYSTEM PORTFOLIO VALUE
            risk_amount = position_value
            risk_percentage = (risk_amount / prime_system_portfolio_value) * 100.0
            
            # Calculate stop loss and take profit
            if atr > 0:
                stop_loss_price = current_price - (atr * self.risk_params.stop_loss_atr_multiplier)
                take_profit_price = current_price + (atr * self.risk_params.take_profit_atr_multiplier)
                risk_reward_ratio = (take_profit_price - current_price) / (current_price - stop_loss_price)
            else:
                stop_loss_price = current_price * 0.95  # 5% stop loss
                take_profit_price = current_price * 1.10  # 10% take profit
                risk_reward_ratio = 2.0
            
            # Create position risk object
            position_risk = PositionRisk(
                symbol=signal.symbol,
                quantity=quantity,
                entry_price=current_price,
                position_value=position_value,
                risk_amount=risk_amount,
                risk_percentage=risk_percentage,
                confidence=signal.confidence,
                confidence_multiplier=confidence_multiplier,
                atr=atr,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                transaction_cost=transaction_cost,
                net_position_value=net_position_value,
                risk_reward_ratio=risk_reward_ratio
            )
            
            log.info(f"💰 Position sizing calculated for {signal.symbol}: "
                    f"${position_value:.2f} value ({risk_percentage:.1f}% of available capital), {quantity} shares, "
                    f"Available Cash: ${available_capital:.2f}, Trading Cash (80%): ${trading_cash_80_percent:.2f}, "
                    f"Base Position: ${base_position_value:.2f}, Concurrent Positions: {num_concurrent_positions}, "
                    f"Conf Mult: {confidence_multiplier:.2f}x, Agreement: {agreement_bonus:.2f}, "
                    f"Profit: {profit_scaling_multiplier:.2f}x, Win Streak: {win_streak_multiplier:.2f}x")
            
            return {
                "approved": True,
                "position_risk": position_risk
            }
            
        except Exception as e:
            log.error(f"Position sizing calculation failed: {e}")
            return {"approved": False, "reason": f"Position sizing error: {str(e)}"}
    
    def _get_confidence_multiplier(self, confidence: float) -> float:
        """Get confidence multiplier for position sizing (Principle 6) - IDENTICAL to Demo Mode"""
        try:
            # Handle string values with comments
            ultra_high_threshold = float(str(self.risk_params.ultra_high_confidence_threshold).split('#')[0].strip())
            high_threshold = float(str(self.risk_params.high_confidence_threshold).split('#')[0].strip())
            medium_threshold = float(str(self.risk_params.medium_confidence_threshold).split('#')[0].strip())
            
            ultra_high_multiplier = float(str(self.risk_params.ultra_high_confidence_multiplier).split('#')[0].strip())
            high_multiplier = float(str(self.risk_params.high_confidence_multiplier).split('#')[0].strip())
            medium_multiplier = float(str(self.risk_params.medium_confidence_multiplier).split('#')[0].strip())
            
            if confidence >= ultra_high_threshold:
                return ultra_high_multiplier
            elif confidence >= high_threshold:
                return high_multiplier
            elif confidence >= medium_threshold:
                return medium_multiplier
            else:
                return 1.0
        except (TypeError, ValueError) as e:
            log.warning(f"Error in confidence calculation, using default: {e}")
            # Use default multipliers
            if confidence >= 0.95:
                return 1.5
            elif confidence >= 0.90:
                return 1.2
            elif confidence >= 0.85:
                return 1.0
            else:
                return 1.0
    
    def _get_profit_scaling_multiplier(self) -> float:
        """Get profit-based scaling multiplier for position sizing (NEW FEATURE)"""
        if not self.account_metrics:
            return 1.0
        
        # Calculate profit percentage from initial capital
        # Assuming initial capital was $10,000 (can be made configurable)
        initial_capital = 10000.0
        current_value = self.account_metrics.total_account_value
        profit_pct = (current_value - initial_capital) / initial_capital
        
        # Scale position sizes based on profit growth
        if profit_pct >= 1.0:  # 100%+ profit
            scaling_multiplier = 2.0  # Double position sizes
        elif profit_pct >= 0.5:  # 50%+ profit
            scaling_multiplier = 1.5  # 1.5x position sizes
        elif profit_pct >= 0.25:  # 25%+ profit
            scaling_multiplier = 1.25  # 1.25x position sizes
        elif profit_pct >= 0.1:  # 10%+ profit
            scaling_multiplier = 1.1  # 1.1x position sizes
        else:
            scaling_multiplier = 1.0  # No scaling for small profits or losses
        
        log.debug(f"Profit scaling multiplier: {profit_pct:.1%} profit -> {scaling_multiplier:.2f}x scaling")
        return scaling_multiplier
    
    def _get_strategy_agreement_bonus(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> float:
        """Get strategy agreement bonus for position sizing"""
        # Get strategy agreement level from market data
        agreement_level = market_data.get("strategy_agreement_level", "NONE")
        
        # Strategy Agreement Bonuses for Position Sizing
        agreement_bonuses = {
            'NONE': 0.0,      # 0 strategies agree
            'LOW': 0.0,       # 1 strategy agrees  
            'MEDIUM': 0.25,   # 2 strategies agree (+25%)
            'HIGH': 0.50,     # 3 strategies agree (+50%)
            'MAXIMUM': 1.00   # 4+ strategies agree (+100%)
        }
        
        return agreement_bonuses.get(agreement_level, 0.0)
    
    def _get_win_streak_multiplier(self) -> float:
        """Get win streak multiplier for position sizing"""
        # This would track consecutive wins and apply multiplier
        # For now, return 1.0 as placeholder
        return self.win_streak_multiplier
    
    
    def _final_risk_assessment(self, position_risk: PositionRisk) -> Dict[str, Any]:
        """Final risk assessment and warnings"""
        warnings = []
        recommendations = []
        risk_level = RiskLevel.LOW
        
        # Check risk percentage
        if position_risk.risk_percentage > 15.0:
            risk_level = RiskLevel.HIGH
            warnings.append(f"High risk percentage: {position_risk.risk_percentage:.2f}%")
        elif position_risk.risk_percentage > 10.0:
            risk_level = RiskLevel.MEDIUM
            warnings.append(f"Medium risk percentage: {position_risk.risk_percentage:.2f}%")
        
        # Check confidence level
        if position_risk.confidence < 0.90:
            warnings.append(f"Low confidence level: {position_risk.confidence:.3f}")
            recommendations.append("Consider waiting for higher confidence signals")
        
        # Check risk-reward ratio
        if position_risk.risk_reward_ratio < 1.5:
            warnings.append(f"Low risk-reward ratio: {position_risk.risk_reward_ratio:.2f}")
            recommendations.append("Consider adjusting stop loss or take profit levels")
        
        # Check position size
        if position_risk.net_position_value < 100.0:
            warnings.append(f"Small position size: ${position_risk.net_position_value:.2f}")
            recommendations.append("Position may not be profitable after transaction costs")
        
        return {
            "risk_level": risk_level,
            "warnings": warnings,
            "recommendations": recommendations
        }
    
    async def _activate_safe_mode(self, reason: SafeModeReason):
        """Activate safe mode (Principle 7)"""
        self.safe_mode_active = True
        self.safe_mode_reason = reason
        self.safe_mode_activated_at = datetime.utcnow()
        
        log.warning(f"Safe mode activated: {reason.value}")
        
        # Send alert about safe mode activation
        await self._send_safe_mode_alert(reason)
    
    async def _deactivate_safe_mode(self):
        """Deactivate safe mode when conditions improve"""
        if self.safe_mode_active:
            self.safe_mode_active = False
            self.safe_mode_reason = None
            self.safe_mode_activated_at = None
            
            log.info("Safe mode deactivated")
            
            # Send alert about safe mode deactivation
            await self._send_safe_mode_alert(None, deactivated=True)
    
    async def _send_safe_mode_alert(self, reason: Optional[SafeModeReason], deactivated: bool = False):
        """Send safe mode alert via Telegram"""
        try:
            from .prime_alert_manager import get_prime_alert_manager
            
            alert_manager = get_prime_alert_manager()
            
            if deactivated:
                message = "🟢 **Safe Mode Deactivated**\n\nTrading has resumed normal operations."
                urgency = "INFO"
            else:
                message = f"🔴 **Safe Mode Activated**\n\nReason: {reason.value if reason else 'Unknown'}\n\nTrading has been suspended for risk management."
                urgency = "HIGH"
            
            await alert_manager.send_alert("SAFE_MODE", message, urgency)
            
        except Exception as e:
            log.error(f"Failed to send safe mode alert: {e}")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        return {
            "account_metrics": self.account_metrics.__dict__ if self.account_metrics else None,
            "safe_mode": {
                "active": self.safe_mode_active,
                "reason": self.safe_mode_reason.value if self.safe_mode_reason else None,
                "activated_at": self.safe_mode_activated_at.isoformat() if self.safe_mode_activated_at else None
            },
            "risk_parameters": self.risk_params.__dict__,
            "performance": {
                "daily_pnl": self.daily_pnl,
                "total_pnl": self.total_pnl,
                "consecutive_losses": self.consecutive_losses,
                "consecutive_wins": self.consecutive_wins,
                "win_streak_multiplier": self.win_streak_multiplier
            },
            "positions": {
                "total": len(self.current_positions),
                "strategy": len(self.strategy_positions),
                "manual": len(self.manual_positions)
            }
        }

# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_prime_risk_manager(strategy_mode: StrategyMode = StrategyMode.STANDARD) -> PrimeRiskManager:
    """Get Prime Risk Manager instance"""
    return PrimeRiskManager(strategy_mode)
