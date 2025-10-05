"""
Mock Trading Executor for Demo Mode
Handles mock trade execution, P&L tracking, and performance simulation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os
from dataclasses import dataclass, asdict

from .prime_models import SignalQuality, SignalSide, TradeStatus
from .prime_alert_manager import PrimeAlertManager

log = logging.getLogger(__name__)

@dataclass
class MockTrade:
    """Mock trade data structure"""
    trade_id: str
    symbol: str
    side: SignalSide
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    signal_quality: SignalQuality
    confidence: float
    timestamp: datetime
    status: TradeStatus = TradeStatus.OPEN
    current_price: float = 0.0
    pnl: float = 0.0
    unrealized_pnl: float = 0.0
    trailing_stop: float = 0.0
    max_favorable: float = 0.0
    exit_price: float = 0.0
    exit_timestamp: Optional[datetime] = None
    exit_reason: str = ""

@dataclass
class MockPosition:
    """Mock position data structure"""
    symbol: str
    quantity: float
    average_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    stop_loss: float
    take_profit: float
    trailing_stop: float
    max_favorable: float

class MockTradingExecutor:
    """
    Mock trading executor for Demo Mode
    Simulates trade execution, P&L tracking, and stealth trailing stops
    """
    
    def __init__(self, alert_manager: Optional[PrimeAlertManager] = None):
        self.alert_manager = alert_manager
        self.active_trades: Dict[str, MockTrade] = {}
        self.closed_trades: List[MockTrade] = []
        self.positions: Dict[str, MockPosition] = {}
        self.total_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.mock_data_file = "data/mock_trading_history.json"
        
        # Load existing mock trading data
        self._load_mock_data()
        
    def _load_mock_data(self):
        """Load existing mock trading data from file"""
        try:
            if os.path.exists(self.mock_data_file):
                with open(self.mock_data_file, 'r') as f:
                    data = json.load(f)
                    
                self.total_pnl = data.get('total_pnl', 0.0)
                self.total_trades = data.get('total_trades', 0)
                self.winning_trades = data.get('winning_trades', 0)
                self.losing_trades = data.get('losing_trades', 0)
                
                # Load closed trades
                for trade_data in data.get('closed_trades', []):
                    trade = MockTrade(**trade_data)
                    trade.timestamp = datetime.fromisoformat(trade_data['timestamp'])
                    if trade_data.get('exit_timestamp'):
                        trade.exit_timestamp = datetime.fromisoformat(trade_data['exit_timestamp'])
                    self.closed_trades.append(trade)
                    
                log.info(f"Loaded mock trading data: {self.total_trades} trades, P&L: ${self.total_pnl:.2f}")
                
        except json.JSONDecodeError as e:
            log.warning(f"Invalid JSON in mock trading data file: {e}")
            # Reset to empty state
            self.total_trades = 0
            self.total_pnl = 0.0
            self.winning_trades = 0
            self.losing_trades = 0
            self.closed_trades = []
        except Exception as e:
            log.warning(f"Failed to load mock trading data: {e}")
            # Reset to empty state
            self.total_trades = 0
            self.total_pnl = 0.0
            self.winning_trades = 0
            self.losing_trades = 0
            self.closed_trades = []
            
    def _save_mock_data(self):
        """Save mock trading data to file"""
        try:
            os.makedirs(os.path.dirname(self.mock_data_file), exist_ok=True)
            
            data = {
                'total_pnl': self.total_pnl,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'closed_trades': []
            }
            
            # Save closed trades
            for trade in self.closed_trades:
                trade_dict = asdict(trade)
                # Convert enums to strings for JSON serialization
                if 'side' in trade_dict and hasattr(trade_dict['side'], 'value'):
                    trade_dict['side'] = trade_dict['side'].value
                if 'signal_quality' in trade_dict and hasattr(trade_dict['signal_quality'], 'value'):
                    trade_dict['signal_quality'] = trade_dict['signal_quality'].value
                if 'status' in trade_dict and hasattr(trade_dict['status'], 'value'):
                    trade_dict['status'] = trade_dict['status'].value
                trade_dict['timestamp'] = trade.timestamp.isoformat()
                if trade.exit_timestamp:
                    trade_dict['exit_timestamp'] = trade.exit_timestamp.isoformat()
                data['closed_trades'].append(trade_dict)
                
            with open(self.mock_data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            log.error(f"Failed to save mock trading data: {e}")
    
    async def execute_mock_trade(self, signal, market_data: List[Dict]) -> Optional[MockTrade]:
        """
        Execute a mock trade based on signal
        """
        try:
            # CRITICAL: Check market hours before executing mock trades
            from .prime_market_manager import get_prime_market_manager
            market_manager = get_prime_market_manager()
            if not market_manager.is_market_open():
                log.warning(f"🚫 Mock Trading: Market is closed, rejecting mock trade for {signal.symbol}")
                return None
            
            # Generate mock trade ID
            trade_id = f"MOCK_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{signal.symbol}"
            
            # Calculate position size using Demo Risk Manager (if available)
            quantity = 100  # Default fallback
            
            # Try to get position size from Demo Risk Manager
            try:
                from .prime_demo_risk_manager import get_prime_demo_risk_manager
                demo_risk_manager = get_prime_demo_risk_manager()
                
                # Create market data for risk assessment
                market_data_dict = {
                    'price': signal.price,
                    'atr': signal.price * 0.02,  # Default 2% ATR
                    'volume_ratio': 1.0,
                    'momentum': 0.0,
                    'volatility': 0.01
                }
                
                # Assess risk and get position size
                risk_decision = await demo_risk_manager.assess_risk(signal, market_data_dict)
                
                if risk_decision.approved and risk_decision.position_size:
                    # Extract quantity from PositionRisk object
                    quantity = risk_decision.position_size.quantity
                    log.info(f"🎮 Demo Risk Manager: Position size {quantity} shares approved")
                else:
                    log.warning(f"🎮 Demo Risk Manager: Position rejected - {risk_decision.reason}")
                    return None
                    
            except Exception as e:
                log.warning(f"Demo Risk Manager not available, using fallback position sizing: {e}")
                
                # Fallback to quality-based sizing
                quality_multiplier = {
                    SignalQuality.ULTRA_HIGH: 1.5,
                    SignalQuality.VERY_HIGH: 1.3,
                    SignalQuality.HIGH: 1.1,
                    SignalQuality.MEDIUM: 1.0,
                    SignalQuality.LOW: 0.8
                }
                
                quantity = 100 * quality_multiplier.get(signal.quality, 1.0)
            
            # Calculate stop loss and take profit based on signal price
            entry_price = signal.price
            stop_loss = entry_price * 0.95  # 5% stop loss
            take_profit = entry_price * 1.15  # 15% take profit
            
            # Create mock trade
            mock_trade = MockTrade(
                trade_id=trade_id,
                symbol=signal.symbol,
                side=signal.side,
                entry_price=entry_price,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit,
                signal_quality=signal.quality,
                confidence=signal.confidence,
                timestamp=datetime.now(),
                current_price=entry_price,
                trailing_stop=stop_loss,
                max_favorable=entry_price
            )
            
            # Add to active trades
            self.active_trades[trade_id] = mock_trade
            
            # Notify Demo Risk Manager of new position for tracking
            try:
                from .prime_demo_risk_manager import get_prime_demo_risk_manager
                demo_risk_manager = get_prime_demo_risk_manager()
                demo_risk_manager.update_mock_position(
                    signal.symbol,
                    {
                        'symbol': signal.symbol,
                        'quantity': quantity,
                        'entry_price': entry_price,
                        'value': quantity * entry_price,
                        'source': 'strategy'
                    }
                )
                log.info(f"🎮 Demo Risk Manager notified of new position: {signal.symbol}")
            except Exception as e:
                log.warning(f"Could not notify Demo Risk Manager: {e}")
            
            # Update position
            await self._update_position(mock_trade)
            
            # Send mock execution alert
            if self.alert_manager:
                try:
                    # Try to send trade execution alert if method exists
                    if hasattr(self.alert_manager, 'send_trade_execution_alert'):
                        # Normalize side for consistent alert display
                        side_value = signal.side.value.upper()
                        if side_value in ["LONG", "BUY"]:
                            normalized_side = "BUY"
                        elif side_value in ["SHORT", "SELL"]:
                            normalized_side = "SELL"
                        else:
                            normalized_side = side_value
                        
                        await self.alert_manager.send_trade_execution_alert(
                            symbol=signal.symbol,
                            side=normalized_side,
                            price=entry_price,
                            quantity=quantity,
                            trade_id=trade_id,
                            mode="DEMO_MODE"
                        )
                    else:
                        # Fallback to general alert
                        alert_message = f"🎮 DEMO BUY: {signal.symbol} @ ${entry_price:.2f} (Qty: {quantity}, ID: {trade_id})"
                        await self.alert_manager.send_alert(
                            alert_type="trade_execution",
                            level="info",
                            title="Demo Trade Executed",
                            message=alert_message
                        )
                except Exception as e:
                    log.warning(f"Failed to send trade execution alert: {e}")
            
            log.info(f"Mock trade executed: {signal.symbol} {signal.side.value} at ${entry_price}")
            
            return mock_trade
            
        except Exception as e:
            log.error(f"Failed to execute mock trade: {e}")
            return None
    
    async def update_mock_trades(self, market_prices: Dict[str, float]):
        """
        Update all active mock trades with current market prices
        """
        try:
            trades_to_close = []
            
            for trade_id, trade in self.active_trades.items():
                if trade.symbol in market_prices:
                    trade.current_price = market_prices[trade.symbol]
                    
                    # Calculate unrealized P&L
                    if trade.side == SignalSide.BUY:
                        trade.unrealized_pnl = (trade.current_price - trade.entry_price) * trade.quantity
                    else:
                        trade.unrealized_pnl = (trade.entry_price - trade.current_price) * trade.quantity
                    
                    # Update trailing stop (stealth trailing)
                    await self._update_trailing_stop(trade)
                    
                    # Check exit conditions
                    exit_reason = await self._check_exit_conditions(trade)
                    if exit_reason:
                        trades_to_close.append((trade_id, exit_reason))
            
            # Close trades that hit exit conditions
            for trade_id, exit_reason in trades_to_close:
                await self._close_mock_trade(trade_id, exit_reason)
                
        except Exception as e:
            log.error(f"Failed to update mock trades: {e}")
    
    async def _update_trailing_stop(self, trade: MockTrade):
        """
        Update trailing stop using stealth trailing logic
        """
        try:
            if trade.side == SignalSide.BUY:
                # For long positions
                if trade.current_price > trade.max_favorable:
                    trade.max_favorable = trade.current_price
                    
                    # Stealth trailing: move stop loss closer as price moves favorably
                    favorable_move = trade.max_favorable - trade.entry_price
                    trailing_distance = trade.entry_price * 0.02  # 2% trailing distance
                    
                    if favorable_move > trailing_distance:
                        new_trailing_stop = trade.max_favorable - trailing_distance
                        if new_trailing_stop > trade.trailing_stop:
                            trade.trailing_stop = new_trailing_stop
                            log.info(f"Updated trailing stop for {trade.symbol}: ${trade.trailing_stop:.2f}")
            else:
                # For short positions
                if trade.current_price < trade.max_favorable:
                    trade.max_favorable = trade.current_price
                    
                    favorable_move = trade.entry_price - trade.max_favorable
                    trailing_distance = trade.entry_price * 0.02
                    
                    if favorable_move > trailing_distance:
                        new_trailing_stop = trade.max_favorable + trailing_distance
                        if new_trailing_stop < trade.trailing_stop:
                            trade.trailing_stop = new_trailing_stop
                            log.info(f"Updated trailing stop for {trade.symbol}: ${trade.trailing_stop:.2f}")
                            
        except Exception as e:
            log.error(f"Failed to update trailing stop: {e}")
    
    async def _check_exit_conditions(self, trade: MockTrade) -> Optional[str]:
        """
        Check if trade should be closed based on exit conditions
        """
        try:
            if trade.side == SignalSide.BUY:
                # Check stop loss
                if trade.current_price <= trade.trailing_stop:
                    return "Stop Loss Hit"
                
                # Check take profit
                if trade.current_price >= trade.take_profit:
                    return "Take Profit Hit"
            else:
                # Check stop loss
                if trade.current_price >= trade.trailing_stop:
                    return "Stop Loss Hit"
                
                # Check take profit
                if trade.current_price <= trade.take_profit:
                    return "Take Profit Hit"
            
            return None
            
        except Exception as e:
            log.error(f"Failed to check exit conditions: {e}")
            return None
    
    async def _close_mock_trade(self, trade_id: str, exit_reason: str):
        """
        Close a mock trade
        """
        try:
            if trade_id not in self.active_trades:
                return
            
            trade = self.active_trades[trade_id]
            trade.status = TradeStatus.CLOSED
            trade.exit_price = trade.current_price
            trade.exit_timestamp = datetime.now()
            trade.exit_reason = exit_reason
            trade.pnl = trade.unrealized_pnl
            
            # Update statistics
            self.total_trades += 1
            self.total_pnl += trade.pnl
            
            if trade.pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            # Move to closed trades
            self.closed_trades.append(trade)
            del self.active_trades[trade_id]
            
            # Notify Demo Risk Manager of trade closure for account growth
            try:
                from .prime_demo_risk_manager import get_prime_demo_risk_manager
                demo_risk_manager = get_prime_demo_risk_manager()
                demo_risk_manager.process_trade_close(trade.symbol, trade.exit_price, trade.quantity, trade.pnl)
                log.info(f"🎮 Demo Risk Manager notified of trade closure: {trade.symbol} - P&L: ${trade.pnl:.2f}")
            except Exception as e:
                log.warning(f"Could not notify Demo Risk Manager: {e}")
            
            # Update position
            await self._update_position(trade, closed=True)
            
            # Send exit alert
            if self.alert_manager:
                try:
                    # Try to send trade exit alert if method exists
                    if hasattr(self.alert_manager, 'send_trade_exit_alert'):
                        await self.alert_manager.send_trade_exit_alert(
                            symbol=trade.symbol,
                            side=trade.side.value,
                            entry_price=trade.entry_price,
                            exit_price=trade.exit_price,
                            quantity=trade.quantity,
                            pnl=trade.pnl,
                            exit_reason=exit_reason,
                            trade_id=trade_id,
                                mode="DEMO_MODE"
                        )
                    else:
                        # Fallback to general alert
                        alert_message = f"🎮 DEMO EXIT: {trade.symbol} @ ${trade.exit_price:.2f} (P&L: ${trade.pnl:.2f}, {exit_reason})"
                        await self.alert_manager.send_alert(
                            alert_type="trade_exit",
                            level="info",
                            title="Demo Trade Closed",
                            message=alert_message
                        )
                except Exception as e:
                    log.warning(f"Failed to send trade exit alert: {e}")
            
            # Save data
            self._save_mock_data()
            
            log.info(f"Mock trade closed: {trade.symbol} {trade.side.value} - P&L: ${trade.pnl:.2f} ({exit_reason})")
            
            return trade
            
        except Exception as e:
            log.error(f"Failed to close mock trade: {e}")
            return None
    
    async def _update_position(self, trade: MockTrade, closed: bool = False):
        """
        Update position based on trade
        """
        try:
            symbol = trade.symbol
            
            if closed:
                # Remove from positions if quantity becomes zero
                if symbol in self.positions:
                    position = self.positions[symbol]
                    if position.quantity == trade.quantity:
                        del self.positions[symbol]
                    else:
                        position.quantity -= trade.quantity
                        position.realized_pnl += trade.pnl
            else:
                # Add to positions
                if symbol not in self.positions:
                    self.positions[symbol] = MockPosition(
                        symbol=symbol,
                        quantity=0.0,
                        average_price=0.0,
                        current_price=trade.current_price,
                        unrealized_pnl=0.0,
                        realized_pnl=0.0,
                        stop_loss=trade.stop_loss,
                        take_profit=trade.take_profit,
                        trailing_stop=trade.trailing_stop,
                        max_favorable=trade.max_favorable
                    )
                
                position = self.positions[symbol]
                total_value = (position.quantity * position.average_price) + (trade.quantity * trade.entry_price)
                position.quantity += trade.quantity
                position.average_price = total_value / position.quantity
                position.current_price = trade.current_price
                position.unrealized_pnl += trade.unrealized_pnl
                
        except Exception as e:
            log.error(f"Failed to update position: {e}")
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary
        """
        try:
            total_trades = len(self.closed_trades)
            win_rate = (self.winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate additional metrics
            total_return = self.total_pnl / 10000 if self.total_pnl > 0 else 0  # Assuming $10k starting capital
            
            avg_win = 0
            avg_loss = 0
            
            if self.winning_trades > 0:
                wins = [t.pnl for t in self.closed_trades if t.pnl > 0]
                avg_win = sum(wins) / len(wins) if wins else 0
            
            if self.losing_trades > 0:
                losses = [t.pnl for t in self.closed_trades if t.pnl < 0]
                avg_loss = sum(losses) / len(losses) if losses else 0
            
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            
            return {
                'total_trades': total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': win_rate,
                'total_pnl': self.total_pnl,
                'total_return': total_return,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'active_positions': len(self.active_trades),
                'active_trades': len(self.positions)
            }
            
        except Exception as e:
            log.error(f"Failed to get performance summary: {e}")
            return {}
    
    def get_active_positions(self) -> Dict[str, Any]:
        """
        Get active mock positions for Demo Mode
        """
        try:
            active_positions = {}
            for trade_id, trade in self.active_trades.items():
                if trade.status == TradeStatus.OPEN:
                    active_positions[trade_id] = {
                        'symbol': trade.symbol,
                        'side': trade.side,
                        'quantity': trade.quantity,
                        'entry_price': trade.entry_price,
                        'current_price': trade.current_price,
                        'unrealized_pnl': trade.unrealized_pnl,
                        'status': trade.status,
                        'entry_time': trade.timestamp
                    }
            return active_positions
        except Exception as e:
            log.error(f"Failed to get active positions: {e}")
            return {}
    
    async def generate_end_of_day_report(self) -> str:
        """
        Generate end-of-day trading report
        """
        try:
            summary = await self.get_performance_summary()
            
            report = f"""
📊 **END-OF-DAY TRADING REPORT (DEMO MODE)**

📈 **Performance Summary:**
• Total Trades: {summary.get('total_trades', 0)}
• Winning Trades: {summary.get('winning_trades', 0)}
• Losing Trades: {summary.get('losing_trades', 0)}
• Win Rate: {summary.get('win_rate', 0):.1f}%

💰 **P&L Summary:**
• Total P&L: ${summary.get('total_pnl', 0):.2f}
• Total Return: {summary.get('total_return', 0):.2%}
• Average Win: ${summary.get('avg_win', 0):.2f}
• Average Loss: ${summary.get('avg_loss', 0):.2f}
• Profit Factor: {summary.get('profit_factor', 0):.2f}

🎯 **Active Positions:**
• Open Trades: {summary.get('active_positions', 0)}
• Active Positions: {summary.get('active_trades', 0)}

📅 **Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎮 **Mode:** Demo Mock Trading
"""
            
            return report
            
        except Exception as e:
            log.error(f"Failed to generate end-of-day report: {e}")
            return "Error generating report"
