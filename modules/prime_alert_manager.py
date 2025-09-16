#!/usr/bin/env python3
"""
Prime Alert Manager
==================

Comprehensive alert management system for the V2 ETrade Strategy.
Handles all Telegram notifications for trade signals, performance updates,
and end-of-day summaries.

Key Features:
- Trade signal alerts (entry/exit notifications)
- Performance monitoring alerts
- End-of-day trade summaries
- System status notifications
- Error and warning alerts
- Configurable alert levels and throttling
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import requests
from collections import defaultdict, deque
import threading

try:
    from .config_loader import get_config_value
except ImportError:
    # Fallback for direct imports
    def get_config_value(key, default=''):
        import os
        return os.getenv(key, default)

log = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert level enumeration"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SUCCESS = "success"

class AlertType(Enum):
    """Alert type enumeration"""
    TRADE_SIGNAL = "trade_signal"
    TRADE_ENTRY = "trade_entry"
    TRADE_EXIT = "trade_exit"
    PERFORMANCE_UPDATE = "performance_update"
    END_OF_DAY_SUMMARY = "end_of_day_summary"
    SYSTEM_STATUS = "system_status"
    ERROR = "error"
    WARNING = "warning"
    MARKET_ALERT = "market_alert"
    # OAuth Token Management Alerts
    OAUTH_RENEWAL = "oauth_renewal"
    OAUTH_SUCCESS = "oauth_success"
    OAUTH_ERROR = "oauth_error"
    OAUTH_WARNING = "oauth_warning"

@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    alert_type: AlertType
    level: AlertLevel
    title: str
    message: str
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    confidence: Optional[float] = None
    expected_return: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TradeAlert:
    """Trade-specific alert data structure"""
    symbol: str
    strategy: str
    action: str  # "BUY" or "SELL"
    price: float
    quantity: int
    confidence: float
    expected_return: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PerformanceSummary:
    """End-of-day performance summary"""
    date: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    daily_return: float
    active_positions: int
    signals_generated: int
    signals_accepted: int
    acceptance_rate: float
    top_performers: List[Dict[str, Any]] = field(default_factory=list)
    worst_performers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Additional metrics for enhanced reporting
    max_drawdown: float = 0.0
    capital_used_pct: float = 0.0
    consecutive_wins: int = 0
    avg_risk_per_trade: float = 4.2
    total_pnl_dollars: float = 0.0

@dataclass
class OAuthAlert:
    """OAuth-specific alert data structure"""
    environment: str  # "prod" or "sandbox"
    alert_type: str  # "renewal", "success", "error", "warning"
    message: str
    oauth_url: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class PrimeAlertManager:
    """Prime Alert Manager for comprehensive notification system"""
    
    def __init__(self):
        self.name = "Prime Alert Manager"
        self.version = "1.0"
        
        # Telegram configuration
        self.telegram_bot_token = get_config_value('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = get_config_value('TELEGRAM_CHAT_ID', '')
        self.telegram_enabled = get_config_value('TELEGRAM_ALERTS_ENABLED', 'true').lower() == 'true'
        
        # Alert configuration
        self.alert_levels_enabled = {
            AlertLevel.INFO: get_config_value('ALERT_LEVEL_INFO', 'true').lower() == 'true',
            AlertLevel.WARNING: get_config_value('ALERT_LEVEL_WARNING', 'true').lower() == 'true',
            AlertLevel.ERROR: get_config_value('ALERT_LEVEL_ERROR', 'true').lower() == 'true',
            AlertLevel.CRITICAL: get_config_value('ALERT_LEVEL_CRITICAL', 'true').lower() == 'true',
            AlertLevel.SUCCESS: get_config_value('ALERT_LEVEL_SUCCESS', 'true').lower() == 'true'
        }
        
        # Throttling configuration
        self.max_alerts_per_minute = int(get_config_value('TELEGRAM_MAX_MESSAGES_PER_MINUTE', '20'))
        self.alert_cooldown_seconds = int(get_config_value('ALERT_COOLDOWN_SECONDS', '30'))
        
        # Alert tracking
        self.alert_history = deque(maxlen=1000)
        self.alert_counts = defaultdict(int)
        self.last_alert_time = defaultdict(float)
        
        # Performance tracking
        self.daily_performance = {}
        self.trade_history = []
        
        # End of day scheduling
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # OAuth configuration
        self.oauth_enabled = get_config_value('OAUTH_ALERTS_ENABLED', 'true').lower() == 'true'
        self.oauth_renewal_url = get_config_value('OAUTH_RENEWAL_URL', 'https://etrade-oauth.yourdomain.com')
        self.oauth_morning_hour = int(get_config_value('OAUTH_MORNING_HOUR', '8'))
        self.oauth_morning_minute = int(get_config_value('OAUTH_MORNING_MINUTE', '30'))
        self.oauth_timezone = get_config_value('OAUTH_TIMEZONE', 'America/New_York')
        
        # OAuth tracking
        self.oauth_status = {
            'prod': {'last_renewed': None, 'is_valid': False, 'expires_at': None},
            'sandbox': {'last_renewed': None, 'is_valid': False, 'expires_at': None}
        }
        
        # System status
        self.is_initialized = False
        
        log.info(f"Prime Alert Manager v{self.version} initialized")
    
    async def initialize(self) -> bool:
        """Initialize the alert manager"""
        try:
            if self.telegram_enabled:
                # Test Telegram connection
                if await self._test_telegram_connection():
                    log.info("✅ Telegram connection successful")
                else:
                    log.warning("⚠️ Telegram connection failed")
                    self.telegram_enabled = False
            
            self.is_initialized = True
            log.info("Prime Alert Manager initialized successfully")
            return True
            
        except Exception as e:
            log.error(f"Failed to initialize alert manager: {e}")
            return False
    
    async def _test_telegram_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                return False
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    log.info(f"Telegram bot connected: @{bot_info['result']['username']}")
                    return True
            
            return False
            
        except Exception as e:
            log.error(f"Telegram connection test failed: {e}")
            return False
    
    # ========================================================================
    # TRADE ALERTS
    # ========================================================================
    
    async def send_trade_signal_alert(self, signal_data: Dict[str, Any]) -> bool:
        """Send trade signal alert"""
        try:
            alert = Alert(
                alert_id=f"signal_{signal_data.get('symbol', 'unknown')}_{int(time.time())}",
                alert_type=AlertType.TRADE_SIGNAL,
                level=AlertLevel.INFO,
                title="🎯 New Trade Signal",
                message=self._format_trade_signal_message(signal_data),
                symbol=signal_data.get('symbol'),
                strategy=signal_data.get('strategy'),
                confidence=signal_data.get('confidence'),
                expected_return=signal_data.get('expected_return'),
                metadata=signal_data
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send trade signal alert: {e}")
            return False
    
    async def send_trade_entry_alert(self, trade_data: TradeAlert) -> bool:
        """Send trade entry alert"""
        try:
            alert = Alert(
                alert_id=f"entry_{trade_data.symbol}_{int(time.time())}",
                alert_type=AlertType.TRADE_ENTRY,
                level=AlertLevel.SUCCESS,
                title="✅ Trade Executed",
                message=self._format_trade_entry_message(trade_data),
                symbol=trade_data.symbol,
                strategy=trade_data.strategy,
                confidence=trade_data.confidence,
                expected_return=trade_data.expected_return,
                metadata={
                    'action': trade_data.action,
                    'price': trade_data.price,
                    'quantity': trade_data.quantity,
                    'stop_loss': trade_data.stop_loss,
                    'take_profit': trade_data.take_profit
                }
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send trade entry alert: {e}")
            return False
    
    async def send_trade_exit_alert(self, trade_data: TradeAlert) -> bool:
        """Send trade exit alert"""
        try:
            pnl = (trade_data.price - trade_data.metadata.get('entry_price', trade_data.price)) / trade_data.metadata.get('entry_price', trade_data.price)
            pnl_pct = pnl * 100
            
            alert = Alert(
                alert_id=f"exit_{trade_data.symbol}_{int(time.time())}",
                alert_type=AlertType.TRADE_EXIT,
                level=AlertLevel.SUCCESS if pnl > 0 else AlertLevel.WARNING,
                title="🔚 Trade Closed",
                message=self._format_trade_exit_message(trade_data, pnl_pct),
                symbol=trade_data.symbol,
                strategy=trade_data.strategy,
                metadata={
                    'action': trade_data.action,
                    'price': trade_data.price,
                    'quantity': trade_data.quantity,
                    'pnl_pct': pnl_pct,
                    'reason': trade_data.reason
                }
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send trade exit alert: {e}")
            return False
    
    # ========================================================================
    # PERFORMANCE ALERTS
    # ========================================================================
    
    async def send_performance_alert(self, performance_data: Dict[str, Any]) -> bool:
        """Send performance update alert"""
        try:
            alert = Alert(
                alert_id=f"performance_{int(time.time())}",
                alert_type=AlertType.PERFORMANCE_UPDATE,
                level=AlertLevel.INFO,
                title="📊 Performance Update",
                message=self._format_performance_message(performance_data),
                metadata=performance_data
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send performance alert: {e}")
            return False
    
    async def send_end_of_day_summary(self, summary: PerformanceSummary) -> bool:
        """Send end-of-day performance summary"""
        try:
            alert = Alert(
                alert_id=f"eod_summary_{summary.date.strftime('%Y%m%d')}",
                alert_type=AlertType.END_OF_DAY_SUMMARY,
                level=AlertLevel.INFO,
                title="📈 End of Day Summary",
                message=self._format_end_of_day_message(summary),
                metadata={
                    'date': summary.date.isoformat(),
                    'total_trades': summary.total_trades,
                    'win_rate': summary.win_rate,
                    'total_pnl': summary.total_pnl,
                    'daily_return': summary.daily_return
                }
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send end-of-day summary: {e}")
            return False
    
    # ========================================================================
    # SYSTEM ALERTS
    # ========================================================================
    
    async def send_system_alert(self, title: str, message: str, level: AlertLevel = AlertLevel.INFO) -> bool:
        """Send system alert"""
        try:
            alert = Alert(
                alert_id=f"system_{int(time.time())}",
                alert_type=AlertType.SYSTEM_STATUS,
                level=level,
                title=title,
                message=message,
                metadata={'timestamp': datetime.now().isoformat()}
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send system alert: {e}")
            return False
    
    async def send_error_alert(self, error_message: str, error_type: str = "General Error") -> bool:
        """Send error alert"""
        try:
            alert = Alert(
                alert_id=f"error_{int(time.time())}",
                alert_type=AlertType.ERROR,
                level=AlertLevel.ERROR,
                title="🚨 System Error",
                message=f"**{error_type}**\n\n{error_message}",
                metadata={'error_type': error_type, 'timestamp': datetime.now().isoformat()}
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send error alert: {e}")
            return False
    
    async def send_warning_alert(self, warning_message: str, warning_type: str = "General Warning") -> bool:
        """Send warning alert"""
        try:
            alert = Alert(
                alert_id=f"warning_{int(time.time())}",
                alert_type=AlertType.WARNING,
                level=AlertLevel.WARNING,
                title="⚠️ System Warning",
                message=f"**{warning_type}**\n\n{warning_message}",
                metadata={'warning_type': warning_type, 'timestamp': datetime.now().isoformat()}
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send warning alert: {e}")
            return False
    
    # ========================================================================
    # CORE ALERT SENDING
    # ========================================================================
    
    async def _send_alert(self, alert: Alert) -> bool:
        """Send alert via configured channels"""
        try:
            # Check if alert level is enabled
            if not self.alert_levels_enabled.get(alert.level, False):
                return False
            
            # Check throttling
            if not self._check_alert_throttling(alert):
                return False
            
            # Send via Telegram if enabled
            if self.telegram_enabled:
                success = await self._send_telegram_alert(alert)
                if success:
                    self._track_alert(alert)
                    return True
            
            # Log alert if no other channels available
            log.info(f"Alert: {alert.title} - {alert.message}")
            self._track_alert(alert)
            return True
            
        except Exception as e:
            log.error(f"Failed to send alert: {e}")
            return False
    
    async def _send_telegram_alert(self, alert: Alert) -> bool:
        """Send alert via Telegram"""
        try:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                return False
            
            # Format message
            message = self._format_telegram_message(alert)
            
            # Send to Telegram
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    log.debug(f"Telegram alert sent: {alert.alert_id}")
                    return True
                else:
                    log.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
            else:
                log.error(f"Telegram HTTP error: {response.status_code}")
            
            return False
            
        except Exception as e:
            log.error(f"Failed to send Telegram alert: {e}")
            return False
    
    # ========================================================================
    # MESSAGE FORMATTING
    # ========================================================================
    
    def _format_telegram_message(self, alert: Alert) -> str:
        """Format alert for Telegram"""
        emoji_map = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "🚨",
            AlertLevel.CRITICAL: "🔥",
            AlertLevel.SUCCESS: "✅"
        }
        
        emoji = emoji_map.get(alert.level, "📢")
        timestamp = alert.timestamp.strftime("%H:%M:%S")
        
        message = f"{emoji} **{alert.title}**\n"
        message += f"🕐 {timestamp}\n\n"
        
        if alert.symbol:
            message += f"📈 **Symbol:** {alert.symbol}\n"
        
        if alert.strategy:
            message += f"🎯 **Strategy:** {alert.strategy}\n"
        
        if alert.confidence:
            message += f"🎲 **Confidence:** {alert.confidence:.1%}\n"
        
        if alert.expected_return:
            message += f"💰 **Expected Return:** {alert.expected_return:.2%}\n"
        
        message += f"\n{alert.message}"
        
        return message
    
    def _format_trade_signal_message(self, signal_data: Dict[str, Any]) -> str:
        """Format trade signal message"""
        symbol = signal_data.get('symbol', 'Unknown')
        strategy = signal_data.get('strategy', 'Unknown')
        confidence = signal_data.get('confidence', 0)
        expected_return = signal_data.get('expected_return', 0)
        entry_price = signal_data.get('entry_price', 0)
        
        message = f"**{symbol}** - {strategy} Strategy\n"
        message += f"🎯 **Entry Price:** ${entry_price:.2f}\n"
        message += f"🎲 **Confidence:** {confidence:.1%}\n"
        message += f"💰 **Expected Return:** {expected_return:.2%}\n"
        
        if signal_data.get('stop_loss'):
            message += f"🛑 **Stop Loss:** ${signal_data['stop_loss']:.2f}\n"
        
        if signal_data.get('take_profit'):
            message += f"🎯 **Take Profit:** ${signal_data['take_profit']:.2f}\n"
        
        return message
    
    def _format_trade_entry_message(self, trade_data: TradeAlert) -> str:
        """Format trade entry message"""
        message = f"**{trade_data.symbol}** - {trade_data.strategy}\n"
        message += f"✅ **{trade_data.action}** {trade_data.quantity} shares @ ${trade_data.price:.2f}\n"
        message += f"🎲 **Confidence:** {trade_data.confidence:.1%}\n"
        message += f"💰 **Expected Return:** {trade_data.expected_return:.2%}\n"
        
        if trade_data.stop_loss:
            message += f"🛑 **Stop Loss:** ${trade_data.stop_loss:.2f}\n"
        
        if trade_data.take_profit:
            message += f"🎯 **Take Profit:** ${trade_data.take_profit:.2f}\n"
        
        if trade_data.reason:
            message += f"📝 **Reason:** {trade_data.reason}\n"
        
        return message
    
    def _format_trade_exit_message(self, trade_data: TradeAlert, pnl_pct: float) -> str:
        """Format trade exit message"""
        pnl_emoji = "💰" if pnl_pct > 0 else "📉"
        
        message = f"**{trade_data.symbol}** - {trade_data.strategy}\n"
        message += f"🔚 **{trade_data.action}** {trade_data.quantity} shares @ ${trade_data.price:.2f}\n"
        message += f"{pnl_emoji} **P&L:** {pnl_pct:+.2f}%\n"
        
        if trade_data.reason:
            message += f"📝 **Reason:** {trade_data.reason}\n"
        
        return message
    
    def _format_performance_message(self, performance_data: Dict[str, Any]) -> str:
        """Format performance update message"""
        message = f"📊 **Performance Update**\n\n"
        
        if 'win_rate' in performance_data:
            message += f"🎯 **Win Rate:** {performance_data['win_rate']:.1%}\n"
        
        if 'total_pnl' in performance_data:
            message += f"💰 **Total P&L:** {performance_data['total_pnl']:.2%}\n"
        
        if 'active_positions' in performance_data:
            message += f"📈 **Active Positions:** {performance_data['active_positions']}\n"
        
        if 'daily_return' in performance_data:
            message += f"📅 **Daily Return:** {performance_data['daily_return']:.2%}\n"
        
        return message
    
    def _format_end_of_day_message(self, summary: PerformanceSummary) -> str:
        """Format end-of-day summary message with enhanced reporting"""
        # Determine performance emojis and status
        pnl_emoji = "✅" if summary.total_pnl > 0 else "📉"
        return_emoji = "📈" if summary.daily_return > 0 else "📉"
        
        # Calculate additional metrics
        avg_gain_per_trade = summary.total_pnl / summary.total_trades if summary.total_trades > 0 else 0
        max_drawdown = getattr(summary, 'max_drawdown', 0.0)
        capital_used_pct = getattr(summary, 'capital_used_pct', 0.0)
        consecutive_wins = getattr(summary, 'consecutive_wins', 0)
        
        # Calculate total P&L in dollars (approximate)
        total_pnl_dollars = getattr(summary, 'total_pnl_dollars', summary.total_pnl * 1000)  # Rough estimate
        
        message = f"⚖️ End of Day Trade Report\n"
        message += f"💹🛅 • Date: {summary.date.strftime('%Y-%m-%d')}\n\n"
        
        message += f"{pnl_emoji} {summary.total_pnl:+.2f}% ${total_pnl_dollars:+,.2f}\n"
        message += f"📈 • Total Trades: {summary.total_trades}\n"
        message += f"      • Win Rate: {summary.win_rate:.1%}\n"
        message += f"      • Max Drawdown: {max_drawdown:+.1f}%\n\n"
        
        # Highlights section
        message += f"⚡ Highlights\n"
        if consecutive_wins >= 3:
            message += f"🔰 Win streak: {consecutive_wins} consecutive wins\n"
        if summary.top_performers:
            best_trade = summary.top_performers[0]
            best_symbol = best_trade.get('symbol', 'N/A')
            best_return = best_trade.get('return', 0)
            message += f"👑 Biggest gain: {best_return:+.1f}% on {best_symbol}\n"
        message += "\n"
        
        # Risk metrics
        message += f"🛡 Risk Metrics\n"
        message += f"      • Capital Used: {capital_used_pct:.0f}%\n"
        message += f"      • Avg Gain per Trade: {avg_gain_per_trade:+.1f}%\n"
        message += f"      • Avg Risk per Trade: {getattr(summary, 'avg_risk_per_trade', 4.2):.1f}%\n\n"
        
        # Best and worst trades with detailed breakdown
        if summary.top_performers:
            best_trade = summary.top_performers[0]
            message += f"📈 Best Trade\n"
            message += f"👑 {best_trade.get('symbol', 'N/A')} ({best_trade.get('side', 'LONG')}) — "
            message += f"{best_trade.get('return', 0):+.1f}% ${best_trade.get('pnl_dollars', 0):+.2f} • "
            message += f"Duration: {best_trade.get('duration', 'N/A')}\n"
            message += f"      • Entry: {best_trade.get('entry_price', 'N/A')} @ {best_trade.get('entry_time', 'N/A')}\n"
            message += f"      • Exit: {best_trade.get('exit_price', 'N/A')} @ {best_trade.get('exit_time', 'N/A')}\n"
            message += f"      • Entry Reason: {best_trade.get('entry_reason', 'N/A')}\n"
            message += f"      • Exit Reason: {best_trade.get('exit_reason', 'N/A')}\n\n"
        
        if summary.worst_performers:
            worst_trade = summary.worst_performers[0]
            message += f"💢 Worst Trade\n"
            message += f"📛 {worst_trade.get('symbol', 'N/A')} ({worst_trade.get('side', 'SHORT')}) — "
            message += f"{worst_trade.get('return', 0):+.1f}% ${worst_trade.get('pnl_dollars', 0):+.2f} • "
            message += f"Duration: {worst_trade.get('duration', 'N/A')}\n"
            message += f"      • Entry: {worst_trade.get('entry_price', 'N/A')} @ {worst_trade.get('entry_time', 'N/A')}\n"
            message += f"      • Exit: {worst_trade.get('exit_price', 'N/A')} @ {worst_trade.get('exit_time', 'N/A')}\n"
            message += f"      • Entry Reason: {worst_trade.get('entry_reason', 'N/A')}\n"
            message += f"      • Exit Reason: {worst_trade.get('exit_reason', 'N/A')}\n\n"
        
        # Summary
        message += f"✨ Summary\n"
        if summary.win_rate >= 0.8:
            message += f"📈 Strong execution with disciplined risk. "
        elif summary.win_rate >= 0.6:
            message += f"📊 Solid performance with room for optimization. "
        else:
            message += f"⚠️ Challenging session - reviewing strategy. "
        
        if summary.total_pnl > 2.0:
            message += f"Momentum signals lined up with sentiment confluence."
        elif summary.total_pnl > 0:
            message += f"Positive day with controlled risk management."
        else:
            message += f"Risk management prevented larger losses."
        
        return message
    
    # ========================================================================
    # END OF DAY SCHEDULING
    # ========================================================================
    
    def start_end_of_day_scheduler(self):
        """Start the end-of-day summary scheduler"""
        if self.scheduler_running:
            log.warning("End-of-day scheduler is already running")
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        log.info("End-of-day scheduler started - will send summary at 4:00 PM ET (9:00 PM UTC)")
    
    def stop_end_of_day_scheduler(self):
        """Stop the end-of-day summary scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        log.info("End-of-day scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in a background thread"""
        while self.scheduler_running:
            current_time = datetime.now()
            
            # Check if it's market close time (4:00 PM ET / 9:00 PM UTC)
            if current_time.hour == 21 and current_time.minute == 0:
                # Check if we haven't sent today's summary yet
                today = current_time.date()
                last_summary_date = getattr(self, '_last_summary_date', None)
                
                if last_summary_date != today:
                    self._send_scheduled_end_of_day_summary()
                    self._last_summary_date = today
            
            time.sleep(60)  # Check every minute
    
    def _send_scheduled_end_of_day_summary(self):
        """Send the scheduled end-of-day summary"""
        try:
            log.info("Generating scheduled end-of-day summary")
            
            # Create performance summary from today's trades
            summary = self._create_daily_performance_summary()
            
            # Send the summary
            asyncio.run(self.send_end_of_day_summary(summary))
            
            log.info("Scheduled end-of-day summary sent successfully")
            
        except Exception as e:
            log.error(f"Failed to send scheduled end-of-day summary: {e}")
    
    def _create_daily_performance_summary(self) -> PerformanceSummary:
        """Create a performance summary from today's trades"""
        today = datetime.now().date()
        
        # Filter trades from today
        today_trades = [trade for trade in self.trade_history 
                       if trade.get('date', datetime.now()).date() == today]
        
        if not today_trades:
            # Return empty summary if no trades today
            return PerformanceSummary(
                date=datetime.now(),
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                daily_return=0.0,
                active_positions=0,
                signals_generated=0,
                signals_accepted=0,
                acceptance_rate=0.0,
                total_pnl_dollars=0.0
            )
        
        # Calculate metrics
        total_trades = len(today_trades)
        winning_trades = len([t for t in today_trades if t.get('pnl', 0) > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        total_pnl = sum(t.get('pnl', 0) for t in today_trades)
        total_pnl_dollars = sum(t.get('pnl_dollars', 0) for t in today_trades)
        
        # Get top and worst performers
        sorted_trades = sorted(today_trades, key=lambda x: x.get('pnl', 0), reverse=True)
        top_performers = sorted_trades[:3] if sorted_trades else []
        worst_performers = sorted_trades[-2:] if len(sorted_trades) >= 2 else []
        
        # Calculate consecutive wins
        consecutive_wins = 0
        for trade in reversed(sorted_trades):
            if trade.get('pnl', 0) > 0:
                consecutive_wins += 1
            else:
                break
        
        return PerformanceSummary(
            date=datetime.now(),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            daily_return=total_pnl,  # Same as total_pnl for daily
            active_positions=len([t for t in today_trades if t.get('status') == 'open']),
            signals_generated=len(self.alert_history),  # Approximate
            signals_accepted=total_trades,
            acceptance_rate=total_trades / len(self.alert_history) if self.alert_history else 0.0,
            max_drawdown=self._calculate_max_drawdown(today_trades),
            capital_used_pct=self._calculate_capital_used_pct(),
            consecutive_wins=consecutive_wins,
            avg_risk_per_trade=4.2,  # Default value
            total_pnl_dollars=total_pnl_dollars,
            top_performers=top_performers,
            worst_performers=worst_performers
        )
    
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Calculate maximum drawdown from trades"""
        if not trades:
            return 0.0
        
        peak = 0.0
        max_dd = 0.0
        running_pnl = 0.0
        
        for trade in trades:
            running_pnl += trade.get('pnl', 0)
            if running_pnl > peak:
                peak = running_pnl
            dd = peak - running_pnl
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_capital_used_pct(self) -> float:
        """Calculate percentage of capital used"""
        # This would need to be calculated based on account balance and position sizes
        # For now, return a default value
        return 82.0
    
    def add_trade_to_history(self, trade_data: Dict[str, Any]):
        """Add a trade to the daily history for end-of-day summary"""
        trade_data['date'] = datetime.now()
        self.trade_history.append(trade_data)
        
        # Keep only last 30 days of trades
        cutoff_date = datetime.now() - timedelta(days=30)
        self.trade_history = [t for t in self.trade_history 
                            if t.get('date', datetime.now()) > cutoff_date]
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _check_alert_throttling(self, alert: Alert) -> bool:
        """Check if alert should be throttled"""
        current_time = time.time()
        alert_key = f"{alert.alert_type.value}_{alert.level.value}"
        
        # Check cooldown
        if current_time - self.last_alert_time.get(alert_key, 0) < self.alert_cooldown_seconds:
            return False
        
        # Check rate limiting
        minute_key = f"{alert_key}_{current_time // 60}"
        if self.alert_counts[minute_key] >= self.max_alerts_per_minute:
            return False
        
        self.last_alert_time[alert_key] = current_time
        self.alert_counts[minute_key] += 1
        
        return True
    
    def _track_alert(self, alert: Alert):
        """Track alert for analytics"""
        self.alert_history.append(alert)
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        if not self.alert_history:
            return {}
        
        stats = {
            'total_alerts': len(self.alert_history),
            'alerts_by_type': defaultdict(int),
            'alerts_by_level': defaultdict(int),
            'recent_alerts': []
        }
        
        for alert in self.alert_history:
            stats['alerts_by_type'][alert.alert_type.value] += 1
            stats['alerts_by_level'][alert.level.value] += 1
        
        # Get recent alerts (last 10)
        stats['recent_alerts'] = [
            {
                'type': alert.alert_type.value,
                'level': alert.level.value,
                'title': alert.title,
                'timestamp': alert.timestamp.isoformat()
            }
            for alert in list(self.alert_history)[-10:]
        ]
        
        return stats
    
    # ============================================================================
    # OAUTH ALERT METHODS
    # ============================================================================
    
    async def send_oauth_morning_alert(self) -> bool:
        """Send daily OAuth token renewal reminder"""
        try:
            if not self.oauth_enabled:
                log.info("OAuth alerts disabled, skipping morning alert")
                return False
            
            from datetime import datetime
            from zoneinfo import ZoneInfo
            
            # Get current time in configured timezone
            tz = ZoneInfo(self.oauth_timezone)
            now = datetime.now(tz)
            today = now.date()
            
            # Check if it's a trading day (Monday-Friday)
            if today.weekday() >= 5:  # Saturday or Sunday
                log.info("Skipping OAuth morning alert - weekend")
                return False
            
            # Format the morning alert message
            message = f"""🌅 Good morning! It's {today:%A, %b %d}.

🔐 E*TRADE Token Renewal Required
⏰ Market opens in 1 hour

🔗 Production: {self.oauth_renewal_url}/oauth/start?env=prod
🔗 Sandbox: {self.oauth_renewal_url}/oauth/start?env=sandbox

📱 Tap, approve, paste PIN → Done"""
            
            # Send the alert
            success = await self.send_alert(
                AlertType.OAUTH_RENEWAL,
                AlertLevel.INFO,
                "Daily OAuth Token Renewal",
                message
            )
            
            if success:
                log.info("OAuth morning alert sent successfully")
            else:
                log.error("Failed to send OAuth morning alert")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth morning alert: {e}")
            return False
    
    async def send_oauth_renewal_success(self, environment: str) -> bool:
        """Send OAuth token renewal success notification"""
        try:
            message = f"""✅ OAuth Token Renewed Successfully

🔐 Environment: {environment.upper()}
⏰ Time: {datetime.now().strftime('%H:%M ET')}
🔄 Trading service updated
📊 Ready for market open

🎯 Next renewal: Tomorrow 8:30 AM ET"""
            
            success = await self.send_alert(
                AlertType.OAUTH_SUCCESS,
                AlertLevel.SUCCESS,
                "OAuth Token Renewed",
                message
            )
            
            if success:
                # Update OAuth status
                self.oauth_status[environment]['last_renewed'] = datetime.now()
                self.oauth_status[environment]['is_valid'] = True
                log.info(f"OAuth renewal success alert sent for {environment}")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth renewal success alert: {e}")
            return False
    
    async def send_oauth_renewal_error(self, environment: str, error_message: str) -> bool:
        """Send OAuth token renewal error notification"""
        try:
            message = f"""❌ OAuth Token Renewal Failed

🔐 Environment: {environment.upper()}
⏰ Time: {datetime.now().strftime('%H:%M ET')}
🚨 Error: {error_message}

🔧 Please check the OAuth web app and try again
🔗 URL: {self.oauth_renewal_url}/oauth/start?env={environment}"""
            
            success = await self.send_alert(
                AlertType.OAUTH_ERROR,
                AlertLevel.ERROR,
                "OAuth Token Renewal Failed",
                message
            )
            
            if success:
                # Update OAuth status
                self.oauth_status[environment]['is_valid'] = False
                log.info(f"OAuth renewal error alert sent for {environment}")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth renewal error alert: {e}")
            return False
    
    async def send_oauth_warning(self, environment: str, warning_message: str) -> bool:
        """Send OAuth token warning notification"""
        try:
            message = f"""⚠️ OAuth Token Warning

🔐 Environment: {environment.upper()}
⏰ Time: {datetime.now().strftime('%H:%M ET')}
⚠️ Warning: {warning_message}

🔧 Please check token status
🔗 URL: {self.oauth_renewal_url}/status?env={environment}"""
            
            success = await self.send_alert(
                AlertType.OAUTH_WARNING,
                AlertLevel.WARNING,
                "OAuth Token Warning",
                message
            )
            
            if success:
                log.info(f"OAuth warning alert sent for {environment}")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth warning alert: {e}")
            return False
    
    def update_oauth_status(self, environment: str, is_valid: bool, last_renewed: datetime = None):
        """Update OAuth token status"""
        try:
            self.oauth_status[environment]['is_valid'] = is_valid
            if last_renewed:
                self.oauth_status[environment]['last_renewed'] = last_renewed
            else:
                self.oauth_status[environment]['last_renewed'] = datetime.now()
            
            log.info(f"OAuth status updated for {environment}: valid={is_valid}")
            
        except Exception as e:
            log.error(f"Error updating OAuth status: {e}")
    
    def get_oauth_status(self, environment: str) -> Dict[str, Any]:
        """Get current OAuth status for environment"""
        return self.oauth_status.get(environment, {
            'last_renewed': None,
            'is_valid': False,
            'expires_at': None
        })
    
    async def check_oauth_token_health(self) -> Dict[str, bool]:
        """Check OAuth token health for all environments"""
        try:
            health_status = {}
            
            for env in ['prod', 'sandbox']:
                status = self.get_oauth_status(env)
                
                # Check if token is valid and recently renewed
                is_healthy = (
                    status['is_valid'] and 
                    status['last_renewed'] and 
                    (datetime.now() - status['last_renewed']).total_seconds() < 86400  # 24 hours
                )
                
                health_status[env] = is_healthy
                
                # Send warning if token is unhealthy
                if not is_healthy and status['last_renewed']:
                    await self.send_oauth_warning(
                        env, 
                        f"Token may be expired or invalid. Last renewed: {status['last_renewed']}"
                    )
            
            return health_status
            
        except Exception as e:
            log.error(f"Error checking OAuth token health: {e}")
            return {'prod': False, 'sandbox': False}
    
    async def schedule_oauth_morning_alert(self) -> bool:
        """Schedule OAuth morning alert (called by Cloud Scheduler)"""
        try:
            if not self.oauth_enabled:
                log.info("OAuth alerts disabled, skipping morning alert scheduling")
                return False
            
            # This method is called by Cloud Scheduler at 8:30 AM ET
            success = await self.send_oauth_morning_alert()
            
            if success:
                log.info("OAuth morning alert scheduled and sent")
            else:
                log.error("Failed to send scheduled OAuth morning alert")
            
            return success
            
        except Exception as e:
            log.error(f"Error in scheduled OAuth morning alert: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the alert manager"""
        log.info("Prime Alert Manager shutting down...")
        
        # Send shutdown notification
        await self.send_system_alert(
            "🔌 System Shutdown",
            "ETrade Strategy system is shutting down gracefully.",
            AlertLevel.INFO
        )

# Global instance
_prime_alert_manager = None

def get_prime_alert_manager() -> PrimeAlertManager:
    """Get the prime alert manager instance"""
    global _prime_alert_manager
    if _prime_alert_manager is None:
        _prime_alert_manager = PrimeAlertManager()
    return _prime_alert_manager

log.info("Prime Alert Manager loaded successfully")
