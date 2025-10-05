#!/usr/bin/env python3
"""
Prime Demo Risk Manager
======================

Demo Mode Risk Manager providing identical risk management functionality
to the Prime Risk Manager but using simulated account data instead of
real E*TRADE API calls.

Key Features:
- Simulated account balance and cash management
- Identical position sizing logic to Live Mode
- Risk parameter validation and enforcement
- Mock account metrics and performance tracking
- Safe Mode activation for Demo Mode
- Position limits and portfolio risk management
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

log = logging.getLogger("prime_demo_risk_manager")

# ============================================================================
# ENUMS (Reused from Prime Risk Manager)
# ============================================================================

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class PositionSizingMethod(Enum):
    """Position sizing method enumeration"""
    FIXED_PERCENTAGE = "fixed_percentage"
    VOLATILITY_BASED = "volatility_based"
    CONFIDENCE_BASED = "confidence_based"
    KELLY_CRITERION = "kelly_criterion"

class SafeModeReason(Enum):
    """Safe mode activation reasons"""
    DRAWDOWN_EXCEEDED = "drawdown_exceeded"
    DAILY_LOSS_EXCEEDED = "daily_loss_exceeded"
    POSITION_LIMIT_EXCEEDED = "position_limit_exceeded"
    SYSTEM_ERROR = "system_error"
    MANUAL_OVERRIDE = "manual_override"

# ============================================================================
# DATA STRUCTURES (Reused from Prime Risk Manager)
# ============================================================================

@dataclass
class RiskParameters:
    """Dynamic risk parameters - identical to Live Mode"""
    # Core risk limits
    max_risk_per_trade_pct: float = 10.0
    cash_reserve_pct: float = 20.0
    trading_cash_pct: float = 80.0
    max_drawdown_pct: float = 10.0
    max_daily_loss_pct: float = 5.0
    
    # Position limits
    max_concurrent_positions: int = 20
    max_positions_per_strategy: int = 5
    max_daily_trades: int = 200
    
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
    base_position_size_pct: float = 10.0
    max_position_size_pct: float = 35.0
    
    # Transaction costs
    transaction_cost_pct: float = 0.5
    
    # Stop management
    stop_loss_atr_multiplier: float = 1.5
    take_profit_atr_multiplier: float = 2.0

@dataclass
class AccountMetrics:
    """Account metrics for risk assessment - identical to Live Mode"""
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
    """Position risk assessment - IDENTICAL to Live Mode"""
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

@dataclass
class RiskDecision:
    """Risk decision result - IDENTICAL to Live Mode"""
    approved: bool
    reason: str
    risk_level: RiskLevel
    position_size: Optional[PositionRisk] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    safe_mode_triggered: bool = False
    safe_mode_reason: Optional[SafeModeReason] = None
    warnings: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

# ============================================================================
# PRIME DEMO RISK MANAGER
# ============================================================================

class PrimeDemoRiskManager:
    """
    Demo Mode Risk Manager providing identical functionality to Prime Risk Manager
    but using simulated account data instead of real E*TRADE API calls.
    """
    
    def __init__(self, strategy_mode: StrategyMode = StrategyMode.STANDARD):
        self.strategy_mode = strategy_mode
        self.config = get_strategy_config(strategy_mode)
        self.risk_params = self._load_risk_parameters()
        
        # Mock account data - Start with $1,000 for realistic Demo Mode
        self.mock_account_balance = 1000.0  # Starting with $1k for realistic growth
        self.mock_initial_balance = 1000.0  # Track initial balance
        self.mock_positions: Dict[str, Any] = {}
        
        # Risk tracking
        self.current_positions: Dict[str, Any] = {}
        self.strategy_positions: Dict[str, Any] = {}
        self.manual_positions: Dict[str, Any] = {}
        self.position_history: deque = deque(maxlen=1000)
        
        # Performance tracking
        self.daily_pnl: float = 0.0
        self.total_pnl: float = 0.0
        self.consecutive_losses: int = 0
        self.consecutive_wins: int = 0
        self.win_streak_multiplier: float = 1.0
        self.winning_trades: int = 0
        self.losing_trades: int = 0
        
        # Safe mode
        self.safe_mode_active: bool = False
        self.safe_mode_reason: Optional[SafeModeReason] = None
        self.safe_mode_activated_at: Optional[datetime] = None
        
        # Account metrics
        self.account_metrics: Optional[AccountMetrics] = None
        
        log.info(f"PrimeDemoRiskManager initialized for {strategy_mode.value} strategy")
        log.info(f"🎮 Demo Mode: Starting with ${self.mock_account_balance:,.2f} simulated balance")
        log.info(f"🎯 Demo Mode: Account will grow with profitable trades - starting small for realistic growth!")
    
    def _load_risk_parameters(self) -> RiskParameters:
        """Load risk parameters from configuration - identical to Live Mode"""
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
    
    async def assess_risk(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> RiskDecision:
        """
        Comprehensive risk assessment for opening a new position - IDENTICAL to Live Mode.
        Implements all 10 core risk management principles.
        """
        try:
            log.info(f"🎮 Assessing Demo risk for {signal.symbol} position")
            
            # 1. Check Safe Mode status
            if self.safe_mode_active:
                return RiskDecision(
                    approved=False,
                    reason=f"Safe mode active: {self.safe_mode_reason.value if self.safe_mode_reason else 'unknown'}",
                    risk_level=RiskLevel.HIGH,
                    safe_mode_triggered=True,
                    safe_mode_reason=self.safe_mode_reason
                )
            
            # 2. Load current mock account metrics
            await self._update_mock_account_metrics()
            if not self.account_metrics:
                return RiskDecision(
                    approved=False,
                    reason="Unable to load mock account metrics",
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
                await self._activate_safe_mode(SafeModeReason.DAILY_LOSS_EXCEEDED)
                return RiskDecision(
                    approved=False,
                    reason=daily_loss_check["reason"],
                    risk_level=RiskLevel.HIGH,
                    safe_mode_triggered=True,
                    safe_mode_reason=SafeModeReason.DAILY_LOSS_EXCEEDED
                )
            
            # 5. Check position limits (Principle 7)
            position_limit_check = self._check_position_limits()
            if not position_limit_check["approved"]:
                return RiskDecision(
                    approved=False,
                    reason=position_limit_check["reason"],
                    risk_level=RiskLevel.MEDIUM
                )
            
            # 6. Check news sentiment filtering (Principle 5) - Demo Mode placeholder
            sentiment_check = self._check_news_sentiment(signal, market_data)
            if not sentiment_check["approved"]:
                return RiskDecision(
                    approved=False,
                    reason=sentiment_check["reason"],
                    risk_level=RiskLevel.MEDIUM
                )
            
            # 7. Calculate dynamic position sizing (Principle 4) - IDENTICAL to Live Mode
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
            
            # 10. Create approved risk decision - IDENTICAL to Live Mode
            return RiskDecision(
                approved=True,
                reason="Position approved after comprehensive risk assessment",
                risk_level=final_risk_assessment["risk_level"],
                position_size=position_sizing["position_risk"],
                warnings=final_risk_assessment["warnings"],
                recommendations=final_risk_assessment["recommendations"]
            )
            
        except Exception as e:
            log.error(f"🎮 Demo risk assessment failed for {signal.symbol}: {e}")
            return RiskDecision(
                approved=False,
                reason=f"Risk assessment error: {str(e)}",
                risk_level=RiskLevel.HIGH
            )
    
    async def _update_mock_account_metrics(self):
        """Update mock account metrics - simulates Live Mode account data"""
        try:
            # Calculate current account value including ONLY strategy positions
            strategy_positions = [pos for pos in self.mock_positions.values() if pos.get('source') == 'strategy']
            total_strategy_position_value = sum(pos.get('value', 0) for pos in strategy_positions)
            
            # Total account value = cash + strategy positions only (ignore manual/other positions)
            total_account_value = self.mock_account_balance + total_strategy_position_value
            
            # Calculate cash allocation - ONLY use available cash, not total account value
            cash_reserve = self.mock_account_balance * (self.risk_params.cash_reserve_pct / 100.0)
            trading_cash = self.mock_account_balance * (self.risk_params.trading_cash_pct / 100.0)
            
            # Calculate drawdown from peak (using strategy-only account value)
            current_drawdown_pct = 0.0
            if hasattr(self, 'peak_capital') and self.peak_capital > 0:
                current_drawdown_pct = max(0.0, (self.peak_capital - total_account_value) / self.peak_capital)
            
            # Update peak capital
            if not hasattr(self, 'peak_capital') or total_account_value > self.peak_capital:
                self.peak_capital = total_account_value
            
            self.account_metrics = AccountMetrics(
                available_cash=self.mock_account_balance,  # Only available cash
                total_account_value=total_account_value,   # Cash + strategy positions only
                cash_reserve=cash_reserve,
                trading_cash=trading_cash,
                margin_available=self.mock_account_balance * 2.0,  # 2x margin for demo
                buying_power=self.mock_account_balance * 2.0,
                current_drawdown_pct=current_drawdown_pct,
                daily_pnl_pct=self.daily_pnl / total_account_value if total_account_value > 0 else 0.0,
                total_open_positions=len(strategy_positions),  # Only strategy positions
                strategy_positions=len(strategy_positions),
                manual_positions=0  # Ignore manual positions
            )
            
            log.debug(f"🎮 Demo Account: ${self.mock_account_balance:,.2f} cash, ${total_account_value:,.2f} total (strategy only)")
            log.debug(f"🎮 Strategy Positions: {len(strategy_positions)} positions, ${total_strategy_position_value:,.2f} value")
            
        except Exception as e:
            log.error(f"Failed to update mock account metrics: {e}")
    
    async def _calculate_position_sizing(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate position sizing with boosting factors and 80/20 rule - IDENTICAL to Live Mode
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
            
            # 1. Calculate base position value using PRIME SYSTEM PORTFOLIO VALUE sizing
            # For concurrent positions, distribute 80% of PRIME SYSTEM PORTFOLIO VALUE proportionally
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
            
            # 2. Apply confidence multiplier for position sizing
            confidence_multiplier = self._get_confidence_multiplier(signal.confidence)
            
            # 3. Apply strategy agreement bonus for position sizing
            agreement_bonus = self._get_strategy_agreement_bonus(signal, market_data)
            
            # 4. Apply profit-based scaling multiplier
            profit_scaling_multiplier = self._get_profit_scaling_multiplier()
            
            # 5. Apply win streak multiplier
            win_streak_multiplier = self._get_win_streak_multiplier()
            
            # 6. Apply all multipliers to calculate position value
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
            
            # Create position risk object - IDENTICAL to Live Mode
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
            
            log.info(f"🎮 Position sizing calculated for {signal.symbol}: "
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
            log.error(f"🎮 Position sizing calculation error: {e}")
            return {"approved": False, "reason": f"Position sizing calculation error: {str(e)}"}
    
    def _get_confidence_multiplier(self, confidence: float) -> float:
        """Get confidence multiplier for position sizing (Principle 6) - IDENTICAL to Live Mode"""
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
        """Get profit-based scaling multiplier for position sizing - IDENTICAL to Live Mode"""
        if not self.account_metrics:
            return 1.0
        
        # Calculate profit percentage from initial capital
        # Using mock initial balance for Demo Mode
        initial_capital = self.mock_initial_balance
        current_value = self.account_metrics.total_account_value
        profit_pct = (current_value - initial_capital) / initial_capital if initial_capital > 0 else 0
        
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
            scaling_multiplier = 1.0  # No scaling
        
        return scaling_multiplier
    
    def _get_strategy_agreement_bonus(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> float:
        """Get strategy agreement bonus for position sizing - IDENTICAL to Live Mode"""
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
        """Get win streak multiplier for position sizing - IDENTICAL to Live Mode"""
        # This tracks consecutive wins and applies multiplier
        return self.win_streak_multiplier
    
    def _check_news_sentiment(self, signal: PrimeSignal, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check news sentiment filtering (Principle 5) - Demo Mode placeholder"""
        # For Demo Mode, we'll always approve (no real news sentiment available)
        # In Live Mode, this would check actual news sentiment data
        return {"approved": True, "reason": "News sentiment check passed (Demo Mode)"}
    
    def _final_risk_assessment(self, position_risk: PositionRisk) -> Dict[str, Any]:
        """Final risk assessment and warnings - IDENTICAL to Live Mode"""
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
        if position_risk.confidence < 0.80:
            warnings.append(f"Low confidence signal: {position_risk.confidence:.2f}")
            recommendations.append("Consider waiting for higher confidence signals")
        
        # Check risk/reward ratio
        if position_risk.risk_reward_ratio < 1.5:
            warnings.append(f"Poor risk/reward ratio: {position_risk.risk_reward_ratio:.2f}")
            recommendations.append("Consider adjusting stop loss or take profit levels")
        
        return {
            "risk_level": risk_level,
            "warnings": warnings,
            "recommendations": recommendations
        }
    
    def _check_drawdown_protection(self) -> Dict[str, Any]:
        """Check drawdown protection - identical to Live Mode"""
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
        """Check daily loss limits - identical to Live Mode"""
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
        """Check position limits - identical to Live Mode"""
        if not self.account_metrics:
            return {"approved": False, "reason": "No account metrics available"}
        
        current_positions = self.account_metrics.strategy_positions
        max_positions = self.risk_params.max_concurrent_positions
        
        if current_positions >= max_positions:
            return {
                "approved": False,
                "reason": f"Position limit reached: {current_positions}/{max_positions}"
            }
        
        return {"approved": True}
    
    async def _activate_safe_mode(self, reason: SafeModeReason):
        """Activate safe mode"""
        self.safe_mode_active = True
        self.safe_mode_reason = reason
        self.safe_mode_activated_at = datetime.now()
        log.warning(f"🚨 Demo Safe Mode activated: {reason.value}")
    
    async def deactivate_safe_mode(self):
        """Deactivate safe mode"""
        self.safe_mode_active = False
        self.safe_mode_reason = None
        self.safe_mode_activated_at = None
        log.info("✅ Demo Safe Mode deactivated")
    
    def update_mock_position(self, symbol: str, position_data: Dict[str, Any]):
        """Update mock position data"""
        self.mock_positions[symbol] = position_data
        log.debug(f"🎮 Updated mock position: {symbol}")
        
        # If this is a new strategy position, deduct cash
        if position_data.get('source') == 'strategy' and 'value' in position_data:
            position_value = position_data['value']
            if position_value > 0:
                self.mock_account_balance -= position_value
                log.debug(f"🎮 Deducted ${position_value:.2f} for new position: {symbol}")
                log.debug(f"🎮 New cash balance: ${self.mock_account_balance:.2f}")
    
    def remove_mock_position(self, symbol: str):
        """Remove mock position"""
        if symbol in self.mock_positions:
            del self.mock_positions[symbol]
            log.debug(f"🎮 Removed mock position: {symbol}")
    
    def process_trade_close(self, symbol: str, exit_price: float, quantity: float, pnl: float):
        """
        Process trade closing and update account balance
        
        Args:
            symbol: Symbol of the closed trade
            exit_price: Exit price of the trade
            quantity: Quantity of shares
            pnl: Profit or loss from the trade
        """
        try:
            if symbol in self.mock_positions:
                # Get position data before removing
                position_data = self.mock_positions[symbol]
                position_value = position_data.get('value', 0)
                
                # Remove position
                del self.mock_positions[symbol]
                
                # Add back the original position value + P&L
                self.mock_account_balance += position_value + pnl
                
                # Update performance tracking
                self.daily_pnl += pnl
                self.total_pnl += pnl
                
                if pnl > 0:
                    self.winning_trades += 1
                    self.consecutive_wins += 1
                    self.consecutive_losses = 0
                else:
                    self.losing_trades += 1
                    self.consecutive_losses += 1
                    self.consecutive_wins = 0
                
                # Update win streak multiplier
                if self.consecutive_wins >= 3:
                    self.win_streak_multiplier = min(2.0, 1.0 + (self.consecutive_wins * 0.1))
                else:
                    self.win_streak_multiplier = 1.0
                
                log.info(f"🎮 Demo Trade Closed: {symbol} - P&L: ${pnl:.2f} - New Balance: ${self.mock_account_balance:.2f}")
                
                # Check if account has grown significantly
                growth_pct = ((self.mock_account_balance - self.mock_initial_balance) / self.mock_initial_balance) * 100
                if growth_pct > 10:  # More than 10% growth
                    log.info(f"🚀 Demo Account Growth: {growth_pct:.1f}% from initial ${self.mock_initial_balance:.2f}")
                
                return True
            else:
                log.warning(f"Demo position {symbol} not found for closing")
                return False
                
        except Exception as e:
            log.error(f"Error processing demo trade close: {e}")
            return False
    
    def get_mock_account_summary(self) -> Dict[str, Any]:
        """Get mock account summary"""
        current_value = self.mock_account_balance + sum(pos.get('value', 0) for pos in self.mock_positions.values())
        growth_pct = ((current_value - self.mock_initial_balance) / self.mock_initial_balance) * 100 if self.mock_initial_balance > 0 else 0
        
        return {
            'mock_balance': self.mock_account_balance,
            'mock_positions': len(self.mock_positions),
            'mock_total_value': current_value,
            'mock_initial_balance': self.mock_initial_balance,
            'growth_percentage': growth_pct,
            'total_pnl': self.total_pnl,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': (self.winning_trades / (self.winning_trades + self.losing_trades)) * 100 if (self.winning_trades + self.losing_trades) > 0 else 0,
            'safe_mode_active': self.safe_mode_active,
            'safe_mode_reason': self.safe_mode_reason.value if self.safe_mode_reason else None
        }

# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def get_prime_demo_risk_manager(strategy_mode: StrategyMode = StrategyMode.STANDARD) -> PrimeDemoRiskManager:
    """Get Prime Demo Risk Manager instance"""
    return PrimeDemoRiskManager(strategy_mode)

def create_demo_risk_manager(strategy_mode: StrategyMode = StrategyMode.STANDARD) -> PrimeDemoRiskManager:
    """Create new Prime Demo Risk Manager instance"""
    return PrimeDemoRiskManager(strategy_mode)
